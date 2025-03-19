import json

from sqlalchemy import and_

from .biz_enum import ChatItemStatus, ChatItemRole
from ...logger import Log
from ...database import models
from pkg.database.database import SessionLocal
import uuid
import time
import datetime
from ...database import schemas
from pkg.server.process import process_model, plugin_process
import importlib
from ...projectvar.statuscode import StatusCodeEnum


log = Log()


# 获取会话列表
def get_session_list(user_id: str):
    try:
        with SessionLocal() as db:
            session_list = db.query(models.ChatSession).filter(models.ChatSession.user_id == user_id)\
                .order_by(models.ChatSession.create_time.desc()).all()
        return session_list
    except Exception as ex:
        log.error(f"process_chat.get_session_list error,{str(ex)}")
        return []


# 创建会话并返回信息
def create_session(user_id: str):
    try:
        with SessionLocal() as db:
            session_id = str(uuid.uuid4()).replace("-", "")
            # time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            datetime_info = datetime.datetime.now()
            session = models.ChatSession(id=session_id, user_id=user_id, session_name="新建会话", create_time=datetime_info, update_time=datetime_info)
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
    except Exception as ex:
        log.error(f"process_chat.create_session error, {str(ex)}")
        return None


# 获取会话信息
def get_session_info(session_id: str, user_id: str):
    try:
        with SessionLocal() as db:
            session_info = db.query(models.ChatSession).filter(and_(models.ChatSession.id == session_id, models.ChatSession.user_id == user_id)).first()
        return session_info
    except Exception as ex:
        log.error(f"process_chat.get_session_info error,{str(ex)}")
        return None


# 更新会话信息
def update_session_name(session_id: str, user_id: str, session_name: str):
    try:
        with SessionLocal() as db:
            session_info = db.query(models.ChatSession).filter(and_(models.ChatSession.id == session_id, models.ChatSession.user_id==user_id)).first()
            session_info.session_name = session_name
            session_info.update_time = datetime.datetime.now()
            db.commit()
        return True
    except Exception as ex:
        log.error(f"process_chat.update_session_name error,{str(ex)}")
        return False


def update_session_time(user_id: str, session_id: str):
    try:
        with SessionLocal() as db:
            session_info = db.query(models.ChatSession).filter(and_(models.ChatSession.id == session_id, models.ChatSession.user_id==user_id)).first()
            if session_info is None:
                return
            session_info.update_time = datetime.datetime.now()
            db.commit()
        return True
    except Exception as ex:
        log.error(f"process_chat.update_session_name error,{str(ex)}")
        return False


# 删除会话
def delete_session(session_id: str):
    try:
        # delete user_plugin
        plugin_process.delete_session_plugin(session_id=session_id)
        # delete knowledge
        from pkg.server.router import knowledge
        knowledge.clean_konwledge_by_session(session_id)
        with SessionLocal() as db:
            db.query(models.ChatSession).filter(models.ChatSession.id == session_id).delete()
            db.query(models.ChatItem).filter(models.ChatItem.session_id == session_id).delete()
            db.commit()
        return True
    except Exception as ex:
        log.error(f"process_chat.delete_session error, {str(ex)}")
        return False


# 根据session_id获取历史会话信息
def get_session_item_list(user_id: str, session_id: str):
    try:
        with SessionLocal() as db:
            item_list = db.query(models.ChatItem).filter(and_(models.ChatItem.user_id == user_id, models.ChatItem.session_id == session_id)).all()
        return item_list
    except Exception as ex:
        log.error(f"process_chat.delete_session error, {str(ex)}")
        return []


# 获取某条聊天记录
def get_chat_item(item_id: str, user_id: str):
    try:
        with SessionLocal() as db:
            return db.query(models.ChatItem).filter(and_(models.ChatItem.id == item_id, models.ChatItem.user_id == user_id)).first()
    except Exception as ex:
        log.error(f"process_chat.get_chat_item error, {str(ex)}")
        return None


# 设置喜欢不喜欢
def chat_item_like(item_id: str, user_id: str, like_type: int):
    try:
        with SessionLocal() as db:
            item = db.query(models.ChatItem).filter(
                and_(models.ChatItem.id == item_id, models.ChatItem.user_id == user_id)).first()
            item.like_type = like_type
            db.commit()
        return True
    except Exception as ex:
        log.error(f"process_chat.chat_item_like error,{str(ex)}")
        return False


def insert_message(user_id: str, message: str, session_id: str, role_str: str, model_id: int, status: int, question_id: str, ext_info: str):
    try:
        with SessionLocal() as db:
            session_list = db.query(models.ChatSession).filter(models.ChatSession.id==session_id).all()
            if len(session_list) <= 0:
                raise Exception("无相应会话信息，请检查")
    except Exception as ex:
        log.error(f"process_chat.insert_message.get_session_info error, {str(ex)}")
        raise ex
    try:
        with SessionLocal() as db:
            # insert info into db
            request_id = str(uuid.uuid4()).replace("-", "")
            # time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            datetime_info = datetime.datetime.now()
            chat_item = models.ChatItem(id=request_id, user_id=user_id, session_id=session_id, question_id=question_id,
                                        text=message, like_type=0, status=status, ext_info=ext_info, think_text="",
                                        role=role_str, model_id=model_id, create_time=datetime_info, update_time=datetime_info)
            db.add(chat_item)
            db.commit()
            db.refresh(chat_item)
            return request_id
    except Exception as ex:
        log.error(f"process_chat.insert_message error,{str(ex)}")
        raise ex

def chat_model_infer(item: schemas.ChatMessageInfo, setting: {}, content_setting: {}):
    try:
        # get current model info
        count_num = 0
        think_start = 0
        think_cost = 0
        model_list = process_model.get_loaded_model_info()
        if len(model_list) <= 0:
            item_result = {"result_flag": False, "result_content": StatusCodeEnum.YUAN_MODEL_NOT_EXIST_ERROR.errmsg, "tokens": round(0.00, 2)}
            yield item_result
        else:
            model_info = model_list[0]
            loaded_model = importlib.import_module(model_info.plugin)
            infer_result = loaded_model.call(item, setting, content_setting)
            time_start = 0
            for item_infer_result in infer_result:
                if time_start == 0:
                    tokens = 0
                    time_start = time.time()
                else:
                    time_now = time.time()
                    count_num += 1
                    tokens = count_num / (time_now - time_start)

                if len(item_infer_result.get("output_think",""))>0 and think_start == 0:
                    think_start = time.time()
                if len(item_infer_result.get("output_think", ""))> 0 and len(item_infer_result["output_answer"])<= 0:
                    think_cost = time.time()-think_start
                item_result = {"result_flag": True, "result_content": item_infer_result["output_answer"], "result_think": item_infer_result["output_think"], "content_setting": item_infer_result, "tokens": round(tokens, 2),"think_cost":round(think_cost,2)}
                yield item_result

    except Exception as ex:
        log.error(f"process_chat.chat_infer error,{str(ex)}")
        raise ex


def chat_update(request_id: str, think_content: str, response: str, refs: str, recommend_question: str, status: int):
    try:
        with SessionLocal() as db:
            # get info
            chat_item_list = db.query(models.ChatItem).filter(models.ChatItem.id == request_id).all()
            if len(chat_item_list) <= 0:
                raise Exception(StatusCodeEnum.DB_NOTFOUND_ERR.errmsg)
            chat_item = chat_item_list[0]
            # update db
            chat_item.recommend_question = recommend_question
            chat_item.refs = refs
            chat_item.think_text = think_content
            chat_item.text = response
            chat_item.status = status
            # time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            chat_item.update_time = datetime.datetime.now()
            db.commit()
    except Exception as ex:
        log.error(f"process_chat.chat_update error,{str(ex)}")
        raise ex


def get_history_list(user_id: str, session_id: str, current_question_id: str, multi_num=5):
    try:
        with SessionLocal() as db:
            # 获取前multi_num+1个对话信息，然后再根据对话信息获取对话内容
            # 首先取24h内的对话信息
            start_time = (datetime.datetime.now()-datetime.timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            chat_question_item_list = db.query(models.ChatItem).filter(and_(models.ChatItem.user_id == user_id,
                models.ChatItem.session_id == session_id, models.ChatItem.status == ChatItemStatus.SUCCESS.status,
                models.ChatItem.create_time >= start_time, models.ChatItem.question_id != current_question_id))\
                .order_by(models.ChatItem.create_time.desc()).group_by(models.ChatItem.question_id).all()
            if len(chat_question_item_list) <= 0:
                return []
            chat_question_id_list = []
            for item in chat_question_item_list:
                chat_question_id_list.append(item.question_id)
            chat_history_list = db.query(models.ChatItem).order_by(models.ChatItem.create_time.desc()).\
                filter(models.ChatItem.question_id.in_(chat_question_id_list), models.ChatItem.status==ChatItemStatus.SUCCESS.status).all()

            chat_item = {}
            for item in chat_history_list:
                if item.role == ChatItemRole.USER.role:
                    if chat_item.get(item.question_id) is None:
                        chat_item[item.question_id] = {}
                    chat_item[item.question_id]["question"] = item.text
                else:
                    if chat_item.get(item.question_id) is None:
                        chat_item[item.question_id] = {}
                    if chat_item[item.question_id].get("answer") is not None:
                        continue
                    chat_item[item.question_id]["answer"] = item.text

            result = []
            for item in chat_history_list:
                if chat_item.get(item.question_id) and chat_item.get(item.question_id).get("question") and chat_item.get(item.question_id).get("answer"):
                    result.append({"question": chat_item.get(item.question_id)["question"], "answer": chat_item.get(item.question_id)["answer"]})
                    chat_item.pop(item.question_id)
                    if len(result) >= multi_num:
                        break
            return result
    except Exception as ex:
        log.error(f"process_chat.get_history_list error, {str(ex)}")
        return []


def get_chat_list_by_question_id(question_id: str):
    try:
        with SessionLocal() as db:
            return db.query(models.ChatItem).filter(models.ChatItem.question_id==question_id)\
                .order_by(models.ChatItem.create_time.asc()).all()
    except Exception as ex:
        log.error(f"process_chat.get_chat_list_by_question_id error, {str(ex)}")
        return []


def delete_item(request_id: str):
    try:
        with SessionLocal() as db:
            item = db.query(models.ChatItem).filter(models.ChatItem.id == request_id).first()
            db.query(models.ChatItem).filter(models.ChatItem.question_id == item.question_id).delete()
            db.commit()
            return True
    except Exception as ex:
        log.error(f"process_chat.delete_item {request_id} error, {str(ex)}")
        return False

def delete_by_question(question_id: str,user_id:str):
    try:
        with SessionLocal() as db:

            db.query(models.ChatItem).filter(models.ChatItem.question_id == question_id,models.ChatItem.user_id==user_id).delete()
            db.commit()
            return True
    except Exception as ex:
        log.error(f"process_chat.delete_item {question_id} error, {str(ex)}")
        return False



def get_session_item_list(session_id: str, user_id: str):
    try:
        chat_item_list = []
        with SessionLocal() as db:
            chat_item_list = db.query(models.ChatItem).filter(models.ChatItem.session_id==session_id, models.ChatItem.user_id==user_id)\
                .order_by(models.ChatItem.create_time.asc()).all()
        return chat_item_list
    except Exception as ex:
        log.error(f"process_chat.delete_item {session_id} error, {str(ex)}")
        return []


def init_session_plugin(user_id: str, session_id: str):
    try:
        from .plugin_process import set_default_plugins
        set_default_plugins(session_id, user_id)
    except Exception as ex:
        log.error(f"process_chat.init_session_plugin session_id:{session_id}, user_id: {user_id} error, {str(ex)}")
        return []