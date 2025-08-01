from ...logger import Log
from pkg.database import models
from pkg.database.database import SessionLocal
from pkg.database import schemas
import json
import os
from pkg.projectvar import constants as const
from pkg.projectvar import Projectvar
gvar = Projectvar()
log = Log()

def get_system_default_path():
    try:
        with SessionLocal() as db:
            system_path_info = db.query(models.Setting).filter(models.Setting.config_key == 'system.default.path').first()
            if system_path_info is None:
                if const.SYSTEM == const.WINDOWS:
                    user_basepath = os.path.expanduser("~")
                    data_path = os.path.join(user_basepath, const.OPENCHAT_CACHEPATH)
                    system_default_info = models.Setting(user_id="", config_key="system.default.path", config_value = data_path)
                else:
                    path = os.path.join(os.path.expanduser('~'),'openchat')
                    system_default_info = models.Setting(user_id="", config_key="system.default.path", config_value=path)
                db.add(system_default_info)
                if const.SYSTEM == const.WINDOWS:
                    old_system_default_info = models.Setting(user_id="", config_key="system.default.path.old", config_value="")
                else:
                    path = gvar.get_cache_path()
                    old_system_default_info = models.Setting(user_id="", config_key="system.default.path.old", config_value=path)
                db.add(old_system_default_info)
                db.commit()
                system_path_info = db.query(models.Setting).filter(models.Setting.config_key == 'system.default.path').first()
            return system_path_info
    except Exception as ex:
        log.error(f"get_system_default_path error：{str(ex)}")
        raise Exception("获取系统默认路径失败，请重试")
    
def init_file_move():
    # v1.0.3版本增加文件迁移，默认在C盘
    with SessionLocal() as db:
        system_path_info = db.query(models.Setting).filter(models.Setting.config_key == 'system.default.path').first()
        if system_path_info.config_value == '':
            log.info("v1.0.3版本后执行且仅执行一次文件迁移")
            # 默认迁移到c盘
            old_path = system_path_info.config_value
            user_basepath = os.path.expanduser("~")
            from pkg.projectvar import constants as const
            os.path.join(user_basepath, const.OPENCHAT_CACHEPATH)
            new_path = os.path.join(user_basepath, const.OPENCHAT_CACHEPATH)
            update_system_default_path(new_path) # 同时更新current和new
            # 执行迁移
            from pkg.server.router import knowledge
            knowledge.mv_knowledge_file(old_path,new_path)
        else:
            return


def update_system_default_path(config_value: str):
    try:
        update_flag = False
        old_config_value = ""
        with SessionLocal() as db:
            system_path_info = db.query(models.Setting).filter(models.Setting.config_key == 'system.default.path').first()
            if system_path_info.config_value is None or system_path_info.config_value != config_value:
                update_flag = True
            old_config_value = system_path_info.config_value
            system_path_info.config_value = config_value
            db.commit()
        if update_flag:
            with SessionLocal() as db:
                old_system_path_info = db.query(models.Setting).filter(models.Setting.config_key == 'system.default.path.old').first()
                old_system_path_info.config_value = old_config_value
                db.commit()
        return True
    except Exception as ex:
        log.error(f"update_system_default_path error：{str(ex)}")
        raise Exception("设置系统默认路径失败，请重试")


def get_system_path_migrate_state():
    try:
        knowledge_info = {}
        status_map = {0: "NOT_MOVED", 1: "MOVING", 2: "SUCCESS", 3: "FAILED"}
        result_info = {}
        # 调用知识库接口获取状态
        from pkg.server.router import knowledge
        knowledge_move_process_result = knowledge.get_move_knowledge_process()
        knowledge_info.update({"status": status_map.get(knowledge_move_process_result.get("resData").get("status")),
                               "message": knowledge_move_process_result.get("resData").get("message"),
                               "total": knowledge_move_process_result.get("resData").get("total"),
                               "moved": knowledge_move_process_result.get("resData").get("moved"),
                })
        result_info.update({"knowledge": knowledge_info})

        # 调用模型获取状态
        model_info = {}
        from pkg.server.process import process_model
        model_move_result_flag, model_move_result = process_model.move_progress()
        if not model_move_result_flag:
            model_info.update({"status": "FAILED", "message": model_move_result.get("error_msg"),
                               "total": model_move_result.get("total"), "moved": model_move_result.get("moved")})
        else:
            model_info.update({"status": status_map.get(model_move_result.get("status")),
                               "message": model_move_result.get("error_msg"),
                               "total": model_move_result.get("total"),
                               "moved": model_move_result.get("moved")})
        result_info.update({"model": model_info})
        if model_info.get("status") == "FAILED" or knowledge_info.get("status") == "FAILED":
            result_info.update({"status": "FAILED"})
        if "FAILED" == result_info.get("status"):
            with SessionLocal() as db:
                old_system_path_info = db.query(models.Setting).filter(models.Setting.config_key == 'system.default.path.old').first()
                system_path_info = db.query(models.Setting).filter(models.Setting.config_key == 'system.default.path').first()
                system_path_info.config_value = old_system_path_info.config_value
                db.commit()
        return result_info
    except Exception as ex:
        log.error(f"get_system_path_migrate_state error：{str(ex)}")
        raise Exception("获取系统默认路径迁移状态失败，请重试")

# 首次初始化全局setting
def create_global_setting(setting:schemas.GlobalSetting):
    with SessionLocal() as db:
        try:
            db_query = db.query(models.Setting).filter(models.Setting.config_key == setting.config_key).first()
            if db_query:
                log.info(f"create_setting config_key: {setting.config_key} is already exist.")
                return None
            db_setting = models.Setting(**setting.dict())
            db.add(db_setting)
            db.commit()
            db.refresh(db_setting)
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            log.error(f"create_setting Exception:{str(e)}")
    return db_setting

# 根据key获取setting的config_key
def get_setting_config(config_key):
    with SessionLocal() as db:
        try:
            db_query  = db.query(models.Setting).filter(models.Setting.config_key==config_key).first()
            return db_query.config_value
        except Exception as e:
            log.error(e)
            return ''
        
def set_setting_config(config_key,config_value):
     with SessionLocal() as db:
        try:
            db_query  = db.query(models.Setting).filter(models.Setting.config_key==config_key).first()
            db_query.config_value = config_value
            db.add(db_query)
            db.commit()
            db.refresh(db_query)
            return True
        except Exception as e:
            log.error(e)
            return False

def global_setting_init():
    setting_list =[
        {'config_key':"model_selected",
         'config_value':json.dumps({"id":1,"model":"deepseek-r1"})},
        {'config_key':"sensitive",
         'config_value':json.dumps({"interval_tokens": 10,"api_key": "","secret_key": ""})},
        {'config_key':"web_search",
         'config_value':json.dumps([
            {
                "style_search": "serper",
                "web_api_key": "",
                "searxng_url":"",
                "embedding_model_id": 1,
                "retrieve_topk": 3,
                "template": "说明：您是一位认真的研究者。使用提供的网络搜索结果，对给定的问题写一个全面而详细的回复。",
                "enable":0
            },
            {
                "style_search": "bocha",
                "web_api_key": "",
                "searxng_url":"",
                "embedding_model_id": 1,
                "retrieve_topk": 3,
                "template": "说明：您是一位认真的研究者。使用提供的网络搜索结果，对给定的问题写一个全面而详细的回复。",
                "enable":0
            },
            {
                "style_search": "bing_bs4",
                "web_api_key": "",
                "searxng_url":"",
                "embedding_model_id": 1,
                "retrieve_topk": 3,
                "template": "说明：您是一位认真的研究者。使用提供的网络搜索结果，对给定的问题写一个全面而详细的回复。",
                "enable":0
            },
            {
                "style_search": "searxng",
                "web_api_key": "",
                "searxng_url":"https://searx.foobar.vip/",
                "embedding_model_id": 1,
                "retrieve_topk": 3,
                "template": "说明：您是一位认真的研究者。使用提供的网络搜索结果，对给定的问题写一个全面而详细的回复。",
                "enable":1
            }
        ])},
        {'config_key':"kbId",'config_value':""},
        {'config_key':"model_param",'config_value':'[{"arg_name": "response_length", "arg_datatype": "number", "arg_precision": 0, "arg_value": 2048, "arg_max": 8000, "arg_min": 0, "arg_maxlen": 0}, {"arg_name": "top_p", "arg_datatype": "number", "arg_precision": 1, "arg_value": 0.8, "arg_max": 1, "arg_min": 0, "arg_maxlen": 0}, {"arg_name": "temperature", "arg_datatype": "number", "arg_precision": 1, "arg_value": 1, "arg_max": 1, "arg_min": 0, "arg_maxlen": 0}, {"arg_name": "repeat_penalty", "arg_datatype": "number", "arg_precision": 2, "arg_value": 1, "arg_max": 3, "arg_min": 0.5, "arg_maxlen": 0}, {"arg_name": "multi_turn", "arg_datatype": "number", "arg_precision": 0, "arg_value": 0, "arg_max": 10, "arg_min": 0, "arg_maxlen": 0}]'}
    ]
    for setting in setting_list:
        try:
            setting_base = schemas.GlobalSetting(**setting)
            db_create_setting = create_global_setting(setting_base)
            if db_create_setting:
                log.info(f"setting {setting_base.config_key} create SUCCESSFUL")
        except Exception as e:
            import traceback
            print(traceback.format_exc())