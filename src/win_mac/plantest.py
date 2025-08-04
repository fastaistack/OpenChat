from uuid import uuid4
from typing import List, Dict
from pkg.plugins.chat_model_plugin.default_openai import call, get_default_settings, load_model
from pkg.database.schemas import ChatMessageInfo
from pkg.plugins.web_argument_plugin.searxng_api_service import searXNGClient
import re
import json

def generate_report_plan_by_default_openai(topic: str, feedback: str = "") -> List[Dict]:
    """
    完整生成报告结构的流程：
    1. 使用大模型生成规划搜索用的查询语句
    2. 使用 searxng 搜索这些查询，获取 context
    3. 再用大模型结合 context 和要求生成结构大纲
    """

    #模型初始化
    api_key = "sk-399f10b5efb24c0ebe0bafc64c74793e"
    base_url = "https://api.deepseek.com/v1"
    model_name = "deepseek-chat"
    load_model(url=base_url, api_key=api_key, precise_select=model_name)

    setting = {s["arg_name"]: s["arg_value"] for s in get_default_settings()}
    setting["stream"] = True

    #生成搜索 query
    system_prompt_q = "你是一个专业的信息检索专家，擅长为报告结构规划提供高质量检索词。"

    user_prompt_q = f"""
你正在为一个中文技术研究报告规划结构，请根据主题与结构要求，生成 6 条高质量的 Web 检索语句。

<报告主题>
{topic}
</报告主题>

<报告结构组织要求>
- 包含引言、多个技术核心部分（如发展、对比、关键技术等）、结论总结
- 聚焦主题本身，避免冗余
- 避免重复内容

请返回如下格式：
{{
  "queries": [
    {{"query": "xxx"}},
    {{"query": "yyy"}}
  ]
}}
""".strip()

    req_q = ChatMessageInfo(session_id=f"query-{uuid4()}", message=topic, dialogs_history=[])
    content_setting_q = {
        "system_prompt": system_prompt_q,
        "input_prompt": user_prompt_q,
    }

    query_output = ""
    for chunk in call(req_q, setting, content_setting_q):
        query_output += chunk.get("output_answer", "")

    match = re.search(r'\{[\s\S]*\}', query_output)
    if match:
        try:
            queries_json = json.loads(match.group())
        except json.JSONDecodeError:
            print(" JSON 解析失败，输出内容如下：\n", match.group())
            queries_json = {"queries": []}
    else:
        print(" 未找到合法 JSON")
        queries_json = {"queries": []}

    query_list = [q.get("query") for q in queries_json.get("queries", []) if isinstance(q, dict)]

    print("查询词生成成功：", query_list)

    # 用 searxng 搜索这些 query，拼 context
    search_client = searXNGClient("https://searx.foobar.vip/")
    context_snippets = []

    for q in query_list:
        try:
            raw = search_client.searxng(q)
            parsed = search_client.extract_components(raw)
            snippets = parsed.get("snippets", [])[:2]
            context_snippets.extend(snippets)
        except Exception as e:
            print(f"搜索失败：{q}", e)

    context = "\n".join(context_snippets)
    print("搜索 context 获取完成")

    #用 context + 要求 生成结构
    system_prompt_s = "你是一个结构规划专家，擅长根据上下文和主题生成清晰的报告结构。"

    user_prompt_s = f"""
我希望你为我规划一份中文研究报告结构。

<报告主题>
{topic}
</报告主题>

<报告结构要求>
报告应包括以下部分：
- 引言
- 若干核心主题部分（可包含对比、原理、技术细节等）
- 结论总结

每一部分应包含：
- 名称
- 描述
- 是否需要检索：主干部分标注为“是”，引言/结论可为“否”
- 内容：留空

<反馈>
{feedback}
</反馈>

<已有背景资料>
{context}
</已有背景资料>

<格式>
【部分名称】
描述：xxx
是否需要检索：是/否
内容：

（请依次列出所有部分）
""".strip()

    req_s = ChatMessageInfo(session_id=f"plan-{uuid4()}", message=topic, dialogs_history=[])
    content_setting_s = {
        "system_prompt": system_prompt_s,
        "input_prompt": user_prompt_s,
    }

    structure_text = ""
    for chunk in call(req_s, setting, content_setting_s):
        structure_text += chunk.get("output_answer", "")

    print("报告结构生成完成")

    # 抽取结构字段
    sections = []
    seen_titles = set()

    # 拆分段落块（按“【xxx】”开始的段落分割）
    raw_sections = re.split(r"(?=【.*?】)", structure_text)
    for block in raw_sections:
        title_match = re.search(r"【(.*?)】", block)
        desc_match = re.search(r"描述[:：](.*)", block)
        need_search_match = re.search(r"是否需要检索[:：](.*)", block)

        if not title_match:
            continue

        title = title_match.group(1).strip()
        if title in seen_titles:
            continue
        seen_titles.add(title)

        desc = desc_match.group(1).strip() if desc_match else ""
        need_search = need_search_match.group(1).strip() if need_search_match else "否"

        sections.append({
            "title": title,
            "desc": desc,
            "need_search": need_search == "是",
            "context": ""
        })

    # 限制段落数量（可选）
    sections = sections[:10]

    # ========== Step 5：写入 Markdown 文件 ==========
    from datetime import datetime

    markdown_lines = [f"# 报告结构：{topic}", ""]

    for i, section in enumerate(sections, 1):
        title = section.get("title", f"Section {i}")
        desc = section.get("desc", "")
        need_research = section.get("need_search", False)
        markdown_lines.append(f"## {i}. {title}")
        markdown_lines.append("")
        markdown_lines.append(f"**是否需要网络检索**：{'是' if need_research else '否'}")
        markdown_lines.append("")
        markdown_lines.append(desc)
        markdown_lines.append("")

    # 写入 Markdown 文件
    filename = f"报告结构_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_lines))

    print(f"✅ 已生成 Markdown 文件：{filename}")




if __name__ == "__main__":
    topic = "写一篇关于三国演义中诸葛亮的报告 - 人物特点、生平事迹"  # 研究主题
    feedback = ""  # 如果有用户之前的反馈
    sections = generate_report_plan_by_default_openai(topic, feedback)
