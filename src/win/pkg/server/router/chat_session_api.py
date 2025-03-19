
import json
from pathlib import Path
from typing import Union, List

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from ..process.biz_enum import ChatItemRole
from ...database import schemas
from ...logger import Log
from ...projectvar.statuscode import StatusCodeEnum
from ...projectvar import constants as const
from ...projectvar import Projectvar
from ...server import schemas as server_schema
from ..process import process_chat, process_model
import time
from ..depends import get_headers
from starlette.responses import FileResponse

gvar = Projectvar()

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},)

log = Log()


# 请求/响应结构体定义


# 会话结构体
class ChatSessionListResponse(server_schema.CommonResponse):
    resData: Union[List[schemas.ChatSessionInfo], None]


class ChatSessionResponse(server_schema.CommonResponse):
    resData: Union[schemas.ChatSessionInfo, None]


class ChatSessionUpdateRequestInfo(BaseModel):
    id: str
    session_name: str


class ChatItemListResponse(server_schema.CommonResponse):
    resData: Union[List[schemas.ChatItemInfo], None]


class ChatItemLikeRequestInfo(BaseModel):
    id: str
    like_type: int # 1-喜欢；2-不喜欢


class ChatItemStopInfo(BaseModel):
    request_id: str


@router.get("/session/list", response_model=ChatSessionListResponse)
async def get_session_list(headers=Depends(get_headers)):
    result = ChatSessionListResponse
    try:
        session_list = process_chat.get_session_list(headers[const.HTTP_HEADER_USER_ID])
        if len(session_list) <= 0:
            return result.success(None)
        result_list = []
        for session_item in session_list:
            item = schemas.ChatSessionInfo(id=session_item.id, session_name=session_item.session_name,
                user_id=session_item.user_id, create_time=int(time.mktime(session_item.create_time.timetuple()))*1000,
                update_time=int(time.mktime(session_item.create_time.timetuple()))*1000)
            result_list.append(item)
        return result.success(result_list)
    except Exception as ex:
        log.error(f"chat.get_session_list error,{str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.post("/session/create", response_model=ChatSessionResponse)
async def get_new_session_info(headers=Depends(get_headers)):
    result = ChatSessionResponse
    try:
        create_result = process_chat.create_session(headers[const.HTTP_HEADER_USER_ID])
        if create_result is None:
            return result.fail(StatusCodeEnum.YUAN_BIZ_DATA_CREATE_FAILED_ERROR.code, StatusCodeEnum.YUAN_BIZ_DATA_CREATE_FAILED_ERROR.errmsg)
        create_session = schemas.ChatSessionInfo(id=create_result.id, user_id=create_result.user_id, session_name=create_result.session_name,
            create_time=int(time.mktime(create_result.create_time.timetuple()))*1000, update_time=int(time.mktime(create_result.update_time.timetuple()))*1000)
        # 初始化用户默认插件
        process_chat.init_session_plugin(headers[const.HTTP_HEADER_USER_ID], create_result.id)
        return result.success(create_session)
    except Exception as ex:
        log.error(f"chat.get_new_session_info error,{str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.put("/session/update")
async def update_session_name(item: ChatSessionUpdateRequestInfo, headers=Depends(get_headers)):
    result = server_schema.CommonResponse
    try:
        session_info = process_chat.get_session_info(item.id, headers[const.HTTP_HEADER_USER_ID])
        if session_info is None:
            return result.fail(StatusCodeEnum.DB_NOTFOUND_ERR.code, StatusCodeEnum.DB_NOTFOUND_ERR.errmsg)
        return result.success({"result": process_chat.update_session_name(item.id, headers[const.HTTP_HEADER_USER_ID], item.session_name[:15])})
    except Exception as ex:
        log.error(f"update_session_name error, {str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.delete("/session/{session_id}")
async def delete_session(session_id, headers=Depends(get_headers)):
    result = server_schema.CommonResponse
    try:
        return result.success({"result": process_chat.delete_session(session_id)})
    except Exception as ex:
        log.error(f"delete_session error, {str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.get("/session/history", response_model=ChatItemListResponse)
async def get_session_history(session_id: str, headers=Depends(get_headers)):
    result = ChatItemListResponse
    try:
        model_list = process_model.get_download_model_list()
        model_map = {}
        for model_item in model_list:
            model_map[model_item.id] = model_item
        item_list = process_chat.get_session_item_list(session_id, headers[const.HTTP_HEADER_USER_ID])
        if len(item_list) <= 0:
            return result.success([])
        result_list = []
        for item in item_list:
            refs_json = []
            recommend_question_json = []
            if item.refs is not None and len(item.refs) > 0:
                refs_json = json.loads(item.refs)
            if item.recommend_question is not None and len(item.recommend_question) > 0:
                recommend_question_json = json.loads(item.recommend_question)
            model_pic = ""
            model_name = ""
            if model_map.get(item.model_id) is not None:
                model_info = model_map.get(item.model_id)
                model_pic = model_info.pic
                model_name = model_info.name
            ext_info_json = None
            if item.ext_info is not None and len(item.ext_info) > 0:
                ext_info_json = json.loads(item.ext_info)
            result_list.append(schemas.ChatItemInfo(id=item.id, session_id=item.session_id, text=item.text, response=item.response,
                refs=refs_json, recommend_question=recommend_question_json, question_id=item.question_id, role=item.role,
                like_type=item.like_type, create_time=int(time.mktime(item.create_time.timetuple()))*1000, think_text=item.think_text,
                model_id=item.model_id, model_pic=model_pic, model_name=model_name, reference_info=ext_info_json))
        return result.success(result_list)
    except Exception as ex:
        log.error(f"chat.get_session_list error, {str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.put("/item/like")
async def set_chat_record_like(item: ChatItemLikeRequestInfo, headers=Depends(get_headers)):
    result = server_schema.CommonResponse
    try:
        if item.like_type not in [0, 1, 2]:
            return result.fail(StatusCodeEnum.YUAN_MODEL_PARAM_INVALID_ERROR.code, StatusCodeEnum.YUAN_MODEL_PARAM_INVALID_ERROR.errmsg)
        chat_item = process_chat.get_chat_item(item.id, headers[const.HTTP_HEADER_USER_ID])
        if chat_item is None:
            return result.fail(StatusCodeEnum.DB_NOTFOUND_ERR.code, StatusCodeEnum.DB_NOTFOUND_ERR.errmsg)
        return result.success({"result": process_chat.chat_item_like(item.id, headers[const.HTTP_HEADER_USER_ID], item.like_type)})
    except Exception as ex:
        log.error(f"set_chat_record_like error, {str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.put("/infer/stop/{request_id}")
async def stop_infer(request_id: str):
    result = server_schema.CommonResponse
    try:
        gvar.set_stop_id(request_id)
        return result.success(True)
    except Exception as ex:
        log.error(f"stop_infer error, {str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.delete("/item/{request_id}")
async def delete_item(request_id: str, headers=Depends(get_headers)):
    result = server_schema.CommonResponse
    try:
        user_id = headers[const.HTTP_HEADER_USER_ID]
        item = process_chat.get_chat_item(request_id, user_id)
        if item is None:
            return result.fail(StatusCodeEnum.DB_NOTFOUND_ERR.code, StatusCodeEnum.DB_NOTFOUND_ERR.DB_NOTFOUND_ERR.errmsg)
        process_chat.delete_item(request_id)
        return result.success(True)
    except Exception as ex:
        log.error(f"delete_item error, {str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.delete("/question/{question_id}")
async def delete_item(question_id: str, headers=Depends(get_headers)):
    result = server_schema.CommonResponse
    try:
        user_id = headers[const.HTTP_HEADER_USER_ID]
        # item = process_chat.get_chat_item(request_id, user_id)
        # if item is None:
        #     return result.fail(StatusCodeEnum.DB_NOTFOUND_ERR.code, StatusCodeEnum.DB_NOTFOUND_ERR.DB_NOTFOUND_ERR.errmsg)
        process_chat.delete_by_question(question_id,user_id)
        return result.success(True)
    except Exception as ex:
        log.error(f"delete_item error, {str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.get("/session/download/{session_id}")
async def download_session_item_list(session_id: str, headers=Depends(get_headers)):
    result = server_schema.CommonResponse
    try:
        user_id = headers[const.HTTP_HEADER_USER_ID]
        now_str = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())

        session_info = process_chat.get_session_info(session_id, user_id)
        if session_info is None:
            return result.fail(StatusCodeEnum.DB_NOTFOUND_ERR.code, StatusCodeEnum.DB_NOTFOUND_ERR.errmsg)
        chat_session_item_list = process_chat.get_session_item_list(session_id, user_id)

        if len(chat_session_item_list) <= 0:
            file = ""
            file = file.join("### 会话名称：" + session_info.session_name + "\n")
            file = file.join("### 会话内容：\n")
            return FileResponse(file, filename=session_info.session_name + "_" + now_str + ".md")

        # 获取模型信息
        model_id_map = {}
        model_id_list = []
        for item in chat_session_item_list:
            model_id_list.append(item.model_id)
        model_id_list = set(model_id_list)
        model_list = process_model.list(list(model_id_list))
        for model_item in model_list:
            if model_id_map.get(model_item["id"]) is not None:
                continue
            model_id_map[model_item["id"]] = model_item

        # 根据question_id分组对话内容
        chat_item = {}
        for item in chat_session_item_list:
            if item.role == ChatItemRole.USER.role:
                if chat_item.get(item.question_id) is None:
                    chat_item[item.question_id] = {}
                if chat_item.get(item.question_id).get("question") is None:
                    chat_item[item.question_id]["question"] = {}
                chat_item[item.question_id]["question"]["text"] = item.text
                if item.ext_info is not None and len(item.ext_info) > 0:
                    chat_item[item.question_id]["question"]["ext_info"] = json.loads(item.ext_info)
                chat_item[item.question_id]["question"]["create_time"] = item.create_time
            else:
                if chat_item.get(item.question_id) is None:
                    chat_item[item.question_id] = {}
                if chat_item.get(item.question_id).get("answer") is None:
                    chat_item[item.question_id]["answer"] = []
                model_name = ""
                if model_id_map.get(item.model_id) is not None:
                    model_name = model_id_map.get(item.model_id).get("name")
                chat_item[item.question_id].get("answer").append({"text": item.text, "create_time": item.create_time, "model_name": model_name})
        # 写入文件
        with open(session_info.session_name + "_" + now_str + ".md", 'w', encoding='utf-8') as file:
            file.write("### 会话名称：" + session_info.session_name + "\n\n")
            file.write("### 会话内容：\n\n")
            # 循环所有chat_item记录，对以question_id为分组的对话内容进行拼接
            for item in chat_session_item_list:
                if chat_item.get(item.question_id) is None:
                    continue
                file.write("---\n\n")
                if chat_item.get(item.question_id).get("question"):
                    file.write("#### 问：\n\n")
                    file.write(chat_item.get(item.question_id)["question"]["text"] + "\n\n")
                    file.write("<font size=2.5>时间：" + chat_item.get(item.question_id)["question"]["create_time"].strftime("%Y-%m-%d %H:%M:%S") + "</font>\n\n")
                    if chat_item.get(item.question_id)["question"].get("ext_info"):
                        ext_info_json = chat_item.get(item.question_id)["question"].get("ext_info")
                        if ext_info_json.get("file") is not None:
                            file_list = ext_info_json.get("file")
                            if len(file_list) > 1:
                                i = 1
                                for file_info in file_list:
                                    file.write("> 文件" + str(i) + "名称：" + file_info["file_name"] + "\n\n")
                                    i += 1
                            else:
                                file.write("> 文件名称：" + file_list[0]["file_name"] + "\n\n")
                        elif ext_info_json.get("knowledge_name") is not None:
                            file.write("> 知识库名称：" + ext_info_json.get("knowledge_name") + "\n\n")
                if chat_item.get(item.question_id).get("answer"):
                    if len(chat_item.get(item.question_id).get("answer")) > 1:
                        i = 1
                        for answer_item in chat_item.get(item.question_id).get("answer"):
                            file.write("#### 答：" + str(i) + "\n\n")
                            file.write(answer_item.get("text") + "\n\n")
                            file.write("<font size=2.5>时间：" + answer_item.get("create_time").strftime("%Y-%m-%d %H:%M:%S") + "</font>\n\n")
                            file.write("> 模型名称：" + answer_item.get("model_name") + "\n\n")
                            i += 1
                    else:
                        file.write("#### 答：" + "\n\n")
                        file.write(chat_item.get(item.question_id).get("answer")[0].get("text") + "\n\n")
                        file.write("<font size=2.5>时间：" + chat_item.get(item.question_id).get("answer")[0].get("create_time").strftime("%Y-%m-%d %H:%M:%S") + "</font>\n\n")
                        file.write("> 模型名称：" + chat_item.get(item.question_id).get("answer")[0].get("model_name") + "\n\n")
                chat_item.pop(item.question_id)
        file_path = Path(file.name)
        response = FileResponse(file_path, media_type="text/markdown", filename=f'{session_info.session_name}_{now_str}.md')
        # file_path.unlink()
        return response
        # return result.success(True)
    except Exception as ex:
        log.error(f"download_session_item_list error, {str(ex)}")
        return result.fail(StatusCodeEnum.ERROR.code, str(ex))