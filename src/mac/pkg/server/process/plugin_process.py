from sqlalchemy.orm import Session
from ...database.database import SessionLocal, engine
from ...database import models,schemas
from ...database.models import SessionPlugins, PluginMo
from ...database.schemas import PluginBaseMo
from ...logger import Log
from typing import Union, List, Dict
from sqlalchemy import and_
import importlib
import json
from pydantic import BaseModel

log = Log()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 创建插件
def create_plugin(plugin: schemas.PluginBaseMo, user_id: str = None):
    with SessionLocal() as db:
        # 如果插件已经存在 禁止创建
        # db_query = query_plugin_by_key(plugin.plugin_key, user_id)
        db_query = query_plugin_by_key_and_type(plugin_key=plugin.plugin_key, plugin_type=plugin.plugin_type, user_id=user_id)
        if db_query:
            log.info(f"create_plugin plugin_name: {plugin.plugin_name_en} is already exist.")
            return None
        plugin.plugin_param = json.dumps(run_plugin_setting_script(plugin.plugin_path))
        try:
            # db_plugin = models.PluginMo(**plugin.dict(), plugin_name_en=plugin.plugin_name_en, plugin_name_cn=plugin.plugin_name_cn, 
            #                             description_en=plugin.description_en, description_cn=plugin.description_cn, user_id = user_id)
            db_plugin = models.PluginMo(**plugin.dict(), user_id = user_id)
            db.add(db_plugin)
            db.commit()
            db.refresh(db_plugin)
        except Exception as e:
            log.error(f"create_plugin Exception:{str(e)}")
            db.rollback()
            db_plugin = None
        finally:
            pass
        return db_plugin

# 根据插件名查询单个插件
def query_plugin_by_name(plugin_name_en: str, user_id: str = None):
    with SessionLocal() as db:
        try:
            plugin = db.query(PluginMo).filter_by(user_id=user_id, plugin_name_en=plugin_name_en).first()
        except Exception as e:
            log.error(f"query_plugin_by_name Exception:{str(e)}")
            db.rollback()
            plugin = None
        finally:
            pass
        return plugin

# 根据插件KEY查询单个插件
def query_plugin_by_key(plugin_key: str, user_id: str = None):
    with SessionLocal() as db:
        try:
            plugin = db.query(PluginMo).filter_by(user_id=user_id, plugin_key=plugin_key).first()
        except Exception as e:
            log.error(f"query_plugin_by_key Exception:{str(e)}")
            db.rollback()
            plugin = None
        finally:
            pass
        return plugin

# 根据插件KEY查询单个插件
def query_plugin_by_key_and_type(plugin_key: str, plugin_type: str, user_id: str = None):
    with SessionLocal() as db:
        try:
            plugin = db.query(PluginMo).filter_by(user_id=user_id, plugin_key=plugin_key, plugin_type=plugin_type).first()
        except Exception as e:
            log.error(f"query_plugin_by_key_and_type Exception:{str(e)}")
            db.rollback()
            plugin = None
        finally:
            pass
        return plugin

# 根据plugin_id查询单个插件
def query_plugin_by_id(plugin_id: int):
    with SessionLocal() as db:
        try:
            plugin = db.query(PluginMo).filter_by(plugin_id=plugin_id).first()
        except Exception as e:
            log.error(f"query_plugin_by_id Exception: {str(e)}")
            db.rollback()
            plugin = None
        finally:
            pass
        return plugin

# 查询所有user_id
def query_all_user_id():
    with SessionLocal() as db:
        try:
            all_users_id = db.query(PluginMo.user_id).distinct().all()
            # all_users = db.query(PluginMo.user_id).group_by(PluginMo.user_id).all()
            all_users = [user_id for (user_id,) in all_users_id]
        except Exception as e:
            log.error(f"query_plugin_by_id Exception: {str(e)}")
            db.rollback()
            all_users = None
        finally:
            pass
        return all_users

# 查询所有插件
def query_plugins(plugin_type: str = None, plugin_status: bool = None, search_type: str = None, user_id: str = None):
    with SessionLocal() as db:
        try:
            plugins = db.query(models.PluginMo).filter_by(user_id=user_id).all()
            if search_type == "all":
                plugins = db.query(models.PluginMo).filter_by(user_id=user_id).all()
            elif plugin_type != None and search_type == "one_type":
                plugins = db.query(models.PluginMo).filter_by(user_id=user_id, plugin_type=plugin_type).all()
            elif plugin_type != None and plugin_status != None and search_type == "one_type_status":
                plugins = db.query(models.PluginMo).filter_by(user_id=user_id, plugin_type=plugin_type,plugin_status=plugin_status).all()
            elif plugin_type != None and search_type == "one_type_nopost":
                db_querys = db.query(models.PluginMo).filter(and_(PluginMo.user_id==user_id, PluginMo.plugin_type==plugin_type)).order_by(PluginMo.plugin_order.desc()).all()
                plugin_map_list = ["postprocess_sensitive_filter", "postprocess_web_argument"]
                plugins = []
                for db_query in db_querys:
                    if db_query.plugin_key not in plugin_map_list:
                        plugins.append(db_query)
        except Exception as e:
            log.error(f"query_plugins Exception: {str(e)}")
            db.rollback()
            plugins = None
        finally:
            pass
        return plugins

# 根据plugin_id更新插件中指定字段
def update_plugin(plugin_id: int, update_val: dict, user_id: str = None):
    with SessionLocal() as db:
        try:
            plugin_to_update = db.query(models.PluginMo).filter_by(plugin_id=plugin_id, user_id=user_id).first()
            if plugin_to_update:
                for key, value in update_val.items():
                    if key == "plugin_status" and value == False:
                        db_delete = delete_session_plugin(session_plugin_id=plugin_id, user_id=user_id)
                    setattr(plugin_to_update, key, value)
                db.commit()
                db.refresh(plugin_to_update)
            else:
                plugin_to_update = None
        except Exception as e:
            log.error(f"update_plugin Exception:{str(e)}")
            db.rollback()
            plugin_to_update = None
        finally:
            pass
        return plugin_to_update

# 根据plugin_id删除指定插件
def delete_plugin(plugin_id: int, user_id: str = None):
    with SessionLocal() as db:
        try:
            plugin_to_delete = db.query(models.PluginMo).filter_by(plugin_id=plugin_id, user_id=user_id).first()
            session_plugins_to_delete = db.query(models.SessionPlugins).filter_by(plugin_id=plugin_id).all()
            if plugin_to_delete:
                db.delete(plugin_to_delete)
                if session_plugins_to_delete:
                    for session_plugin_to_delete in session_plugins_to_delete:
                        db.delete(session_plugin_to_delete)
                db.commit()
                # db.refresh(plugin_to_delete)
                plugin_to_delete = True
            else:
                plugin_to_delete = True
        except Exception as e:
            log.error(f"delete_plugin Exception: {str(e)}")
            db.rollback()
            plugin_to_delete = False
        finally:
            pass
        return plugin_to_delete



def create_new_plugin(plugin: schemas.PluginBaseMo):
    with SessionLocal() as db:
        try:
            all_user_id = query_all_user_id()
            
            insert_plugin_order = plugin.plugin_order
            if insert_plugin_order > 0:
                update_positive_order = db.query(PluginMo).filter(PluginMo.plugin_order >= insert_plugin_order).update({PluginMo.plugin_order: PluginMo.plugin_order + 1}, synchronize_session=False)
            elif insert_plugin_order < 0:
                update_negative_order = db.query(PluginMo).filter(PluginMo.plugin_order <= insert_plugin_order).update({PluginMo.plugin_order: PluginMo.plugin_order - 1}, synchronize_session=False)

            res = []
            final_res = []
            
            for user_id in all_user_id:
                db_query = query_plugin_by_key(plugin_key=plugin.plugin_key, user_id=user_id)
                # 如果插件已经存在 返回该插件
                if db_query:
                    log.info(f"creat_new_plugin plugin_name: {plugin.plugin_key} for user_id: {user_id} is already exist.")
                    final_res.append(db_query)
                    continue
        
                db_plugin = models.PluginMo(**plugin.dict(), user_id = user_id)
                db.add(db_plugin)
                res.append(db_plugin)
                final_res.append(db_plugin)
            db.commit()
            for plugin in res:
                db.refresh(plugin)
            
        except Exception as e:
            log.error(f"creat_new_plugin Exception:{str(e)}")
            db.rollback()
            final_res = None
        finally:
            pass
        return final_res
    

def get_and_update_plugin_param():
    with SessionLocal() as db:
        try:
            res = []
            all_user_id = query_all_user_id()
            for user_id in all_user_id:
                plugins = query_plugins(user_id=user_id, search_type="all")
                for plugin in plugins:
                    plugin.plugin_param = json.dumps(run_plugin_setting_script(plugin.plugin_path))
                    plugin_update = {"plugin_param": plugin.plugin_param}
                    update_plu = update_plugin(plugin_id=plugin.plugin_id, update_val=plugin_update, user_id=user_id)
                    res.append(update_plu)
        except Exception as e:
            log.error(f"get_and_update_plugin_param Exception:{str(e)}")
            db.rollback()
            res = None
        finally:
            pass
        return res





def run_plugin_setting_script(plugin_path):
    try:
        # log.info("plugin_path:{0}".format(plugin_path))
        load_model_result = importlib.import_module(plugin_path)
        # log.info("after exec plugin_path:{0}".format(plugin_path))
        # 执行脚本中的函数
        exec_result = load_model_result.get_default_settings()
        return exec_result
    except Exception as e:
        log.error(f"Error executing plugin '{plugin_path}': {str(e)}")
        return None

# 在session中添加插件
def create_session_plugin(session_plugins: List[schemas.SessionPluginBase]):
    
    db = SessionLocal()
    
    db_plugins = []
    for session_plugin in session_plugins:
        # 如果插件不存在 禁止创建
        db_query = query_plugin_by_id(plugin_id = session_plugin.plugin_id)
        if not db_query:
            log.error(f"create_session_plugin plugin_id:{session_plugin.plugin_id} is NOT exist")
            return None
        
        # 判断session中插件是否存在，存在返回，不存在创建
        db_session_plugin = db.query(models.SessionPlugins).filter_by(session_id=session_plugin.session_id, plugin_id=session_plugin.plugin_id).first()
        if db_session_plugin:
            log.info(f"create_session_plugin plugin_id:{session_plugin.plugin_id} is already exist")
            db_plugins.append(db_session_plugin)
        else:
            session_plugin.plugin_param = db_query.plugin_param
            
            try:
                db_plugin = models.SessionPlugins(**session_plugin.dict())
                db.add(db_plugin)
                db.commit()
                db.refresh(db_plugin)
                db_plugins.append(db_plugin)
            except Exception as e:
                log.error(f"create_session_plugin Exception:{str(e)}")
                db.rollback()
                db_plugin = None
                db_plugins.append(db_plugin)
            finally:
                pass
    return db_plugins
    


def query_session_plugin_by_id(session_id: str, plugin_id: int):
    with SessionLocal() as db:
        try:
            plugins = db.query(SessionPlugins).join(PluginMo, SessionPlugins.plugin_id == PluginMo.plugin_id).filter(and_(SessionPlugins.session_id==session_id, SessionPlugins.plugin_id==plugin_id)).first()
        except Exception as e:
            log.error(f"query_session_plugin_by_id Exception:{str(e)}")
            plugins = None
        finally:
            pass
        return plugins


# 在session中查询插件（session中所有插件、特定类型的插件（默认（default）、可选（normal））、已开启的插件）
def query_session_plugins(session_id: str, plugin_type: str = None, status: bool = None, search_type: str = None):
    
    if not session_id:
        raise ValueError("session_id must be provided and non-empty")
    
    with SessionLocal() as db:
        try:
            # 查询session中所有的插件
            if search_type == "all":
                plugins = db.query(SessionPlugins, PluginMo).join(PluginMo, SessionPlugins.plugin_id == PluginMo.plugin_id).filter(SessionPlugins.session_id==session_id).all()
            # 查询session中某种类型的所有插件
            elif plugin_type != None and search_type == "one_type":
                plugins = db.query(SessionPlugins, PluginMo).join(PluginMo, SessionPlugins.plugin_id == PluginMo.plugin_id).filter(and_(SessionPlugins.session_id==session_id, PluginMo.plugin_type==plugin_type)).all()
            # 查询session中状态为status的所有插件
            elif status != None and search_type == "one_status":
                plugins = db.query(SessionPlugins, PluginMo).join(PluginMo, SessionPlugins.plugin_id == PluginMo.plugin_id).filter(and_(SessionPlugins.session_id==session_id, SessionPlugins.session_status==status)).all()
            # 查询session中状态为status的某种类型的所有插件
            elif plugin_type != None and status != None and search_type == "one_type_status_in_session":
                plugins = db.query(SessionPlugins, PluginMo).join(PluginMo, SessionPlugins.plugin_id == PluginMo.plugin_id).filter(and_(SessionPlugins.session_id==session_id, SessionPlugins.session_status==status, PluginMo.plugin_type==plugin_type)).all()
            # 查询session中"已安装"的某种类型的插件
            elif plugin_type != None and status != None and search_type == "one_type_status":
                plugins = db.query(SessionPlugins, PluginMo).join(PluginMo, SessionPlugins.plugin_id == PluginMo.plugin_id).filter(and_(SessionPlugins.session_id==session_id, PluginMo.plugin_status==status, PluginMo.plugin_type==plugin_type)).all()
            # 查询session中"已安装"的某种类型不包含后处理的插件
            elif plugin_type != None and status != None and search_type == "one_type_status_nopost":
                db_querys = db.query(SessionPlugins, PluginMo).join(PluginMo, SessionPlugins.plugin_id == PluginMo.plugin_id).filter(and_(SessionPlugins.session_id==session_id, PluginMo.plugin_status==status, PluginMo.plugin_type==plugin_type)).all()
                plugin_map_list = ["postprocess_sensitive_filter", "postprocess_web_argument"]
                plugins = []
                for session_plugin, plugin_mo in db_querys:
                    if plugin_mo.plugin_key not in plugin_map_list:
                        plugins.append((session_plugin, plugin_mo))
                        
        except Exception as e:
            log.error(f"query_session_plugins Exception:{str(e)}")
            plugins = None
        finally:
            pass
        return plugins


class SessionUpdateReq(BaseModel):
    session_id: str
    plugin_id: int
    update_val: dict


def update_session_tool(session_updates):
    db = SessionLocal()
    result = []
    for session_update in session_updates:
        try:
            # 判断插件是否存在，存在更新值，不存在创建
            plugin_to_update = db.query(models.SessionPlugins).filter_by(session_id=session_update.session_id, plugin_id=session_update.plugin_id).first()
            if plugin_to_update:
                for key, value in session_update.update_val.items():
                    setattr(plugin_to_update, key, value)
                db.commit()
                db.refresh(plugin_to_update)
                result.append(plugin_to_update)
            else:
                try:
                    db_query = query_plugin_by_id(plugin_id=session_update.plugin_id)
                    session_create_dict = {"session_id": session_update.session_id, "plugin_id": session_update.plugin_id, "plugin_param": db_query.plugin_param, "session_status": session_update.update_val["session_status"]}
                    plugin_to_create = create_session_plugin([schemas.SessionPluginBase(**session_create_dict)])
                    result.extend(plugin_to_create)
                except Exception as e:
                    log.debug(f"rrr:{str(e)}")
        except Exception as e:
            log.error(f"Error.SQLAlchemy.update_plugin SQLAlchemyError:{str(e)}")
            db.rollback()
            plugin_to_update = None
            result.append(plugin_to_update)
        finally:
            pass
    return result


def update_seeeion_mid_tool(session_updates, user_id: str = None):
    # 默认开启后处理网络检索插件、后处理敏感词检测插件
    plugin_mapped = {"preprocess_web_argument": "postprocess_web_argument", "preprocess_sensitive_filter": "postprocess_sensitive_filter"}
    # 检查当前session_update.plugin_id是否在映射中
    for session_update in session_updates:
        db_query_plugin = query_plugin_by_id(plugin_id=session_update.plugin_id)
        if db_query_plugin.plugin_key in plugin_mapped:
            mapped_plugin_key = plugin_mapped.get(db_query_plugin.plugin_key)
            db_query_mapped_plugin = query_plugin_by_key(user_id=user_id, plugin_key=mapped_plugin_key)
            session_update_list = {"session_id": session_update.session_id, "plugin_id": db_query_mapped_plugin.plugin_id,"update_val": {"plugin_param": session_update.update_val["plugin_param"]}}
            plugin_to_default_post_update = update_session_tool([SessionUpdateReq(**session_update_list)])

    # 更新主要插件状态或参数
    result = update_session_tool(session_updates=session_updates)
    return result

# session_updates = List[session_id: str, plugin_id: int, update_val: dict]
# eg. [{"session_id": session_id, "plugin_id": plugin_id, "update_val": {"plugin_param": plugin_param}}]
# 更新session中指定插件中的指定字段
def update_session_plugin(session_updates, user_id: str = None):
    
    # 判断是否只有一个插件激活
    total_active_plugin = []
    # session_id_temp = None
    # for session_update in session_updates:
    #     session_id_temp = session_update.session_id
    # db_querys = query_session_plugins(session_id=session_id_temp, plugin_type="normal", status=True, search_type="one_type_status_in_session")
    # for db_session, db_plugin in db_querys:
    #     session_query_list = {"session_id": session_update.session_id, "plugin_id": db_session.plugin_id, "update_val": {"session_status": False}}
    #     plugin_to_query_update = update_session_tool([SessionUpdateReq(**session_query_list)])
    for session_update in session_updates:
        if session_update.update_val["session_status"] == True:
            total_active_plugin.append(session_update.plugin_id)
    if len(set(total_active_plugin)) > 1:
        log.error(f"Total Active Plugin OVER ONE. Please check.")
        raise Exception(f"Total Active Plugin OVER ONE. Please check.")
    
    # 默认开启后处理网络检索插件、后处理敏感词检测插件
    plugin_mapped = {"preprocess_web_argument": "postprocess_web_argument", "preprocess_sensitive_filter": "postprocess_sensitive_filter"}
    # 检查当前session_update.plugin_id是否在映射中
    for session_update in session_updates:
        db_query_plugin = query_plugin_by_id(plugin_id=session_update.plugin_id)
        if db_query_plugin.plugin_key in plugin_mapped:
            mapped_plugin_key = plugin_mapped.get(db_query_plugin.plugin_key)
            db_query_mapped_plugin = query_plugin_by_key(user_id=user_id, plugin_key=mapped_plugin_key)
            session_update_list = {"session_id": session_update.session_id, "plugin_id": db_query_mapped_plugin.plugin_id,"update_val": {"session_status": session_update.update_val["session_status"]}}
            plugin_to_default_post_update = update_session_tool([SessionUpdateReq(**session_update_list)])

    # 更新主要插件状态或参数
    result = update_session_tool(session_updates=session_updates)
    return result


# 删除session中指定插件
def delete_session_plugin(session_plugin_id: int = None, session_id: str = None, user_id: str =None):
    with SessionLocal() as db:
        try:
            if session_plugin_id == None and session_id != None and user_id == None:
                plugins_to_delete = db.query(models.SessionPlugins).filter_by(session_id=session_id).all()
                if plugins_to_delete:
                    for plugin_to_delete in plugins_to_delete:
                        db.delete(plugin_to_delete)
                        db.commit()
                        # db.refresh(plugin_to_delete)
                        plugin_to_delete = True
                else:
                    plugin_to_delete = True
            elif session_plugin_id != None and session_id == None and user_id != None:
                plugins_to_delete = db.query(SessionPlugins).join(PluginMo, SessionPlugins.plugin_id == PluginMo.plugin_id).filter(and_(SessionPlugins.plugin_id==session_plugin_id, PluginMo.user_id==user_id)).all()
                if plugins_to_delete:
                    for plugin_to_delete in plugins_to_delete:
                        plugin_mapped = {"preprocess_web_argument": "postprocess_web_argument", "preprocess_sensitive_filter": "postprocess_sensitive_filter"}
                        db_query_plugin = query_plugin_by_id(plugin_id=plugin_to_delete.plugin_id)
                        if db_query_plugin.plugin_key in plugin_mapped:
                            mapped_plugin_key = plugin_mapped.get(db_query_plugin.plugin_key)
                            post_session_plugin = db.query(SessionPlugins).join(PluginMo, SessionPlugins.plugin_id == PluginMo.plugin_id).filter(and_(PluginMo.plugin_key==mapped_plugin_key, PluginMo.plugin_type=="normal", PluginMo.user_id==user_id)).first()
                            db.delete(post_session_plugin)
                        db.delete(plugin_to_delete)
                        db.commit()
                        # db.refresh(plugin_to_delete)
                        plugin_to_delete = True
                else:
                    plugin_to_delete = True
        except Exception as e:
            log.error(f"delete_session_plugin Exception:{str(e)}")
            db.rollback()
            plugin_to_delete = False
        finally:
            pass
        return plugin_to_delete


# 查询结果已经包含默认插件
def query_session_plugins_pre_or_post(session_id: str, status: bool = True, exe_order: str = None):
    with SessionLocal() as db:
        try:
            plugins = db.query(SessionPlugins).join(PluginMo, SessionPlugins.plugin_id == PluginMo.plugin_id).filter(and_(SessionPlugins.session_id==session_id, PluginMo.plugin_order == 0, SessionPlugins.session_status == status)).all()
            if exe_order == "pre":
                plugins = db.query(SessionPlugins).join(PluginMo, SessionPlugins.plugin_id == PluginMo.plugin_id).filter(and_(SessionPlugins.session_id==session_id, PluginMo.plugin_order > 0, SessionPlugins.session_status == status)).order_by(PluginMo.plugin_order.desc()).all()
            elif exe_order == "post":
                plugins = db.query(SessionPlugins).join(PluginMo, SessionPlugins.plugin_id == PluginMo.plugin_id).filter(and_(SessionPlugins.session_id==session_id, PluginMo.plugin_order < 0, SessionPlugins.session_status == status)).order_by(PluginMo.plugin_order.desc()).all()
    
        except Exception as e:
            log.error(f"query_session_plugins Exception:{str(e)}")
            plugins = None
        finally:
            pass
        return plugins


# 查询session中已开启插件
def query_activeplugin_by_sessionid(session_id: str):
    
    pos_plugins = query_session_plugins_pre_or_post(session_id=session_id, status=True, exe_order="pre")
    neg_plugins = query_session_plugins_pre_or_post(session_id=session_id, status=True, exe_order="post")
    zero_plugins = query_session_plugins_pre_or_post(session_id=session_id, status=True, exe_order="zero")

    return {"pos_plugin":  [schemas.SessionPluginInDB.from_orm(pos_plugin) for pos_plugin in pos_plugins], 
            "neg_plugin":  [schemas.SessionPluginInDB.from_orm(neg_plugin) for neg_plugin in neg_plugins],
            "zero_plugin": [schemas.SessionPluginInDB.from_orm(zero_plugin) for zero_plugin in zero_plugins]}


# 创建会话时开启默认插件(删除使用delete_session_plugin（）)
def set_default_plugins(session_id: str, user_id: str):
    with SessionLocal() as db:
        try:
            res = []
            db_query_plugins = query_plugins(plugin_type="default", plugin_status=True, search_type="one_type", user_id=user_id)
            if db_query_plugins:
                for db_query_plugin in db_query_plugins:
                    db_query_session_plugin = query_session_plugin_by_id(session_id=session_id, plugin_id=db_query_plugin.plugin_id)
                    if db_query_session_plugin:
                        log.info(f"set_default_plugins: Default Session Plugin {db_query_plugin.plugin_name_en} has already exist.")
                        update_dict = {"session_id": session_id, "plugin_id": db_query_session_plugin.plugin_id, "update_val": {"plugin_param": db_query_session_plugin.plugin_param, "session_status": True}}
                        update_res = update_session_tool([SessionUpdateReq(**update_dict)])
                        res.append(update_res)
                    else:
                        log.info(f"set_default_plugins: Default Session Plugin {db_query_plugin.plugin_name_en} is creating...")
                        creat_dict = {"session_id": session_id, "plugin_id": db_query_plugin.plugin_id, "plugin_param": db_query_plugin.plugin_param, "session_status": True}
                        creat_res = create_session_plugin([schemas.SessionPluginBase(**creat_dict)])
                        log.info(f"set_default_plugins: Default Session Plugin {db_query_plugin.plugin_name_en} has created successful.")
                        res.append(creat_res)
                return res
            else:
                log.info(f"Can NOT Find Any Default Plugins.")
                return None
        except Exception as ex:
            log.error(f"set_default_plugins: Set Default plugin error: {str(ex)}")
            return None



async def set_model_setting(session_id: str, user_id: str, model_id: int):
    with SessionLocal() as db:
        # 查询模型列表中数据：
        model_search_results = db.query(models.Model).filter_by(id=model_id).first()
        # 组建路径和插件名
        plugin_path = model_search_results.plugin
        plugin_key = plugin_path.split('.')[-1]

        # 根据名称判断模型插件是否存在（默认：模型插件不改名）
        db_query_plugin = query_plugin_by_key_and_type(plugin_key=plugin_key, plugin_type="model", user_id=user_id)
        if not db_query_plugin:
            log.error(f"Model Plugin: {plugin_key} is NOT exist.")
            return None

        # 将“session”中模型插件中只保留一个模型是激活状态
        db_query_plugins = query_session_plugins(session_id=session_id, plugin_type="model", search_type="one_type")
        # for db_query_session_model_plugins, plugin_mo in db_query_plugins:
        if db_query_plugins:
            for db_query_session_model_plugin, plugin_mo in db_query_plugins:
                # for db_query_session_model_plugin in db_query_session_model_plugins:
                if db_query_session_model_plugin.plugin_id == db_query_plugin.plugin_id:
                    session_update = {"session_id": session_id, "plugin_id": db_query_session_model_plugin.plugin_id,
                                    "update_val": {"session_status": True}}
                    db_update_session_plugin = update_session_plugin([SessionUpdateReq(**session_update)])
                else:
                    session_update = {"session_id": session_id, "plugin_id": db_query_session_model_plugin.plugin_id,
                                    "update_val": {"session_status": False}}
                    db_update_session_plugin = update_session_plugin([SessionUpdateReq(**session_update)])

        # 查询session中指定模型插件是否存在
        db_query_session_plugin = query_session_plugin_by_id(session_id=session_id,
                                                                plugin_id=db_query_plugin.plugin_id)
        if db_query_session_plugin:
            return db_query_session_plugin
        else:
            plugin_param_list = await run_plugin_model_setting_script(plugin_path)
            if plugin_param_list:
                plugin_param = json.dumps(plugin_param_list)
                plugin_id = db_query_plugin.plugin_id
                db_create_session = create_session_plugin([schemas.SessionPluginBase(session_id=session_id,
                                                                                        plugin_id=plugin_id,
                                                                                        plugin_param=plugin_param,
                                                                                        session_status=True)])
                return db_create_session[0]
            else:
                log.error(f"can NOT get model setting.")
                return None



# --------------------other tool---------------------------------------

def plugins_init(user_id: str):
    plugins = [
        {"plugin_logo": "extension",
         "plugin_key": "preprocess_check_input",
         "plugin_name_en": "preprocess_check_input",
         "plugin_name_cn": "输入合法性检验",
         "plugin_path": "pkg.plugins.preprocess_check_input",
         "plugin_order": 6,
         "plugin_type": "default",
         "plugin_status": True,
         "description_en": "Checking inputs for compliance",
         "description_cn": "检查输入是否符合要求"},
        {"plugin_logo": "pi pi-shield",
         "plugin_key": "preprocess_sensitive_filter",
         "plugin_name_en": "preprocess_sensitive_filter",
         "plugin_name_cn": "敏感词检测",
         "plugin_path": "pkg.plugins.sensitive_filter_plugin.preprocess_sensitive_filter",
         "plugin_order": 5,
         "plugin_type": "normal",
         "plugin_status": True,
         "description_en": "Detect sensitive words in input",
         "description_cn": "检测输入中是否有敏感词"},
        {"plugin_logo": "pi pi-globe",
         "plugin_key": "preprocess_web_argument",
         "plugin_name_en": "preprocess_web_argument",
         "plugin_name_cn": "网络检索",
         "plugin_path": "pkg.plugins.web_argument_plugin.preprocess_web_argument",
         "plugin_order": 4,
         "plugin_type": "normal",
         "plugin_status": True,
         "description_en": "Web Search Related Content",
         "description_cn": "网络检索相关内容"},
        {"plugin_logo": "pi pi-book",
         "plugin_key": "retrievers",
         "plugin_name_en": "retrievers",
         "plugin_name_cn": "知识库",
         "plugin_path": "pkg.plugins.knowledge_base.retrievers",
         "plugin_order": 3,
         "plugin_type": "normal",
         "plugin_status": True,
         "description_en": "Knowledge Base Plugin",
         "description_cn": "知识库插件"},
        {"plugin_logo": "pi pi-file",
         "plugin_key": "chat_files_retrievers",
         "plugin_name_en": "chat_files_retrievers",
         "plugin_name_cn": "文档对话",
         "plugin_path": "pkg.plugins.chat_files.chat_files_retrievers",
         "plugin_order": 2,
         "plugin_type": "normal",
         "plugin_status": True,
         "description_en": "File Upload Plugin for Knowledge Base",
         "description_cn": "文档对话插件"},
        {"plugin_logo": "extension",
         "plugin_key": "preprocess_sensitive_filter_model",
         "plugin_name_en": "preprocess_sensitive_filter",
         "plugin_name_cn": "敏感词模型",
         "plugin_path": "pkg.plugins.sensitive_filter_plugin.preprocess_sensitive_filter",
         "plugin_order": 0,
         "plugin_type": "model",
         "plugin_status": False,
         "description_en": "Detect sensitive words model",
         "description_cn": "敏感词模型"},
         {"plugin_logo": "extension",
         "plugin_key": "deepseek_local",
         "plugin_name_en": "deepseek_local",
         "plugin_name_cn": "deepseek_local",
         "plugin_path": "pkg.plugins.chat_model_plugin.deepseek_local",
         "plugin_order": 0,
         "plugin_type": "model",
         "plugin_status": False,
         "description_en": "deepseek model",
         "description_cn": "deepseek_local模型"},
         {"plugin_logo": "extension",
         "plugin_key": "ollama",
         "plugin_name_en": "ollama",
         "plugin_name_cn": "ollama",
         "plugin_path": "pkg.plugins.chat_model_plugin.ollama",
         "plugin_order": 0,
         "plugin_type": "model",
         "plugin_status": False,
         "description_en": "ollama model",
         "description_cn": "ollama模型"},
         {"plugin_logo": "extension",
         "plugin_key": "tencent",
         "plugin_name_en": "tencent",
         "plugin_name_cn": "tencent",
         "plugin_path": "pkg.plugins.chat_model_plugin.tencent",
         "plugin_order": 0,
         "plugin_type": "model",
         "plugin_status": False,
         "description_en": "tencent model",
         "description_cn": "tencent模型"},
         {"plugin_logo": "extension",
         "plugin_key": "baidu",
         "plugin_name_en": "baidu",
         "plugin_name_cn": "baidu",
         "plugin_path": "pkg.plugins.chat_model_plugin.baidu",
         "plugin_order": 0,
         "plugin_type": "model",
         "plugin_status": False,
         "description_en": "baidu model",
         "description_cn": "baidu模型"},
         {"plugin_logo": "extension",
         "plugin_key": "deepseek_office",
         "plugin_name_en": "deepseek_office",
         "plugin_name_cn": "deepseek_office",
         "plugin_path": "pkg.plugins.chat_model_plugin.deepseek_office",
         "plugin_order": 0,
         "plugin_type": "model",
         "plugin_status": False,
         "description_en": "deepseek_office model",
         "description_cn": "deepseek_office模型"},
         {"plugin_logo": "extension",
         "plugin_key": "openai",
         "plugin_name_en": "openai",
         "plugin_name_cn": "openai",
         "plugin_path": "pkg.plugins.chat_model_plugin.openai",
         "plugin_order": 0,
         "plugin_type": "model",
         "plugin_status": False,
         "description_en": "openai model",
         "description_cn": "openai模型"},
         {"plugin_logo": "extension",
         "plugin_key": "kimi",
         "plugin_name_en": "kimi",
         "plugin_name_cn": "kimi",
         "plugin_path": "pkg.plugins.chat_model_plugin.kimi",
         "plugin_order": 0,
         "plugin_type": "model",
         "plugin_status": False,
         "description_en": "kimi model",
         "description_cn": "kimi模型"},
         {"plugin_logo": "extension",
         "plugin_key": "zhipu",
         "plugin_name_en": "zhipu",
         "plugin_name_cn": "zhipu",
         "plugin_path": "pkg.plugins.chat_model_plugin.zhipu",
         "plugin_order": 0,
         "plugin_type": "model",
         "plugin_status": False,
         "description_en": "zhipu model",
         "description_cn": "zhipu模型"},
        {"plugin_logo": "pi pi-shield",
         "plugin_key": "postprocess_sensitive_filter",
         "plugin_name_en": "postprocess_sensitive_filter",
         "plugin_name_cn": "后置敏感词检测",
         "plugin_path": "pkg.plugins.sensitive_filter_plugin.postprocess_sensitive_filter",
         "plugin_order": -1,
         "plugin_type": "normal",
         "plugin_status": False,
         "description_en": "Detect sensitive words in output",
         "description_cn": "检测输出中是否有敏感词"},
        {"plugin_logo": "extension",
         "plugin_key": "postprocess_clean_specialchars",
         "plugin_name_en": "postprocess_clean_specialchars",
         "plugin_name_cn": "后置清理特殊字符",
         "plugin_path": "pkg.plugins.postprocess_clean_specialchars",
         "plugin_order": -2,
         "plugin_type": "default",
         "plugin_status": False,
         "description_en": "Cleaning up special characters in the output",
         "description_cn": "清理输出中的特殊字符"},
        {"plugin_logo": "extension",
         "plugin_key": "postprocess_formula_rendering",
         "plugin_name_en": "postprocess_formula_rendering",
         "plugin_name_cn": "后置公式渲染",
         "plugin_path": "pkg.plugins.postprocess_formula_rendering",
         "plugin_order": -3,
         "plugin_type": "default",
         "plugin_status": False,
         "description_en": "Render formulas in the output",
         "description_cn": "渲染输出中的公式"},
        {"plugin_logo": "pi pi-globe",
         "plugin_key": "postprocess_web_argument",
         "plugin_name_en": "postprocess_web_argument",
         "plugin_name_cn": "后置网络检索",
         "plugin_path": "pkg.plugins.web_argument_plugin.postprocess_web_argument",
         "plugin_order": -4,
         "plugin_type": "normal",
         "plugin_status": False,
         "description_en": "Web Search Related Content",
         "description_cn": "网络检索相关内容"}
    ]

    for plugin in plugins:
        plugin_base = PluginBaseMo(**plugin)
        db_create_plugin = create_plugin(plugin=plugin_base, user_id=user_id)
        if db_create_plugin:
            log.info(f"Plugin {db_create_plugin.plugin_name_en} create SUCCESSFUL.")


async def run_plugin_model_setting_script(plugin_path):
    try:
        log.info("plugin_path:{0}".format(plugin_path))
        load_model_result = importlib.import_module(plugin_path)
        # 执行脚本中的函数
        exec_result = load_model_result.get_default_settings()
        if exec_result:
            return exec_result
        else:
            return None
    except Exception as e:
        log.error(f"Error:get model plugin setting'{plugin_path}': {str(e)}")
        return None


def run_plugin_script(plugin_id, item, setting, content_setting):
    try:
        with SessionLocal() as db:
            # 加载脚本文件
            db_plugin = query_plugin_by_id(plugin_id)
            plugin_path = db_plugin.plugin_path

            # plugin_path = f"{plugin_path}.py"
            # spec = importlib.util.spec_from_file_location("MyPlugin", plugin_path)
            # module = importlib.util.module_from_spec(spec)
            # spec.loader.exec_module(module)

            load_model_result = importlib.import_module(plugin_path)

            # 执行脚本中的函数
            exec_result = load_model_result.call(item, setting, content_setting)
            if not exec_result:
                exec_result["flag"] = False

            return exec_result
    except Exception as e:
        log.error(f"Error: run_plugin_script executing plugin '{plugin_path}': {str(e)}")
        return {"flag": False, "result": None, "setting": setting, "content_setting": content_setting}


def pre_or_post_process(session_id: str, plugin_turn: str, item, setting: dict, content_setting: dict):
    with SessionLocal() as db:
        
        # 根据session获取已激活插件列表，按顺序执行插件
        # 查询结果：[{'session_id': 'ijukaeghrdfiubfqo2w35sdgf', 'plugin_id': 3, 'plugin_param': '[]', 'status': True, 'id': 5,
        # 'create_time': datetime.datetime(2024, 5, 9, 14, 52, 54, 728676), 'update_time': datetime.datetime(2024, 5, 9, 14, 52, 54, 728705)}]
        try:
            db_query_active_plugins = query_activeplugin_by_sessionid(session_id=session_id)
        except Exception as ex:
            log.error("event_stream error" + str(ex))

        # 定义执行结果结构
        if plugin_turn == "pre":
            run_result = {"flag": True, "result": {"content": item.message, "refs": [], "recommend_question": []},
                          "setting": setting,
                          "content_setting": content_setting}
        else:
            run_result = {"flag": True,
                          "result": {"content": content_setting["output_answer"], "refs": [], "recommend_question": []},
                          "setting": setting,
                          "content_setting": content_setting}

        # 如果有已激活插件，获取激活插件
        if db_query_active_plugins:
            pos_plugins = db_query_active_plugins['pos_plugin']
            zero_plugins = db_query_active_plugins['zero_plugin']
            neg_plugins = db_query_active_plugins['neg_plugin']

            # 前处理
            if plugin_turn == "pre":
                # 执行顺序大于0的插件
                if pos_plugins:
                    for pos_plugin in pos_plugins:
                        plugin_id = pos_plugin.plugin_id
                        plugin_param = pos_plugin.plugin_param
                        db_query = query_plugin_by_id(plugin_id=plugin_id)
                        plugin_type = db_query.plugin_type

                        try:
                            # 处理setting, content_setting(TODO)
                            setting = process_setting(setting=setting, plugin_param=plugin_param, type=plugin_type)
                            # 执行插件（TODO）
                            run_result = run_plugin_script(plugin_id, item, setting, content_setting)
                            run_result["setting"] = {}
                            if run_result['flag'] == False:
                                return run_result

                        except Exception as ex:
                            log.error("event_stream error" + str(ex))
                            run_result["result"] = {"content": str(ex), "refs": [], "recommend_question": []}
                            run_result["flag"] = False
                            run_result["content_setting"] = content_setting
                            return run_result
                
                ##检查plugin_param是否为空
                    #如果为空，更新plugin_param
                

                # 执行顺序等于0的模型插件
                if zero_plugins:
                    setting = {}
                    for zero_plugin in zero_plugins:
                        plugin_id = zero_plugin.plugin_id
                        plugin_param = zero_plugin.plugin_param
                        db_query = query_plugin_by_id(plugin_id=plugin_id)
                        plugin_type = db_query.plugin_type

                        try:
                            # 处理setting, content_setting(TODO)
                            setting = process_setting(setting=setting, plugin_param=plugin_param, type=plugin_type)
                            run_result["setting"] = setting

                        except Exception as ex:
                            log.error("参数配置有误，正在重新配置参数...")
                            
                            
                            fix_db_sessions = db.query(SessionPlugins).filter(SessionPlugins.plugin_id == plugin_id).all()
                            
                            fix_db = db.query(PluginMo).filter(PluginMo.plugin_id == plugin_id).first()
                            path = fix_db.plugin_path
                            load_model_result = importlib.import_module(path)
                            # 执行脚本中的函数
                            exec_result = load_model_result.get_default_settings()
                            fix_db.plugin_param = json.dumps(exec_result)
                            db.commit()
                            db.refresh(fix_db)
                            for fix_db_session in fix_db_sessions:
                                fix_db_session.plugin_param =  json.dumps(exec_result)
                                db.commit()
                                db.refresh(fix_db_session)
                            

                            log.info("参数重新配置完成，请重新输入...")
                            run_result["result"] = {"content": "参数重新配置完成，请重新输入", "refs": [], "recommend_question": []}
                            run_result["flag"] = False
                            run_result["content_setting"] = content_setting
                            return run_result

            # 后处理
            elif plugin_turn == "post":
                # 执行顺序小于0的插件
                if neg_plugins:
                    for neg_plugin in neg_plugins:
                        plugin_id = neg_plugin.plugin_id
                        plugin_param = neg_plugin.plugin_param
                        db_query = query_plugin_by_id(plugin_id=plugin_id)
                        plugin_type = db_query.plugin_type
                        try:
                            # 处理setting, content_setting
                            setting = process_setting(setting=setting, plugin_param=plugin_param, type=plugin_type)
                            # 执行插件
                            run_result = run_plugin_script(plugin_id, item, setting, content_setting)
                            if run_result['flag'] == False:
                                return run_result

                        except Exception as ex:
                            log.error("event_stream error" + str(ex))
                            run_result["result"] = {"content": str(ex), "refs": [], "recommend_question": []}
                            run_result["flag"] = False
                            run_result["content_setting"] = content_setting
                            return run_result
            # log.info(f"---------run_result------:{run_result}")
            return run_result
        else:
            return run_result


def process_setting(setting, plugin_param, type):
    # 获取插件参数
    if type == "model" or type == "default":
        # 将JSON字符串转换为Python列表
        param_datas = json.loads(plugin_param)
        model_dict = {param_data['arg_name']: param_data['arg_value'] for param_data in param_datas}
        # 创建新的字典，从每个元素中提取arg_name作为键，arg_value作为值
        setting.update(model_dict)
        # for param_data in param_datas:
        #     model_dict = {param_data['arg_name']: param_data['arg_value']}
        #     # 创建新的字典，从每个元素中提取arg_name作为键，arg_value作为值
        #     setting.update(model_dict)

    elif type == "normal":
        # 将JSON字符串转换为Python列表
        param_datas = json.loads(plugin_param)
        setting.update(param_datas)

    return setting