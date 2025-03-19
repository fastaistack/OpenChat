import json
import time
import uuid
from typing import Union, List
import traceback
from fastapi import FastAPI, Request, Depends
from sse_starlette import EventSourceResponse
from ...database import schemas
from ...logger import Log
from ...projectvar import constants as const
from ...projectvar import Projectvar
from ...projectvar.statuscode import StatusCodeEnum
from ...server import schemas as server_schema
from ..depends import get_headers
from ..process import process_chat, process_model
from ..process.plugin_process import pre_or_post_process
from ..process.biz_enum import ChatItemStatus, ChatItemRole

chatapi = FastAPI(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}}, )

log = Log()
gvar = Projectvar()


# 聊天内容结构体
class ChatMessageResponse(server_schema.CommonResponse):
    resData: Union[schemas.ChatMessageResponseInfo, None]


@chatapi.post('/sse/subscribe')
def chat_message(item: schemas.ChatMessageInfo, headers=Depends(get_headers)):
    def event_stream(item: schemas.ChatMessageInfo):
        request_id = ''
        question_id = str(uuid.uuid4())
        model_info = None
        try:
            user_id = headers[const.HTTP_HEADER_USER_ID]
            item.user_id = user_id
            ext_info = None
            if item.reference_info:
                ext_info = json.dumps(item.reference_info)
            process_chat.insert_message(user_id, item.message, item.session_id, ChatItemRole.USER.role,
                None, ChatItemStatus.SUCCESS.status, question_id, ext_info)
            process_chat.update_session_time(user_id, item.session_id)
            model_list = process_model.get_loaded_model_info()
            if len(model_list) <= 0:
                # yield json.dumps(get_result_dict(True, "", "", get_result_info(StatusCodeEnum.YUAN_MODEL_NOT_EXIST_ERROR.errmsg, "",
                #     [], [], int(time.time() * 1000), False, str(uuid.uuid4()), str(uuid.uuid4()), None, "", None, 0)))
                yield json.dumps(get_result_dict(True, "", "", get_result_info(StatusCodeEnum.YUAN_MODEL_NOT_EXIST_ERROR.errmsg, "",
                    [], [], int(time.time() * 1000), True, str(uuid.uuid4()), str(uuid.uuid4()), None, "", None, 0)))
                request_id = process_chat.insert_message(user_id, StatusCodeEnum.YUAN_MODEL_NOT_EXIST_ERROR.errmsg,
                    item.session_id, ChatItemRole.SYSTEM.role, None, ChatItemStatus.ERROR.status, question_id, None)
            else:
                model_info = model_list[0]
                dialog_history = process_chat.get_history_list(user_id, item.session_id, question_id, 5)
                item.dialogs_history = dialog_history
                request_id = process_chat.insert_message(user_id, "", item.session_id, ChatItemRole.SYSTEM.role,
                    model_info.id, ChatItemStatus.WAIT_TO_PROCESS.status, question_id, None)
                result_msg = run_chat_infer(item, headers, item.session_id, question_id, request_id, model_info.id, model_info.name, model_info.pic)
                for chat_item in result_msg:
                    yield chat_item
            gvar.delete_stop_id(request_id)
        except Exception as ex:
            log.error(f"chat event_stream error, {str(ex)}")
            log.error(f"{traceback.format_exc()}")
            model_id = None
            model_pic = None
            model_name = ""
            if model_info is not None:
                model_id = model_info.id
                model_pic = model_info.pic
                model_name = model_info.name
            if request_id != '':
                yield json.dumps(get_result_dict(True, "", "", get_result_info(str(ex), [], [], int(time.time() * 1000), "",
                    False, request_id, question_id, model_id, model_name, model_pic, 0)))
                yield json.dumps(get_result_dict(True, "", "", get_result_info(str(ex), [], [], int(time.time() * 1000), "",
                    True, request_id, question_id, model_id, model_name, model_pic, 0)))
                process_chat.chat_update(request_id, "",str(ex),  "", "", ChatItemStatus.ERROR.status)
            else:
                yield json.dumps(get_result_dict(True, "", "", get_result_info(str(ex), [], [], int(time.time() * 1000), "",
                    False, str(uuid.uuid4()), str(uuid.uuid4()), model_id, model_name, model_pic, 0)))
                yield json.dumps(get_result_dict(True, "", "", get_result_info(str(ex), [], [], int(time.time() * 1000), "",
                    True, str(uuid.uuid4()), str(uuid.uuid4()), model_id, model_name, model_pic, 0)))
    return EventSourceResponse(event_stream(item))


@chatapi.post('/sse/re-subscribe')
def chat_message(re_item: schemas.ReChatMessageInfo, headers=Depends(get_headers)):
    def event_stream(re_item: schemas.ReChatMessageInfo):
        request_id = ''
        model_info = None
        user_id = headers[const.HTTP_HEADER_USER_ID]
        try:
            chat_list = process_chat.get_chat_list_by_question_id(re_item.question_id)
            if len(chat_list) <= 0 or chat_list[0].role != ChatItemRole.USER.role:
                yield json.dumps(get_result_dict(False, "", "", get_result_info(StatusCodeEnum.DB_NOTFOUND_ERR.errmsg,  "",\
                    [], [], int(time.time() * 1000), False, str(uuid.uuid4()), re_item.question_id, None, "", None, 0)))
                yield json.dumps(get_result_dict(False, "", "", get_result_info(StatusCodeEnum.DB_NOTFOUND_ERR.errmsg, "",\
                    [], [], int(time.time() * 1000), True, str(uuid.uuid4()), re_item.question_id, None, "", None, 0)))
            else:
                chat_item = chat_list[0]
                reference_info = None
                if chat_item.ext_info is not None:
                    reference_info = json.loads(chat_item.ext_info)
                item = schemas.ChatMessageInfo(user_id=user_id, session_id=chat_item.session_id, message=chat_item.text,
                    dialogs_history=process_chat.get_history_list(user_id, chat_item.session_id, chat_item.question_id, 5),
                    reference_info=reference_info)
                model_list = process_model.get_loaded_model_info()
                process_chat.update_session_time(user_id, chat_item.session_id)
                if len(model_list) <= 0:
                    yield json.dumps(get_result_dict(True, "", "", get_result_info(StatusCodeEnum.YUAN_MODEL_NOT_EXIST_ERROR.errmsg, "",
                        [], [], int(time.time() * 1000), False, str(uuid.uuid4()), re_item.question_id, None, "", None, 0)))
                    yield json.dumps(get_result_dict(True, "", "", get_result_info(StatusCodeEnum.YUAN_MODEL_NOT_EXIST_ERROR.errmsg, "",
                        [], [], int(time.time() * 1000), True, str(uuid.uuid4()), re_item.question_id, None, "", None, 0)))
                    process_chat.insert_message(user_id, StatusCodeEnum.YUAN_MODEL_NOT_EXIST_ERROR.errmsg,
                        chat_item.session_id, ChatItemRole.SYSTEM.role, None, ChatItemStatus.ERROR.status, re_item.question_id, None)
                else:
                    model_info = model_list[0]
                    request_id = process_chat.insert_message(user_id, "", item.session_id, ChatItemRole.SYSTEM.role,
                        model_info.id, ChatItemStatus.WAIT_TO_PROCESS.status, re_item.question_id, None)
                    result_msg = run_chat_infer(item, headers, chat_item.session_id, re_item.question_id, request_id, model_info.id, model_info.name, model_info.pic)
                    for item in result_msg:
                        yield item
            gvar.delete_stop_id(request_id)
        except Exception as ex:
            log.error(f"re-chat event_stream error, {str(ex)}")
            model_id = None
            model_pic = None
            model_name = ""
            if model_info is not None:
                model_id = model_info.id
                model_pic = model_info.pic
                model_name = model_info.name
            if request_id != '':
                yield json.dumps(get_result_dict(True, "", "", get_result_info(str(ex), "", [], [], int(time.time() * 1000),
                    False, request_id, re_item.question_id, model_id, model_name, model_pic, 0)))
                yield json.dumps(get_result_dict(True, "", "", get_result_info(str(ex), "", [], [], int(time.time() * 1000),
                    True, request_id, re_item.question_id, model_id, model_name, model_pic, 0)))
                process_chat.chat_update(request_id, "",str(ex),  "", "", ChatItemStatus.ERROR.status)
            else:
                yield json.dumps(get_result_dict(True, "", "", get_result_info(str(ex), "", [], [], int(time.time() * 1000),
                    False, str(uuid.uuid4()), re_item.question_id, model_id, model_name, model_pic, 0)))
                yield json.dumps(get_result_dict(True, "", "", get_result_info(str(ex), "", [], [], int(time.time() * 1000),
                    True, str(uuid.uuid4()), re_item.question_id, model_id, model_name, model_pic, 0)))
    return EventSourceResponse(event_stream(re_item))


def get_result_dict(flag: bool, err_code: "", err_msg: "", res_data: dict):
    return {"flag": flag, "errCode": err_code, "errMessage": err_msg, "resData": res_data}


def get_result_info(message: str, think_content: str, refs: [], recommend_question: [], create_time: time,
                    finish_flag: bool, id: str, question_id: str, model_id: int, model_name: str, model_pic: str, tokens: float):
    return {"message": message, "think_text": think_content, "refs": refs, "recommend_question": recommend_question,
            "time": create_time, "finish_flag": finish_flag, "id": id, "question_id": question_id,
            "model_id": model_id, "model_pic": model_pic, "model_name": model_name, "tokens": tokens}


def run_chat_infer(item: schemas.ChatMessageInfo, headers, session_id: str, question_id: str, request_id: str, model_id, model_name, model_pic):
    run_pre_result = pre_or_post_process(session_id, "pre", item, {}, {})
    setting = {}
    content_setting = {}
    think_cost = 0.00
    if not run_pre_result["flag"]:
        yield json.dumps(get_result_dict(True, "", "", get_result_info(run_pre_result["result"]["content"], "",
            [], [], int(time.time() * 1000), False, request_id, question_id, model_id, model_name, model_pic, 0)))
        yield json.dumps(get_result_dict(True, "", "", get_result_info(run_pre_result["result"]["content"], "",
            [], [], int(time.time() * 1000), True, request_id, question_id, model_id, model_name, model_pic, 0)))
        process_chat.chat_update(request_id, "",run_pre_result["result"]["content"],  "", "", ChatItemStatus.ERROR.status)
    else:
        res_msg_dict = process_chat.chat_model_infer(item, run_pre_result["setting"], run_pre_result["content_setting"])
        continue_flag = True
        res_tmp = ""
        think_tmp = ""
        refs=[]
        for result_info in res_msg_dict:
            flag = result_info.get("result_flag")
            res_tmp = result_info.get("result_content")
            think_tmp = result_info.get("result_think")
            content_setting = result_info.get("content_setting")
            tokens = result_info.get("tokens")
            think_cost = 0.00 if result_info.get("think_cost", 0.00) is None else result_info.get("think_cost", 0.00)
            if not flag:
                yield json.dumps(get_result_dict(True, "", "", get_result_info(res_tmp, think_tmp, [], [], int(time.time() * 1000),
                    False, request_id, question_id, model_id, model_name, model_pic, tokens)))
                yield json.dumps(get_result_dict(True, "", "", get_result_info(res_tmp, think_tmp, [], [], int(time.time() * 1000),
                    True, request_id, question_id, model_id, model_name, model_pic, tokens)))
                process_chat.chat_update(request_id, "",res_tmp,  "", "", ChatItemStatus.ERROR.status)
                continue_flag = False
            else:
                run_post_result = pre_or_post_process(session_id, "post", item, setting, content_setting)
                res_tmp = run_post_result["result"].get("content")
                if not run_post_result["flag"]:
                    yield json.dumps(get_result_dict(True, "", "", get_result_info(res_tmp, think_tmp, [], [], int(time.time() * 1000),
                        False, request_id, question_id, model_id, model_name, model_pic, tokens)))
                    yield json.dumps(get_result_dict(True, "", "", get_result_info(res_tmp, think_tmp, [], [], int(time.time() * 1000),
                        True, request_id, question_id, model_id, model_name, model_pic, tokens)))
                    continue_flag = False
                    process_chat.chat_update(request_id, "",res_tmp,  "", "", ChatItemStatus.ERROR.status)
                    break
                else:
                    refs = []
                    if len(run_post_result["result"].get("refs")) > 0:
                        refs = list(run_post_result["result"].get("refs"))
                    recommend_question = []
                    if len(run_post_result["result"].get("recommend_question")) > 0:
                        recommend_question = list(run_post_result["result"].get("recommend_question"))
                    res_data = get_result_info(res_tmp, think_tmp, refs, recommend_question, int(time.time() * 1000), False,
                                               request_id, question_id, model_id, model_name, model_pic, tokens)
                    process_chat.chat_update(request_id, think_tmp, res_tmp,  json.dumps(refs), json.dumps(recommend_question), ChatItemStatus.SUCCESS.status)
                    yield json.dumps(get_result_dict(True, "", "", res_data))
                    if request_id in gvar.get_stop_id():
                        res_data["finish_flag"] = True
                        yield json.dumps(get_result_dict(True, "", "", res_data))
                        continue_flag = False
        if continue_flag:
            res_data = get_result_info(res_tmp, think_tmp, refs, recommend_question, int(time.time() * 1000), True, request_id,
                                       question_id, model_id, model_name, model_pic, tokens)
            yield json.dumps(get_result_dict(True, "", "", res_data))
            process_chat.chat_update(request_id, think_tmp,res_tmp,  json.dumps(refs), json.dumps(recommend_question), ChatItemStatus.SUCCESS.status)
