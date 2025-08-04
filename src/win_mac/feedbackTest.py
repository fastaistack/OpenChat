import json
from typing import List
from uuid import uuid4
from pkg.plugins.chat_model_plugin.default_openai import call, get_default_settings, load_model
from pkg.database.schemas import ChatMessageInfo
import re


def generate_feedback_by_default_openai(query: str) -> List[str]:
    """
    使用 default_openai 的 call 方法生成 3~5 个后续研究问题。
    - 模型参数写死；
    - 自动收集 yield 输出内容；
    - 使用正则提取最后一个 JSON 解析；
    - 返回 questions 列表；
    """

    # 根据项目的实际配置替换
    api_key = "sk-399f10b5efb24c0ebe0bafc64c74793e"
    base_url = "https://api.deepseek.com/v1"
    model_name = "deepseek-chat"

    # 2. 模型初始化
    load_model(url=base_url, api_key=api_key, precise_select=model_name)

    #  3. 构造请求
    req = ChatMessageInfo(
        session_id=f"feedback-{uuid4()}",
        message=query,
        dialogs_history=[]
    )

    # 4. 构造参数
    setting = {s["arg_name"]: s["arg_value"] for s in get_default_settings()}
    setting["stream"] = True

    system_prompt = """
你是一个研究引导助手，善于帮助用户澄清研究意图。请根据用户输入的研究主题，生成 3~5 个简洁明了的提问，用于与用户交互、明确研究目标、范围、数据类型或背景信息。

请务必生成格式如下的合法 JSON：
{
  "questions": [
    "您是否希望将幸福感的定义具体化，例如包括经济水平、环境质量等因素？",
    "您是否需要关注某一时间段的数据，还是希望获得长期趋势分析？",
    "……"
  ]
}

要求：
- 每个问题必须是以“您是否…”、“您希望…”、“您更关注…”等方式开头；
- 问题是用于与用户交互的，不要是开放性问答；
- 不要加额外解释或文本，只输出一个 JSON。
""".strip()

    user_prompt = f"研究主题是：{query}。请生成适合的后续研究问题。"

    content_setting = {
        "system_prompt": system_prompt,
        "input_prompt": user_prompt,
    }

    #  5. 收集所有输出内容
    output = ""
    for result in call(req, setting, content_setting):
        chunk = result.get("output_answer", "")
        if chunk:
            output += chunk

    # === 6. 提取最后一个合法 JSON 块 ===
    matches = re.findall(r'\{[\s\S]*?\}', output)
    if not matches:
        print(" 未找到合法 JSON")
        return []

    last_json = matches[-1]

    # === 7. 尝试解析 ===
    last_json_cleaned = extract_last_json_block(last_json)
    print(" 最后一个 JSON 块如下:\n", last_json_cleaned)


def extract_last_json_block(text: str) -> str:
    """从文本中提取最后一个完整的 JSON 块（匹配最外层大括号）"""
    stack = []
    end = text.rfind("}")
    if end == -1:
        return ''
    for i in range(end, -1, -1):
        if text[i] == "}":
            stack.append("}")
        elif text[i] == "{":
            stack.pop()
            if not stack:
                return text[i:end+1]
    return ''


qs = generate_feedback_by_default_openai("写一篇关于三国演义中诸葛亮的报告 - 人物特点、生平事迹")
