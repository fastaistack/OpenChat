# -*- coding: utf-8  -*-
from pkg.plugins.web_argument_plugin.utils import citation_correction
from pkg.logger import Log
from pkg.database.schemas import ChatMessageInfo
log = Log()


def get_default_settings():
    settings = {
        "retrieve_topk": 3,
        "template": "说明：您是一位认真的研究者。使用提供的网络搜索结果，对给定的问题写一个全面而详细的回复。",
        "embedding_model_id": None,
        "embedding_model_path": "",
        "web_api_key": "",
        "style_search": "",
        "searxng_url":""
    }

    return settings


def call(reqeust:ChatMessageInfo, setting:dict, content_setting:dict):
    """
   web检索后处理插件，将模型答案加入引用标号
    Args:
        reqeust: ChatMessageInfo对象，从中获取待检测信息
        setting：输入超参数，包括检索相关超参数，包括 output_answer: llm生成初始答案, relevant_docs_list/serper_response: 检索前处理生成结果
    Returns:
        {"flag": False表示有检索异常情况，返回result异常信息至UI；True表示正常，继续代码
        "result"：返回UI提示，flag为False时输出报错信息
        "setting"：参数结构体，包括"content": 返回UI最终答案, "refs": 参考链接及摘要, "peopleAlsoAsk": 感兴趣话题
        }
    """
    input_query = reqeust.message
    output_answer = content_setting.get("output_answer", "")
    relevant_docs_list = content_setting.get("web_retrieve_args", {}).get("relevant_docs_list", [])
    web_response = content_setting.get("web_retrieve_args", {}).get("web_response", {})

    # 感兴趣相关话题
    peopleAlsoAsk = web_response.get("search_response",{}).get("peopleAlsoAsk", [])
    if peopleAlsoAsk == []:
        relatedSearches = web_response.get("search_response",{}).get("relatedSearches",[])
        for d in relatedSearches:
            if d.get("query"):
                peopleAlsoAsk.append({'question': d.get("query")})

    # 只选topN的相关参考文档，去重
    refs = []
    organic_results = web_response.get("search_response",{}).get("organic", [])
    log.info('\norganic_results: {}'.format(organic_results))
    for i in range(len(relevant_docs_list)):
        ref = {}
        try:
            ref['url'] = (relevant_docs_list[i].metadata)['url']
            ref['text'] = relevant_docs_list[i].page_content
        except:
            ref['url'] = relevant_docs_list[i].get("metadata",{}).get("url")
            ref['text'] = relevant_docs_list[i].get("page_content")

        try:
            ref['title'] = web_response.get("titles")[web_response['links'].index(ref['url'])]
            # 从 organic 结果中获取 site_name 和 icon_url
            for result in organic_results:
                if result.get('link') == ref['url']:
                    ref['site_name'] = result.get('site_name', '网页搜索')
                    ref['site_icon'] = result.get('icon_url', '')
                    break
        except:
            ref['title'] = ref.get("text", "").split('。')[0]
            ref['site_name'] = '网页搜索'
            ref['site_icon'] = ''
        if ref['url']==None or ref['text']==None or ref['title']=="":
            continue
        else:
            ref['text'] = ref['text'].replace(" ", "") #去除解析的常见特殊字符
            ref['title'] = ref['title'].replace(" ", "")

        if refs == []:
            refs.append(ref)
        else:
            if ref['url'] == refs[-1]['url'] and ref['text'] != refs[-1]['text']:
                refs[-1]['text'] += ref['text']
            elif ref['url'] != refs[-1]['url']:
                refs.append(ref)

    # 引用校正
    answer = citation_correction(output_answer, [ref.get("text", "") for ref in refs])
    out_dict = {"content": answer.strip(), "refs": refs, "recommend_question": peopleAlsoAsk}
    log.info('\nweb retriever postprocess output')
    content_setting["output_answer"] = answer

    return {"flag": True, "result": out_dict, "content_setting": content_setting}