# -*- coding: utf-8  -*-
import os
import re
from datetime import datetime
from pkg.plugins.web_argument_plugin.fetch_web_content import WebContentFetcher
from pkg.plugins.web_argument_plugin.retrieval import EmbeddingRetriever
from pkg.plugins.web_argument_plugin.llm_answer import LLMAnswer
from pkg.database.schemas import ChatMessageInfo
from pkg.logger import Log

log = Log()


def get_default_settings():
    settings = {
        "retrieve_topk": 3,
        "template": "说明：您是一位认真的研究者。使用提供的网络搜索结果，对给定的问题写一个全面而详细的回复。",
        "embedding_model_id": None,
        "embedding_model_path": "",
        "web_api_key": "",
        "style_search": ""
    }
    return settings


def call(reqeust:ChatMessageInfo, setting:dict, content_setting:dict):
    """
   启用web检索插件，调用此函数获取web检索内容
    Args:
        reqeust: ChatMessageInfo对象，从中获取待检测信息
        setting：输入超参数，包括检索相关超参数，包括"retrieve_topk", "template", "embedding_model_path", "serper_key", "style_search"
        "content_setting"：参数结构体，存贮中间变量，
    Returns:
        {"flag": False表示有检索异常情况，返回result异常信息至UI；True表示正常，继续代码
        "result"：返回UI提示，flag为False时输出报错信息
        "content_setting"：参数结构体，包括新生成中间变量，relevant_docs_list：相关参考文档列表, serper_response：检索API响应
        }
    """
    log.info('\npreprocess_web_argument plugin input setting paras: {}'.format(setting))

    t1 = datetime.now()
    input_query = reqeust.message.strip()
    out_dict = {"content": input_query, "refs": [], "recommend_question": []}

    paras_dict = setting
    # if type(paras_dict) != dict:
    #     out_dict["content"] = "您提供的web检索参数不合法，请重新输入"
    #     return {"flag": False, "result": out_dict, "setting": setting}
    style_search = paras_dict.get("style_search", "serper")  #网络检索类型设置

    # 基于问题提取网页内容
    web_api_key = paras_dict.get("web_api_key", "")

    if style_search=="serper" and re.fullmatch(r"[a-zA-Z0-9]{40,40}", web_api_key) is None:   #serper api key长度40，而且由字母和数字组成
        out_dict["content"] = "您提供的serper api key不合法，请重新输入"
        return {"flag": False, "result": out_dict, "content_setting": content_setting}
    elif style_search=="bing_api":
        # ToDo:完善bing api key 输入要求
        # out_dict["content"] = "您提供的bing api key不合法，请重新输入"
        # return {"flag": False, "result": out_dict, "setting": setting}
        pass

    embeddings_model_path = paras_dict.get("embedding_model_path")
    # if embeddings_model_path == None or not os.path.exists(embeddings_model_path):
    #     out_dict["content"] = "您提供的embeddings模型路径不合法，请重新输入"
    #     return {"flag": False, "result": out_dict, "content_setting": content_setting}

    try:
        web_contents_fetcher = WebContentFetcher(input_query, web_api_key)
        web_contents, web_response = web_contents_fetcher.fetch(style_search)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        log.info('\nweb fetch contents error: {}'.format(e))
        out_dict["content"] = "网络检索结果为空，请检查网络是否通畅或尝试其它关键字或切换其它网络检索方式"
        return {"flag": False, "result": out_dict, "content_setting": content_setting}

    if type(web_response) == str:
        out_dict["content"] = web_response
        return {"flag": False, "result": out_dict, "content_setting": content_setting}
    if web_contents == [] or web_response == {} or 'search_response' not in web_response:
        out_dict["content"] = "网络检索结果为空，请检查网络是否通畅或提供 api key是否合法或切换其它网络检索方式"
        return {"flag": False, "result": out_dict, "content_setting": content_setting}
    elif web_response.get('search_response').get('message') == 'Unauthorized.':
        out_dict["content"] = "您提供的serper api key未经授权，请检查重新输入"
        return {"flag": False, "result": out_dict, "content_setting": content_setting}
    else:
        # ToDo:完善bing api key 未经授权时，检索输出异常
        pass

    # 基于embeddings检索相关文档
    retriever = EmbeddingRetriever(paras_dict)
    relevant_docs_list = retriever.retrieve_embeddings_noreapt(web_contents, web_response['links'], input_query)

    content_processor = LLMAnswer(paras_dict)
    formatted_relevant_docs = content_processor._format_reference(relevant_docs_list, web_response['links'])
    if relevant_docs_list == [] or formatted_relevant_docs.strip() == "":
        out_dict["content"] = "网络检索结果为空，请检查相关参数是否设置正确"
        return {"flag": False, "result": out_dict, "content_setting": content_setting}

    t2 = datetime.now()
    content_setting["web_retrieve_args"] = {}
    content_setting["web_retrieve_args"]["formatted_relevant_docs"] = formatted_relevant_docs
    content_setting["web_retrieve_args"]["relevant_docs_list"] = relevant_docs_list
    content_setting["web_retrieve_args"]["web_response"] = web_response
    content_setting["input_prompt"] = "Web搜索结果：" + formatted_relevant_docs + \
                              paras_dict.get("template", "") + "\n问题：" + input_query.strip() + "\n答案："

    log.info('\nweb retriever use time:{0}, get relevant docs:{1}'.format(t2-t1, formatted_relevant_docs))
    return {"flag": True, "result": out_dict, "content_setting": content_setting}



# from fastapi import FastAPI
# import asyncio
# app = FastAPI()
# @app.post("/items1/")
# def create_item(item: ChatMessageInfo):
#     setting = {# 检索相关参数
#                    "retrieve_topk": 3, "template": "说明：您是一位认真的研究者。使用提供的网络搜索结果，对给定的问题写一个全面而详细的回复。",
#                    "embedding_model_path": r"D:\E\Code\NLP\yuan_checkpoints\text2vec-base-chinese",
#                    "web_api_key": "",
#                    "style_search": "serper"
#                }
#     result = asyncio.run(call(item, setting, {}))
#     return result
#
#
# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=2000)
