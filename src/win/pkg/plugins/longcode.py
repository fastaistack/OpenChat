# -*- coding: utf-8  -*-
from pkg.database.schemas import ChatMessageInfo
from pkg.projectvar import Projectvar
import threading
import os


def get_default_settings() -> list:
    settings = list()
    return settings


def call(reqeust:ChatMessageInfo, setting:dict):
    """
    拼接仓库文件与用户问题，作为模型输入。
    Args:
        reqeust: ChatMessageInfo对象，从中获取待检测信息
        setting：输入超参数
    Returns:
        {"flag": False表示有不合法情况，返回"result"至UI；True表示正常，继续代码
        "result"：返回UI提示，flag为False时输出报错信息
        "setting"：参数结构体
        }
    """
    input_query = reqeust.message.strip()
    user_id = reqeust.user_id

    out_dict = {"content": input_query.strip(), "refs": [], "recommend_question": []}

    meta_info = Projectvar()
    user_path = meta_info.get_cache_path()
    res_path = os.path.join(user_path, f'{user_id}_longcode.txt')
    res_path_exists = os.path.exists(res_path)
    if not res_path_exists:
        out_dict['content'] = '上传文件不存在。'
        return {'flag': False, 'result': out_dict, 'setting':setting}
    
    try:
        with open(res_path, 'r') as in_file:
            user_input = in_file.readlines()
        repo_text = '\n'.join(user_input).strip()
    except Exception as e:
        out_dict['content'] = '读入文件失败。'
        return {'flag': False, 'result': out_dict, 'setting':setting}
    
    if repo_text == '':
        out_dict['content'] = '上传文件为空。'
        return {'flag': False, 'result': out_dict, 'setting':setting}

    text = repo_text + "\nGenerate a code snippet according to the following requirements.\n" + input_query + '<sep>'
    text = text.replace('<n>', '\n')
    out_dict['content'] = text
    setting['input_prompt'] = text

    return {'flag': True, 'result': out_dict, 'setting':setting}



