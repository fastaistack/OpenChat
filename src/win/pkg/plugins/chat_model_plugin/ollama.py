from pkg.database.schemas import ChatMessageInfo
from ollama import Client
import ollama
from pkg.projectvar import Projectvar

gvar = Projectvar()
def get_default_settings() -> list:
    settings = list()
    setting = {"arg_name": "response_length", "arg_datatype": "number", "arg_precision": 0, "arg_value": 2048,
               "arg_max": 8000, "arg_min": 0, "arg_maxlen": 0}
    settings.append(setting)
    setting = {"arg_name": "top_p", "arg_datatype": "number", "arg_precision": 1, "arg_value": 0.8, "arg_max": 1,
               "arg_min": 0, "arg_maxlen": 0}
    settings.append(setting)
    setting = {"arg_name": "temperature", "arg_datatype": "number", "arg_precision": 1, "arg_value": 1, "arg_max": 1,
               "arg_min": 0, "arg_maxlen": 0}
    settings.append(setting)
    setting = {"arg_name": "top_k", "arg_datatype": "number", "arg_precision": 0, "arg_value": 5, "arg_max": 50,
               "arg_min": 0, "arg_maxlen": 0}
    settings.append(setting)
    setting = {"arg_name": "repeat_penalty", "arg_datatype": "number", "arg_precision": 2, "arg_value": 1, "arg_max": 3,
               "arg_min": 0.5, "arg_maxlen": 0}
    settings.append(setting)
    setting = {"arg_name": "multi_turn", "arg_datatype": "number", "arg_precision": 0, "arg_value": 0, "arg_max": 10,
               "arg_min": 0, "arg_maxlen": 0}
    settings.append(setting)

    return settings


def load_model(device='', url="", api_key="",precise_select="")->bool:
    print(url, api_key,precise_select)
    gvar.set_model_info({"url":url, "api_key":api_key,"model_selected":precise_select})
    return True
def call(reqeust:ChatMessageInfo, setting:dict, content_setting:dict):


    reasoning_content = ""  # 定义完整思考过程
    answer_content = ""     # 定义完整回复
    is_answering = False   # 判断是否结束思考过程并开始回复
    model_info= gvar.get_model_info()

    input_text = reqeust.message.strip()
    # 获取历史对话，根据设置获取指定数量的历史对话
    his_dialogs = reqeust.dialogs_history[:setting.get("multi_turn", 5)]  # 获取历史对话并按 multi_turn 限制

    # 创建聊天消息列表，包括历史对话和当前用户输入
    messages = [{"role": "system", "content": "你是一个非常有帮助的助手。"}]  # 初始化系统消息，定义对话背景

    # 将历史对话添加到 messages 列表中
    for QA in his_dialogs:
        if len(QA["question"]) and len(QA["answer"]):  # 确保问题和答案都有内容
            # 构建问题和答案的连接内容
            conversation = f"User: {QA['question']} Assistant: {QA['answer']}"
            messages.append({"role": "user", "content": conversation})

    plugin_prompt = content_setting.get("input_prompt", "")
    if plugin_prompt == "":   #若没有调用插件，用用户输入
        plugin_prompt = input_text

    # 加入当前用户输入的消息
    messages.append({"role": "user", "content": plugin_prompt})
    
    client = ollama.Client(host=model_info['url'])
    model = model_info['model_selected']
    stream = client.chat(
        model=model,  # 此处以 deepseek-v3 为例，可按需更换模型名称
        messages=messages,
        options = {
            "temperature": setting.get("temperature", 0.8),
            "num_ctx": setting.get("response_length", 2048),
            "top_p": setting.get("top_p", 0.8),
            "top_k": setting.get("top_k", 1),
            "repeat_penalty": setting.get("repeat_penalty", 1),
        },
        stream=setting.get("stream", True)
    )
    if 'deepseek-r1' in model:
        content_setting["output_think"] = ''
        content_setting["output_answer"]=''
        for chunk in stream:
            # 处理usage信息
            answer_content += chunk["message"]["content"]
            if '<think>' in answer_content:
                reasoning_content = answer_content.replace('<think>', '')
                if '</think>' in answer_content:
                    content_setting["output_answer"] = answer_content.split('</think>')[1]
                else :
                    content_setting["output_think"]  = reasoning_content
            
            yield content_setting

    else:
        try:
            output_all = ''
            for output in stream:
                output_all += output['message']['content']
                print(output_all)
                content_setting["output_think"] = ''
                content_setting["output_answer"] = output_all
                yield content_setting
        finally:
            content_setting["is_end_streamout"] = True