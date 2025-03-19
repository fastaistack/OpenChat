import json
import threading
import uuid

from fastapi import APIRouter
from pkg.logger import Log
from sqlalchemy import and_
from pkg.database.database import SessionLocal
from pkg.database import models
from ...database import schemas
from ..process import process_model
from .plugin_process import SessionUpdateReq, query_session_plugin_by_id

router = APIRouter(
    prefix="/plugin-setting",
    tags=["plugin-setting"],
    responses={404: {"description": "Not found"}},
)

log = Log()


# 获取插件信息
def get_web_search_param(user_id: str, session_id, plugin_id: int):
    try:
        with SessionLocal() as db:
            param_list = db.query(models.UserPluginParam).filter(and_(models.UserPluginParam.user_id == user_id,
                                                                      models.UserPluginParam.session_id == session_id,
                                                                      models.UserPluginParam.param_key.like("web_search.%"))).all()
            if len(param_list) <= 0:
                insert_default(user_id, session_id, "web_search", plugin_id)
                param_list = db.query(models.UserPluginParam).filter(and_(models.UserPluginParam.user_id == user_id,
                                                                          models.UserPluginParam.session_id == session_id,
                                                                          models.UserPluginParam.param_key.like("web_search.%"))).all()
            return param_list
    except Exception as ex:
        log.error(f"process_plugin_param get_web_search_param error, {str(ex)}")
        raise Exception("获取参数信息失败，请检查并重试！")


def insert_default(user_id, session_id, param_type, plugin_id):
    try:
        if param_type == 'web_search':
            insert_default_web_search(user_id, session_id, plugin_id)
        elif param_type == "sensitive_info":
            insert_default_sensitive_info(user_id, session_id, plugin_id)
    except Exception as ex:
        log.error(f"process_plugin_param insert_default param_type:{param_type} error, {str(ex)}")
        raise Exception("插入默认值失败，请检查！")


def insert_default_web_search(user_id: str, session_id: str, plugin_id: int):
    with SessionLocal() as db:
        plugin_info = query_session_plugin_by_id(session_id, plugin_id)
        if plugin_info is None:
            raise Exception("插件信息获取失败，请检查并重试！")
        web_search_info = json.loads(plugin_info.plugin_param)
        web_api_key = models.UserPluginParam()
        web_api_key.id = str(uuid.uuid4()).replace("-", "")
        web_api_key.param_key = "web_search.web_api_key"
        web_api_key.user_id = user_id
        web_api_key.session_id = session_id
        web_api_key.param_value = web_search_info.get("web_api_key")
        db.add(web_api_key)
        embedding_model_path = models.UserPluginParam()
        embedding_model_path.id = str(uuid.uuid4()).replace("-", "")
        embedding_model_path.user_id = user_id
        embedding_model_path.param_key = "web_search.embedding_model_id"
        # embedding_model_list = process_model.get_download_embedding_model_list()
        # if len(embedding_model_list) > 0:
        if web_search_info.get("embedding_model_id") is not None:
            # embedding_model_path.param_value = embedding_model_list[0].id
            embedding_model_path.param_value = web_search_info.get("embedding_model_id")
        else:
            embedding_model_path.param_value = ''
        embedding_model_path.session_id = session_id
        db.add(embedding_model_path)
        retrieve_topk = models.UserPluginParam()
        retrieve_topk.id = str(uuid.uuid4()).replace("-", "")
        retrieve_topk.user_id = user_id
        retrieve_topk.param_key = "web_search.retrieve_topk"
        retrieve_topk.param_value = web_search_info.get("retrieve_topk")
        retrieve_topk.session_id = session_id
        db.add(retrieve_topk)
        template = models.UserPluginParam()
        template.id = str(uuid.uuid4()).replace("-", "")
        template.user_id = user_id
        template.param_key = "web_search.template"
        template.param_value = web_search_info.get("template")
        template.session_id = session_id
        db.add(template)
        style_search = models.UserPluginParam()
        style_search.id = str(uuid.uuid4()).replace("-", "")
        style_search.user_id = user_id
        style_search.param_key = "web_search.style_search"
        style_search.param_value = web_search_info.get("style_search")
        style_search.session_id = session_id
        db.add(style_search)
        db.commit()
        db.flush()


def insert_default_sensitive_info(user_id: str, session_id: str, plugin_id: int):
    plugin_info = query_session_plugin_by_id(session_id, plugin_id)
    if plugin_info is None:
        raise Exception("插件信息获取失败，请检查并重试！")
    sensitive_info_json = json.loads(plugin_info.plugin_param)

    style_filter_list_info = models.UserPluginParam()
    style_filter_list_info.id = str(uuid.uuid4()).replace("-", "")
    style_filter_list_info.user_id = user_id
    style_filter_list_info.session_id = session_id
    style_filter_list_info.param_key = "sensitive.style_filter_list"
    style_filter_list_info.param_value = json.dumps(sensitive_info_json.get("style_filter_list"))

    local_words_info_interval_tokens = models.UserPluginParam()
    local_words_info_interval_tokens.id = str(uuid.uuid4()).replace("-", "")
    local_words_info_interval_tokens.user_id = user_id
    local_words_info_interval_tokens.session_id = session_id
    local_words_info_interval_tokens.param_key = "sensitive.local_words.interval_tokens"
    local_words_info_interval_tokens.param_value = sensitive_info_json.get("local_words").get("interval_tokens")

    baidu_api_info_interval_tokens = models.UserPluginParam()
    baidu_api_info_interval_tokens.id = str(uuid.uuid4()).replace("-", "")
    baidu_api_info_interval_tokens.user_id = user_id
    baidu_api_info_interval_tokens.session_id = session_id
    baidu_api_info_interval_tokens.param_key = "sensitive.baidu_api.interval_tokens"
    baidu_api_info_interval_tokens.param_value = sensitive_info_json.get("baidu_api").get("interval_tokens")

    baidu_api_info_api_key = models.UserPluginParam()
    baidu_api_info_api_key.id = str(uuid.uuid4()).replace("-", "")
    baidu_api_info_api_key.user_id = user_id
    baidu_api_info_api_key.session_id = session_id
    baidu_api_info_api_key.param_key = "sensitive.baidu_api.api_key"
    baidu_api_info_api_key.param_value = sensitive_info_json.get("baidu_api").get("api_key")

    baidu_api_info_secret_key = models.UserPluginParam()
    baidu_api_info_secret_key.id = str(uuid.uuid4()).replace("-", "")
    baidu_api_info_secret_key.user_id = user_id
    baidu_api_info_secret_key.session_id = session_id
    baidu_api_info_secret_key.param_key = "sensitive.baidu_api.secret_key"
    baidu_api_info_secret_key.param_value = sensitive_info_json.get("baidu_api").get("secret_key")

    local_model_info_interval_tokens = models.UserPluginParam()
    local_model_info_interval_tokens.id = str(uuid.uuid4()).replace("-", "")
    local_model_info_interval_tokens.user_id = user_id
    local_model_info_interval_tokens.session_id = session_id
    local_model_info_interval_tokens.param_key = "sensitive.local_model.interval_tokens"
    local_model_info_interval_tokens.param_value = sensitive_info_json.get("local_model").get("interval_tokens")

    local_model_info_style_filter_model = models.UserPluginParam()
    local_model_info_style_filter_model.id = str(uuid.uuid4()).replace("-", "")
    local_model_info_style_filter_model.user_id = user_id
    local_model_info_style_filter_model.session_id = session_id
    local_model_info_style_filter_model.param_key = "sensitive.local_model.filter_model_list"
    local_model_info_style_filter_model.param_value = json.dumps(sensitive_info_json.get("local_model").get("filter_model_list"))

    local_model_info_model_id = models.UserPluginParam()
    local_model_info_model_id.id = str(uuid.uuid4()).replace("-", "")
    local_model_info_model_id.user_id = user_id
    local_model_info_model_id.session_id = session_id
    local_model_info_model_id.param_key = "sensitive.local_model.model_id"
    local_model_info_model_id.param_value = ''

    with SessionLocal() as db:
        db.add(style_filter_list_info)
        db.add(local_words_info_interval_tokens)
        db.add(baidu_api_info_interval_tokens)
        db.add(baidu_api_info_api_key)
        db.add(baidu_api_info_secret_key)
        db.add(local_model_info_interval_tokens)
        db.add(local_model_info_style_filter_model)
        db.add(local_model_info_model_id)
        db.commit()
        db.flush()


def get_sensitive_setting_list(user_id: str, session_id: str, plugin_id: int):
    try:
        with SessionLocal() as db:
            setting_list = db.query(models.UserPluginParam).filter(and_(models.UserPluginParam.user_id == user_id,
                                                                models.UserPluginParam.session_id == session_id,
                                                                models.UserPluginParam.param_key.like('sensitive.%')
                                                               )).all()
            if len(setting_list) <= 0:
                insert_default(user_id, session_id, "sensitive_info", plugin_id)
                setting_list = db.query(models.UserPluginParam).filter(and_(models.UserPluginParam.user_id == user_id,
                                                                models.UserPluginParam.session_id == session_id,
                                                                models.UserPluginParam.param_key.like('sensitive.%')
                                                               )).all()
        local_words = {}
        baidu_api_info = {}
        local_model_info = {}
        style_filter_list = []
        for item in setting_list:
            if item.param_key == "sensitive.style_filter_list":
                style_filter_list = json.loads(item.param_value)
            elif item.param_key == "sensitive.local_words.interval_tokens":
                local_words.update({"interval_tokens": int(item.param_value)})
            elif item.param_key == "sensitive.baidu_api.interval_tokens":
                baidu_api_info.update({"interval_tokens": int(item.param_value)})
            elif item.param_key == "sensitive.baidu_api.api_key":
                baidu_api_info.update({"api_key": item.param_value})
            elif item.param_key == "sensitive.baidu_api.secret_key":
                baidu_api_info.update({"secret_key": item.param_value})
            elif item.param_key == "sensitive.local_model.interval_tokens":
                local_model_info.update({"interval_tokens": int(item.param_value)})
            elif item.param_key == "sensitive.local_model.filter_model_list":
                if len(item.param_value) > 0:
                    local_model_info.update({"filter_model_list": json.loads(item.param_value)})
                else:
                    local_model_info.update({"style_filter_model": []})
            elif item.param_key == "sensitive.local_model.model_id":
                if len(item.param_value) > 0:
                    local_model_info.update({"model_id": int(item.param_value)})
                else:
                    local_model_info.update({"model_id": None})
        sensitive_info = schemas.SensitiveSettingInfo(style_filter_list=style_filter_list, local_words=local_words,
                                                      baidu_api=baidu_api_info,local_model=local_model_info)
        return sensitive_info
    except Exception as ex:
        log.error(f"in process_plugin_param get_sensitive_setting_list error,{str(ex)}")
        return []


def update_web_search(user_id: str, session_id, item: schemas.UserPluginWebSearchParamUpdateInfo):
    try:
        with SessionLocal() as db:
            param_list = db.query(models.UserPluginParam).filter(and_(models.UserPluginParam.user_id == user_id,
                models.UserPluginParam.session_id == session_id, models.UserPluginParam.param_key.like("web_search.%"))).all()
            if len(param_list) <= 0:
                return False
            for param_info in param_list:
                if param_info.param_key.split(".")[1] == "web_api_key" and param_info.param_value != item.web_api_key:
                    param_info.param_value = item.web_api_key
                elif param_info.param_key.split(".")[1] == "retrieve_topk" and int(param_info.param_value) != item.retrieve_topk:
                    param_info.param_value = item.retrieve_topk
                elif param_info.param_key.split(".")[1] == "embedding_model_id" and param_info.param_value != item.embedding_model_id:
                    param_info.param_value = item.embedding_model_id
                elif param_info.param_key.split(".")[1] == "template" and param_info.param_value != item.template:
                    param_info.param_value = item.template
                elif param_info.param_key.split(".")[1] == "style_search" and param_info.param_value != item.style_search:
                    param_info.param_value = item.style_search
            db.commit()
        plugin_param_json = get_web_search_plugin_param_json(item.retrieve_topk, item.template, item.style_search, item.embedding_model_id, item.web_api_key)
        from .plugin_process import update_session_tool
        session_updates = {"session_id": session_id, "plugin_id": item.plugin_id, "update_val": {"plugin_param": json.dumps(plugin_param_json)}}
        db_update = update_session_tool([SessionUpdateReq(**session_updates)])
        return True
    except Exception as ex:
        log.error(f"in process_plugin_param update_web_search error, {str(ex)}")
        return False


def get_web_search_plugin_param_json(retrieve_topk: int, template: str, style_search: str, embedding_model_id: int, web_api_key: str):
    embedding_model_path = ""
    # embedding_models = process_model.list([embedding_model_id])
    # if len(embedding_models) > 0:
    #     for model_item in embedding_models:
    #         if model_item.get("id") == embedding_model_id:
    #             embedding_model_path = model_item.get("local_path")
    #             break
    embedding_model_list= process_model.get_download_ollama_embedding_model_list()
    if len(embedding_model_list)>0:
        for embedding_model in embedding_model_list:
            if embedding_model.get('id') == embedding_model_id:
                embedding_model_path = embedding_model.get('local_path').split(":")[0]
    return {"retrieve_topk": retrieve_topk, "template": template, "web_api_key": web_api_key,
                                  "style_search": style_search, "embedding_model_path": embedding_model_path,
                                  }


def get_sensitive_plugin_param_json(update_info: schemas.SensitiveSettingPluginParamInfo):
    local_words_json = {"interval_tokens": update_info.local_words.get("interval_tokens")}
    baidu_api_json = {"interval_tokens": update_info.baidu_api.get("interval_tokens"), "api_key": update_info.baidu_api.get("api_key"),
                      "secret_key": update_info.baidu_api.get("secret_key")}
    local_model_json = {"interval_tokens": update_info.local_model.get("interval_tokens"),
                        "filter_model_list": update_info.local_model.get("filter_model_list"),
                        "model_id": update_info.local_model.get("model_id")
                        }
    return {"style_filter_list": update_info.style_filter_list, "local_words":local_words_json,
                                      "baidu_api": baidu_api_json, "local_model": local_model_json}


def update_sensitive_setting_info(user_id: str, session_id: str, update_info: schemas.SensitiveSettingUpdateInfo):
    try:
        with SessionLocal() as db:
            item_list = db.query(models.UserPluginParam).filter(and_(models.UserPluginParam.user_id == user_id,
                models.UserPluginParam.session_id == session_id, models.UserPluginParam.param_key.like("sensitive.%"))).all()
            for item in item_list:
                if item.param_key == "sensitive.local_words.interval_tokens":
                    item.param_value = str(update_info.local_words.interval_tokens)
                elif item.param_key == "sensitive.style_filter_list":
                    item.param_value = json.dumps(update_info.style_filter_list)
                    if "local_model" in update_info.style_filter_list:
                        load_model_filter_model_list = []
                        for filter_model_item in update_info.local_model.filter_model_list:
                            load_model_filter_model_list.append(filter_model_item.get("type"))
                        t = threading.Thread(target=load_local_sensitive_model, args=(update_info.local_model.model_id, load_model_filter_model_list))
                        t.start()
                elif item.param_key == "sensitive.baidu_api.interval_tokens":
                    item.param_value = update_info.baidu_api.interval_tokens
                elif item.param_key == "sensitive.baidu_api.api_key":
                    item.param_value = update_info.baidu_api.api_key
                elif item.param_key == "sensitive.baidu_api.secret_key":
                    item.param_value = update_info.baidu_api.secret_key
                elif item.param_key == "sensitive.local_model.interval_tokens":
                    item.param_value = update_info.local_model.interval_tokens
                elif item.param_key == "sensitive.local_model.filter_model_list":
                    if len(update_info.local_model.filter_model_list) > 0:
                        item.param_value = json.dumps(update_info.local_model.filter_model_list)
                elif item.param_key == "sensitive.local_model.model_id":
                    if update_info.local_model.model_id is not None:
                        item.param_value = str(update_info.local_model.model_id)
                    else:
                        item.param_value = ""
            db.commit()
            db.flush()
        local_words_json = {"interval_tokens": update_info.local_words.interval_tokens}
        baidu_api_json = {"interval_tokens": update_info.baidu_api.interval_tokens, "api_key": update_info.baidu_api.api_key,
                          "secret_key": update_info.baidu_api.secret_key}
        local_models_json = {"interval_tokens": update_info.local_model.interval_tokens, "filter_model_list": update_info.local_model.filter_model_list,
                             "model_id": update_info.local_model.model_id}
        plugin_param_info = schemas.SensitiveSettingPluginParamInfo(local_words=local_words_json, baidu_api=baidu_api_json, local_model=local_models_json, style_filter_list=update_info.style_filter_list)
        plugin_param_json = get_sensitive_plugin_param_json(plugin_param_info)
        from .plugin_process import update_session_tool
        session_updates = {"session_id": session_id, "plugin_id": update_info.plugin_id,
             "update_val": {"plugin_param": json.dumps(plugin_param_json)}}
        db_update = update_session_tool([SessionUpdateReq(**session_updates)])
        return True
    except Exception as ex:
        log.error(f"update_sensitive_setting_info error, user_id:{user_id}, session_id:{session_id}, error:{str(ex)}")
        return False


def load_local_sensitive_model(model_id: int, filter_model_list: []):
    try:
        embedding_model_list = process_model.list([model_id])
        embedding_model_info = embedding_model_list[0]
        from pkg.plugins.sensitive_filter_plugin.preprocess_sensitive_filter import load_model
        load_model('', embedding_model_info.get("local_path"), filter_model_list)
    except Exception as ex:
        log.error(f"load local sensitive model error, model_id:{model_id}, error:{str(ex)}")
        return False

