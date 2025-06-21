# -*- coding: utf-8  -*-
from pkg.database.schemas import ChatMessageInfo


def get_default_settings() -> list:
    settings = list()
    setting = {"arg_name": "multi_turn", "arg_datatype": "number", "arg_precision": 0, "arg_value": 0, "arg_max": 5,
               "arg_min": 0, "arg_maxlen": 0}
    settings.append(setting)

    setting = {"arg_name": "response_length", "arg_datatype": "number", "arg_precision": 0, "arg_value": 512,
               "arg_max": 8000, "arg_min": 0, "arg_maxlen": 0}
    settings.append(setting)

    return settings


def call(reqeust:ChatMessageInfo, setting:dict, content_setting=None):
    """
    前处理：对输入request进行合法性检验
    Args:
        reqeust: ChatMessageInfo对象，从中获取待检测信息
        setting：输入超参数
        content_setting：插件产生的中间变量，吐传即可
    Returns:
        {"flag": False表示有不合法情况，返回"result"至UI；True表示正常，继续代码
        "result"：返回UI提示，flag为False时输出报错信息
        "content_setting"：插件产生的中间变量，吐传即可
        }
    """
    if content_setting is None:
        content_setting = {}
    input_query = reqeust.message  # 待检测信息
    out_dict = {"content": input_query.strip(), "refs": [], "recommend_question": []}

    dialogs_history = reqeust.dialogs_history[:setting.get("multi_turn", 0)]
    his_length = 0
    for QA in dialogs_history:
        his_length += len(QA["question"]) + len(QA["answer"])

    if len(input_query) < 2:
        out_dict["content"] = "您输入的有效信息太少了，有什么需要帮忙吗？"
        return {"flag": False, "result": out_dict, "content_setting": content_setting}
    elif len(input_query) + his_length + setting.get("response_length", 512) > 8192:  #不同模型一致
        out_dict["content"] = "您输入的信息长度与期望响应长度之和大于8192，请重新输入"
        return {"flag": False, "result": out_dict, "content_setting": content_setting}
    else:
        #其它参数
        pass

    return {"flag": True, "result": out_dict, "setting":setting,"content_setting": content_setting}


# from fastapi import FastAPI
# import asyncio
# app = FastAPI()
# @app.post("/items1/")
# def create_item(item: ChatMessageInfo):
#     setting = {"do_sample": True, "top_p": 0.8, "temperature": 1, "top_k": 5,"repeat_penalty": 1.0, }
#     result = asyncio.run(call(item, setting))
#     return result
#
# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=2000)


