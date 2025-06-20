# -*- coding: utf-8  -*-

import re
from pkg.logger import Log
from pkg.database.schemas import ChatMessageInfo
log = Log()


def get_default_settings() -> list:
    settings = list()
    return settings


def call(reqeust:ChatMessageInfo, setting:dict, content_setting:dict):
    """
       后处理插件，清理特殊字符
    Args:
        reqeust: ChatMessageInfo对象，从中获取待检测信息
        setting：输入超参数，包括检索相关超参数，包括 output_answer: 上一个后处理插件处理后答案
    Returns:
        {"flag": False表示有检索异常情况，返回result异常信息至UI；True表示正常，继续代码
        "result"：返回UI提示，flag为False时输出报错信息，否则返回正确的结构体
        "setting"：参数结构体，包括"content": 返回UI最终答案, "refs": 参考链接及摘要, "peopleAlsoAsk": 感兴趣话题
        }
    """

    output_answer = content_setting.get("output_answer", "")
    text = output_answer.strip()  # 去除开头结尾\r, \t, \n, 空格等字符
    text = text.replace('<unk>', '').replace('<eod>', '').replace('▃', '\n').replace('▂', ' ').replace('<n>', '\n').replace('<sep>', '')

    text = re.sub(r'(\.{6,})', r'......', text)  # 省略号最多6个.
    text = re.sub(r'(。{2,})', r'。', text)  # 两个以上的连续句号只保留一个
    text = re.sub(r'(_{8,})', r'________', text)  # _最多8个.
    text = text.strip()
    log.info('\npostprocess clean special characters:{0}'.format(text))

    out_dict = {"content": text, "refs": [], "recommend_question": []}
    content_setting["output_answer"] = text
    return {"flag": True, "result": out_dict, "content_setting": content_setting}


from fastapi import FastAPI
import asyncio
app = FastAPI()
@app.post("/items1/")
def create_item(item: ChatMessageInfo):
    setting = {}
    content_setting = {"output_answer":"<sep>泰山位于山东省中部，隶属于泰安市，绵亘于泰安、济南、淄博三市之间。<eod>被誉为“五岳独尊”，是联合国教科文组织世界遗产。<n>1+1=2"}
    result = asyncio.run(call(item, setting, content_setting))
    return result

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=2000)
