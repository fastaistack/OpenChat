from ...logger import Log
from pkg.database import models
from pkg.database.database import SessionLocal

log = Log()

from pkg.projectvar import *
gvar=Projectvar()
path=gvar.get_cache_path()

def get_system_default_path():
    try:
        with SessionLocal() as db:
            system_path_info = db.query(models.Setting).filter(models.Setting.config_key == 'system.default.path').first()
            if system_path_info is None:
                system_default_info = models.Setting(user_id="", config_key="system.default.path", config_value=path)
                db.add(system_default_info)
                old_system_default_info = models.Setting(user_id="", config_key="system.default.path.old", config_value=path)
                db.add(old_system_default_info)
                db.commit()
                system_path_info = db.query(models.Setting).filter(models.Setting.config_key == 'system.default.path').first()
            return system_path_info
    except Exception as ex:
        log.error(f"get_system_default_path error：{str(ex)}")
        raise Exception("获取系统默认路径失败，请重试")


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