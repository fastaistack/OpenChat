# -*- coding: utf-8  -*-

import re
from pkg.plugins.formula_utils import add_dollor_to_formula
from pkg.logger import Log
from pkg.database.schemas import ChatMessageInfo
log = Log()


def get_default_settings() -> list:
    settings = list()
    return settings


def call(reqeust:ChatMessageInfo, setting:dict, content_setting:dict):
    """
        后处理插件，公式渲染
    Args:
        reqeust: ChatMessageInfo对象，从中获取待检测信息
        setting：输入超参数，包括检索相关超参数，包括 output_answer: 上一个后处理插件处理后答案
    Returns:
        {"flag": False表示有检索异常情况，返回result异常信息至UI；True表示正常，继续代码
        "result"：返回UI提示，flag为False时输出报错信息，否则返回正确的结构体
        "setting"：参数结构体，包括"content": 返回UI最终答案, "refs": 参考链接及摘要, "peopleAlsoAsk": 感兴趣话题
        }
    """
    input_query = reqeust.message.strip()
    output_answer = content_setting.get("output_answer", "")

    # style: 0 代码类别
    check_str = input_query + output_answer
    check_str_fli = re.sub(r'(python|代码|```|"""|def |int |return |def\(|int\(|return\()', r'', check_str)

    if len(check_str) - len(check_str_fli) < 4:  # 若是公式意图（缺少代码标识符），在公式前后添加$符号
        output_answer = add_dollor_to_formula(output_answer)
    output_answer = output_answer.strip()
    log.info('\npostprocess formula rendering answer:{0}'.format(output_answer))

    out_dict = {"content": output_answer, "refs": [], "recommend_question": []}
    content_setting["output_answer"] = output_answer
    return {"flag": True, "result": out_dict, "content_setting": content_setting}


# from fastapi import FastAPI
# import asyncio
# app = FastAPI()
# @app.post("/items1/")
# def create_item(item: ChatMessageInfo):
#     setting = {}
#     content_setting = {
#         "output_answer":"泰山位于山东省中部，隶属于泰安市，绵亘于泰安、济南、淄博三市之间。被誉为“五岳独尊”，是联合国教科文组织世界遗产。1+1=2"
#     }
#     result = asyncio.run(call(item, setting, content_setting))
#     return result
#
#
# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=2000)


