# -*- coding: utf-8 -*-
from pkg.plugins.sensitive_filter_plugin.sensitive_baidu_filtering import fetch_token, text_request
# from pkg.plugins.sensitive_filter_plugin.sensitive_words_filtering import senstive_words
# from pkg.plugins.sensitive_filter_plugin.sensitive_models_filtering import load_roberta_model_single, evaluate_score
from pkg.logger import Log
from pkg.database.schemas import ChatMessageInfo
import time
import os

log = Log()
# out_count=0  #输出token数目
# Baidu api 账号的信息，并发50
API_KEY = ""
SECRET_KEY = ""
ACCESS_TOKEN = ""
TOKEN_START_TIME=int(time.time())

# 模型语义过滤
model_politic = any
model_porn = any
model_insult = any
model_violence = any


def get_default_settings():
    settings = {
        "style_filter_list": ["local_words"],
        "local_words": {"interval_tokens": 10},
        "baidu_api": {"interval_tokens": 20, "api_key": "", "secret_key": ""},
        "local_model": {
            "interval_tokens": 20,
            "filter_model_list": [
                # {"type":"politic", "threshold":0.8},
                # {"type":"porn", "threshold":0.8},
                # {"type":"insult", "threshold":0.8},
                # {"type":"violence", "threshold":0.8}
            ],
            "model_id": None
        }
    }
    return settings


# def load_model(device='', model_path='', filter_model_list=["politic", "porn", "insult", "violence"])->bool:
#     """
#     加载源hf模型，https://modelscope.cn/models/YuanLLM/Yuan2-2B-Janus-hf/files
#     Args:
#         device: 模型运行设备
#         model_path: 模型存放路径
#     Returns:
#         bool
#     """
#     global model_politic, model_porn, model_insult, model_violence

#     if not os.path.exists(model_path):
#         raise ValueError("安全审核模型路径不存在，请重新输入")

#     for name in filter_model_list:
#         if name == "politic" and 'bert' not in dir(model_politic):
#             model_politic = load_roberta_model_single(model_path, filter_model_name=name)
#         elif name == "porn" and 'bert' not in dir(model_porn):
#             model_porn = load_roberta_model_single(model_path, filter_model_name=name)
#         elif name == "insult" and 'bert' not in dir(model_insult):
#             model_insult = load_roberta_model_single(model_path, filter_model_name=name)
#         elif name == "violence" and 'bert' not in dir(model_violence):
#             model_violence = load_roberta_model_single(model_path, filter_model_name=name)

#     log.info("load model success")
#     return True


def call(reqeust:ChatMessageInfo, setting:dict, content_setting:dict):
    """
    文本审核接口，通过UI选择过滤方式
    Args:
        reqeust: ChatMessageInfo对象，从中获取待检测信息
    Returns:
        {"flag": False表示有敏感信息，中断后续代码，返回"result"至UI；True表示无敏感信息，继续代码
        "result"：返回UI提示
        "content_setting"：插件产生的中间变量，吐传即可
        }
    """
    log.info('\npreprocess_sensitive_filter plugin input setting paras: {}'.format(setting))

    info = reqeust.message  #前处理，待检测信息
    out_dict = {"content": info.strip(), "refs": [], "recommend_question": []}  # 不包含敏感信息

    sensitive_filter_args = setting
    style_filter_list = sensitive_filter_args.get("style_filter_list",[])

    if info.strip() == "" or sensitive_filter_args=={} or style_filter_list==[]: #若无有效内容，直接返回
        log.warning('\n待检测信息为空或未选择任何一种敏感信息过滤方式')
        return {"flag": True, "result": out_dict, "content_setting": content_setting}

    # 本地敏感词库过滤
    # if "local_words" in style_filter_list:
    #     flag, filter_res, contain_words = senstive_words(info)
    #     log.info('\nlocal sensitive words filtering result: {0}, sensitive words :{1}'.format(filter_res, str(contain_words)))
    #     if flag:
    #         out_dict["content"] = "对不起，您的输入包含敏感信息，请重新输入"
    #         return {"flag": False, "result": out_dict, "content_setting": content_setting}

    # baidu api 过滤
    if "baidu_api" in style_filter_list:
        baidu_api_args = sensitive_filter_args.get("baidu_api", {})
        global API_KEY, SECRET_KEY, ACCESS_TOKEN, TOKEN_START_TIME
        API_KEY_UI = baidu_api_args.get("api_key", "")
        SECRET_KEY_UI = baidu_api_args.get("secret_key", "")

        delta_tmie = int(time.time()) - TOKEN_START_TIME  #Access Token的有效期(秒为单位，有效期30天), 2592000
        if ACCESS_TOKEN=="" or API_KEY_UI!=API_KEY or SECRET_KEY_UI!=SECRET_KEY or delta_tmie>=2592000:
            flag, token_result = fetch_token(API_KEY_UI, SECRET_KEY_UI)
            if flag:
                ACCESS_TOKEN = token_result
                API_KEY = API_KEY_UI
                SECRET_KEY = SECRET_KEY_UI
                TOKEN_START_TIME = int(time.time())
            else:
                log.info('\nbaidu api filtering result: {0}'.format(token_result))
                out_dict["content"] = token_result
                return {"flag": False, "result": out_dict, "content_setting": content_setting}

        try:
            baidu_result = text_request(info, ACCESS_TOKEN)  # 百度api文本审核
            log.info('baidu sensitive filtering api result: {0}'.format(baidu_result))
            if baidu_result['conclusion'] != '合规':  # 包含敏感信息
                out_dict["content"] = "对不起，您的输入包含敏感信息，请重新输入"
                return {"flag": False, "result": out_dict, "content_setting": content_setting}
        except Exception as e:
            log.info('\nbaidu api error:{0}'.format(e))
            out_dict["content"] = "baidu api审核失败，请检查网络是否通畅或输入Key是否正确"
            return {"flag": False, "result": out_dict, "content_setting": content_setting}

    # 微调roberta模型进行语义过滤
    # if "local_model" in style_filter_list:
    #     local_model_args = sensitive_filter_args.get("local_model", {})
    #     filter_model_list = local_model_args.get("filter_model_list", [])

    #     for filter_model in filter_model_list:
    #         if filter_model.get("type") == "politic":
    #             politic_flg, politic_score = evaluate_score([info], model_politic, threshold=filter_model.get("threshold", 0.8))
    #             log.info('\nuse politic model filtering, score:{0}'.format(politic_score[0]))
    #             if politic_flg[0]:
    #                 out_dict["content"] = "对不起，您的输入包含敏感信息，请重新输入"
    #                 return {"flag": False, "result": out_dict, "content_setting": content_setting}
    #         elif filter_model.get("type") == "porn":
    #             porn_flg, porn_score = evaluate_score([info], model_porn, threshold=filter_model.get("threshold", 0.8))
    #             log.info('\nuse porn model filtering, score:{0}'.format(porn_score[0]))
    #             if porn_flg[0]:
    #                 out_dict["content"] = "对不起，您的输入包含敏感信息，请重新输入"
    #                 return {"flag": False, "result": out_dict, "content_setting": content_setting}
    #         elif filter_model.get("type") == "insult":
    #             insult_flg, insult_score = evaluate_score([info], model_insult, threshold=filter_model.get("threshold", 0.8))
    #             log.info('\nuse insult model filtering, score:{0}'.format(insult_score[0]))
    #             if insult_flg[0]:
    #                 out_dict["content"] = "对不起，您的输入包含敏感信息，请重新输入"
    #                 return {"flag": False, "result": out_dict, "content_setting": content_setting}
    #         elif filter_model.get("type") == "violence":
    #             violence_flg, violence_score = evaluate_score([info], model_violence, threshold=filter_model.get("threshold", 0.8))
    #             log.info('\nuse violence model filtering, score:{0}'.format(violence_score[0]))
    #             if violence_flg[0]:
    #                 out_dict["content"] = "对不起，您的输入包含敏感信息，请重新输入"
    #                 return {"flag": False, "result": out_dict, "content_setting": content_setting}

    return {"flag": True, "result": out_dict, "content_setting": content_setting}   #不包含敏感信息


# from fastapi import FastAPI
# import asyncio
# app = FastAPI()
# load_model(device='', model_path=r'D:\E\Code\NLP\yuan_checkpoints\SensitiveFiltermodels', filter_model_list=["politic", "porn", "insult", "violence"])
# @app.post("/items1/")
# def create_item(item: ChatMessageInfo):
#     setting = {
#                "style_filter_list": ["local_words", "local_model"],
#                "local_words": {"interval_tokens":10},
#                "baidu_api": {"interval_tokens":20, "api_key":"", "secret_key":""},
#                "local_model": {"interval_tokens":20, "filter_model_list":[{"type":"politic", "threshold":0.8}, {"type":"porn", "threshold":0.8},
#                                                                           {"type":"insult", "threshold":0.8}, {"type":"violence", "threshold":0.8}]}
#                }
#     t1 = time.time()
#     result = asyncio.run(call(item, setting, content_setting={}))
#     print('use time: ', time.time()-t1)
#     return result
#
#
# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=2000)
