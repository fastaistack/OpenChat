import os

from fastapi import Depends, APIRouter, Request
from sqlalchemy.orm import Session
from typing import Union, List, Dict, Optional
from pydantic import BaseModel
from ...projectvar import Projectvar
from ...projectvar.statuscode import StatusCodeEnum as status
from ...logger import Log
from ...database import models, schemas
from ..process import plugin_process as dbcrud
from ...server import schemas as server_schemas
from ..depends import get_headers
from ...projectvar import constants as const
import json
from ...database.schemas import PluginBaseMo, PluginInDB, SessionPluginBase, SessionPluginInDB
from ...projectvar.statuscode import StatusCodeEnum
from ...database.database import SessionLocal

"""初始化"""
gvar = Projectvar()
log = Log()

router = APIRouter(
    prefix="/plugin",
    tags=["plugin"],
    responses={404: {"description": "Not found"}},
)


# ----------------------plugin------------------------------------
"""请求/响应结构体定义"""


class PluginResponse(server_schemas.CommonResponse):
    resData: Union[str, PluginBaseMo, PluginInDB, None]


class PluginListResponse(server_schemas.CommonResponse):
    resData: Union[List[PluginInDB], str, None]


class PluginGetRequest(BaseModel):
    plugin_id: int


class PluginGetListRequest(BaseModel):
    plugin_type: str
    plugin_status: bool
    search_type: str


class PluginUpdateRequest(BaseModel):
    plugin_id: int
    update_val: dict


@router.post("/create", response_model=PluginResponse)
async def create(plugin: PluginBaseMo, headers=Depends(get_headers)):
    user_id = headers[const.HTTP_HEADER_USER_ID]
    # language = headers[const.HTTP_HEADER_ACCEPT_LANGUAGE]
    try:
        result = PluginResponse
        db_plugin = dbcrud.create_plugin(plugin, user_id=user_id)
        if db_plugin:
            plugin_db = PluginInDB.from_orm(db_plugin)
            # if language == "cn":
            #     plugin_db.plugin_name = plugin_db.plugin_name_en
            #     plugin_db.description = plugin_db.description_cn
            # else:
            #     plugin_db.plugin_name = plugin_db.plugin_name_en
            #     plugin_db.description = plugin_db.description_en
            return result.success(plugin_db)
        else:
            return result.success(None)
    except Exception as ex:
        log.error("plugin: create error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.post("/get", response_model=PluginResponse)
async def get(req: PluginGetRequest, headers=Depends(get_headers)):
    try:
        result = PluginResponse
        user_id = headers[const.HTTP_HEADER_USER_ID]
        language = headers[const.HTTP_HEADER_ACCEPT_LANGUAGE]
        plugin = dbcrud.query_plugin_by_id(req.plugin_id)
        if plugin:
            plugin_db = PluginInDB.from_orm(plugin)
            if language == "cn":
                plugin_db.plugin_name = plugin_db.plugin_name_cn
                plugin_db.description = plugin_db.description_cn
            else:
                plugin_db.plugin_name = plugin_db.plugin_name_en
                plugin_db.description = plugin_db.description_en
            return result.success(plugin_db)
        else:
            return result.success(None)
    except Exception as ex:
        log.error("plugin: get error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.post("/getlist", response_model=PluginListResponse)
async def getlist(req: PluginGetListRequest, headers=Depends(get_headers)):
    try:
        result = PluginListResponse
        user_id = headers[const.HTTP_HEADER_USER_ID]
        language = headers[const.HTTP_HEADER_ACCEPT_LANGUAGE]
        plugins = dbcrud.query_plugins(plugin_type=req.plugin_type, plugin_status=req.plugin_status,
                                     search_type=req.search_type, user_id=user_id)
        if plugins:
            res = []
            for plugin in plugins:
                plugin_db = PluginInDB.from_orm(plugin)
                if language == "cn":
                    plugin_db.plugin_name = plugin_db.plugin_name_cn
                    plugin_db.description = plugin_db.description_cn
                    res.append(plugin_db)
                else:
                    plugin_db.plugin_name = plugin_db.plugin_name_en
                    plugin_db.description = plugin_db.description_en
                    res.append(plugin_db)
            return result.success(res)
            # return result.success([PluginInDB.from_orm(plugin) for plugin in plugins])
        else:
            return result.success(None)
    except Exception as ex:
        log.error("plugin: getlist error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.post("/update", response_model=PluginResponse)
async def plugin_update(req: PluginUpdateRequest, headers=Depends(get_headers)):
    try:
        result = PluginResponse
        user_id = headers[const.HTTP_HEADER_USER_ID]
        db_update_plugin = dbcrud.update_plugin(plugin_id=req.plugin_id, update_val=req.update_val, user_id=user_id)
        if db_update_plugin:
            return result.success(PluginInDB.from_orm(db_update_plugin))
        else:
            return result.success(None)
    except Exception as ex:
        log.error("plugin: update error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.post("/delete", response_model=PluginResponse)
async def plugin_delete(req: PluginGetRequest, headers=Depends(get_headers)):
    try:
        result = PluginResponse
        user_id = headers[const.HTTP_HEADER_USER_ID]
        db_delete_plugin = dbcrud.delete_plugin(req.plugin_id, user_id=user_id)
        if db_delete_plugin:
            return result.success("DELETE PLUGIN SUCCESS.")
    except Exception as ex:
        log.error("plugin: delete error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.post("/createforall", response_model=PluginListResponse)
async def createforall(plugin: PluginBaseMo):
    # user_id = headers[const.HTTP_HEADER_USER_ID]
    # language = headers[const.HTTP_HEADER_ACCEPT_LANGUAGE]
    try:
        result = PluginListResponse
        res = []
        db_plugins = dbcrud.create_new_plugin(plugin)
        if db_plugins:
            for db_plugin in db_plugins:
                plugin_db = PluginInDB.from_orm(db_plugin)
                res.append(plugin_db)
            return result.success(res)
        else:
            return result.success(None)
    except Exception as ex:
        log.error("plugin: create error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)
    
    
@router.post("/updatepluginparam", response_model=PluginListResponse)
async def plugin_param_update():
    try:
        res = []
        result = PluginListResponse
        db_update_plugins = dbcrud.get_and_update_plugin_param()
        if db_update_plugins:
            for db_update_plugin in db_update_plugins:
                res.append(PluginInDB.from_orm(db_update_plugin))
            return result.success(res)
        else:
            return result.success(res)
    except Exception as ex:
        log.error("plugin: update error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


# -----------------------session plugin-----------------------------------
"""请求/响应结构体定义"""


class SessionPluginGetRequest(BaseModel):
    plugin_name_en: str


class SessionPluginResponse(server_schemas.CommonResponse):
    resData: Union[str, SessionPluginBase, SessionPluginInDB, None]


class SessionPluginListResponse(server_schemas.CommonResponse):
    resData: Union[List[SessionPluginInDB], str, None]


class SessionGetListReq(BaseModel):
    session_id: str
    plugin_type: str
    status: bool
    search_type: str


class SessionPluginListResponseTest(server_schemas.CommonResponse):
    resData: Union[List[dict], str, None]


class SessionUpdateReq(BaseModel):
    session_id: str
    plugin_id: int
    update_val: dict


class SessionUpdateResponse(server_schemas.CommonResponse):
    resData: Union[List[SessionPluginInDB], str, None]


class SessionDeleteReq(BaseModel):
    session_plugin_id: int


@router.post("/session/create", response_model=SessionPluginListResponse)
async def session_plugin_create(plugins: List[SessionPluginBase]):
    with SessionLocal() as db:
        try:
            result = SessionPluginListResponse
            db_plugins = dbcrud.create_session_plugin(plugins)
            if db_plugins:
                return result.success([SessionPluginInDB.from_orm(db_plugin) for db_plugin in db_plugins])
            else:
                return result.success(None)
        except Exception as ex:
            log.error("plugin: create error", str(ex))
            return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.post("/session/getlist", response_model=SessionPluginListResponseTest)
async def getlist(req: SessionGetListReq, headers=Depends(get_headers)):
    try:
        result = SessionPluginListResponseTest
        user_id = headers[const.HTTP_HEADER_USER_ID]
        language = headers[const.HTTP_HEADER_ACCEPT_LANGUAGE]
        
        db_querys = dbcrud.query_plugins(plugin_type="normal", plugin_status=True, search_type="one_type_status", user_id=user_id)
        if db_querys:
            for db_query in db_querys:
                db_plugin = dbcrud.query_session_plugin_by_id(session_id=req.session_id, plugin_id=db_query.plugin_id)
                if not db_plugin:
                    db_create_session = dbcrud.create_session_plugin([schemas.SessionPluginBase(session_id=req.session_id, plugin_id=db_query.plugin_id, plugin_param=db_query.plugin_param, session_status=False)])
            
        plugins = dbcrud.query_session_plugins(session_id=req.session_id, plugin_type=req.plugin_type, status=req.status,
                                             search_type=req.search_type)
        if plugins:
            results = []
            for session_plugin, plugin_mo in plugins:
                plugin_mo_db = PluginInDB.from_orm(plugin_mo)
                if language == "cn":
                    plugin_mo_db.plugin_name = plugin_mo_db.plugin_name_cn
                    plugin_mo_db.description = plugin_mo_db.description_cn
                else:
                    plugin_mo_db.plugin_name = plugin_mo_db.plugin_name_en
                    plugin_mo_db.description = plugin_mo_db.description_en

                # 使用 SessionPluginInDB PluginInDB模型组装数据
                combined_data = {
                    **SessionPluginInDB.from_orm(session_plugin).dict(),
                    # **PluginInDB.from_orm(plugin_mo).dict()
                    **plugin_mo_db.dict()
                }
                results.append(combined_data)
            if results:
                return result.success(results)
            else:
                return result.success([])
        else:
            return result.success([])
    except Exception as ex:
        log.error("plugin: getlist error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.post("/session/update", response_model=SessionUpdateResponse)
async def plugin_update(session_update: List[SessionUpdateReq], headers=Depends(get_headers)):
    try:
        result = SessionUpdateResponse
        user_id = headers[const.HTTP_HEADER_USER_ID]
        db_update_plugins = dbcrud.update_session_plugin(session_update, user_id)
        session_update = []
        if db_update_plugins:
            return result.success(
                [SessionPluginInDB.from_orm(db_update_plugin) for db_update_plugin in db_update_plugins])
        else:
            return result.success(None)
    except Exception as ex:
        log.error("plugin: update error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, str(ex))


@router.post("/session/delete", response_model=SessionPluginResponse)
async def plugin_delete(req: SessionDeleteReq):
    try:
        result = SessionPluginResponse
        db_delete_plugin = dbcrud.delete_session_plugin(req.session_plugin_id)
        if db_delete_plugin:
            return result.success("DELETE PLUGIN SUCCESS.")
    except Exception as ex:
        log.error("plugin: delete error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


# -------------------------other api---------------------------------

class SessionPluginSetResponse(server_schemas.CommonResponse):
    resData: Union[List[schemas.SessionPluginInDB], str, None]


class ModelGetRequest(BaseModel):
    session_id: str
    model_id: int


class SessionPluginGetModelResponse(server_schemas.CommonResponse):
    resData: Union[str, SessionPluginInDB, SessionPluginBase, None]


class ModelPluginSetRequest(ModelGetRequest):
    plugin_param: str


@router.post("/session/getmodelsettings", response_model=SessionPluginGetModelResponse)
async def getsettings(model: ModelGetRequest, db: Session = Depends(dbcrud.get_db), headers=Depends(get_headers)):
    try:
        result = SessionPluginGetModelResponse

        user_id = headers[const.HTTP_HEADER_USER_ID]
        session_id = model.session_id
        model_id = model.model_id

        # 查询模型列表中数据：
        model_search_results = db.query(models.Model).filter_by(id=model_id).first()
        # model_download = ModelDownload()
        # model_search_results = model_download._get_model_info(id=model_id)
        # 组建路径和插件名
        plugin_path = model_search_results.plugin
        plugin_key = plugin_path.split('.')[-1]

        # 根据名称判断模型插件是否存在（默认：模型插件不改名）
        db_query_plugin = dbcrud.query_plugin_by_key_and_type(plugin_key=plugin_key, plugin_type="model", user_id=user_id)
        if not db_query_plugin:
            log.info(f"Model Plugin: {plugin_key} is NOT exist.")
            return result.success(None)

        # 将“session”中模型插件中只保留一个模型是激活状态
        db_query_plugins = dbcrud.query_session_plugins(session_id=session_id, plugin_type="model", search_type="one_type")
        # for db_query_session_model_plugins, plugin_mo in db_query_plugins:
        if db_query_plugins:
            for db_query_session_model_plugin, plugin_mo in db_query_plugins:
                # for db_query_session_model_plugin in db_query_session_model_plugins:
                if db_query_session_model_plugin.plugin_id == db_query_plugin.plugin_id:
                    session_update = {"session_id": session_id, "plugin_id": db_query_session_model_plugin.plugin_id,
                                    "update_val": {"session_status": True}}
                    db_update_session_plugin = dbcrud.update_session_plugin([SessionUpdateReq(**session_update)])
                else:
                    session_update = {"session_id": session_id, "plugin_id": db_query_session_model_plugin.plugin_id,
                                    "update_val": {"session_status": False}}
                    db_update_session_plugin = dbcrud.update_session_plugin([SessionUpdateReq(**session_update)])

        # 查询session中指定模型插件是否存在
        db_query_session_plugin = dbcrud.query_session_plugin_by_id(session_id=session_id,
                                                                plugin_id=db_query_plugin.plugin_id)
        if db_query_session_plugin:
            return result.success(SessionPluginInDB.from_orm(db_query_session_plugin))
        else:
            plugin_param_list = await dbcrud.run_plugin_model_setting_script(plugin_path)
            if plugin_param_list:
                plugin_param = json.dumps(plugin_param_list)
                plugin_id = db_query_plugin.plugin_id
                db_create_session = dbcrud.create_session_plugin([schemas.SessionPluginBase(session_id=session_id,
                                                                                        plugin_id=plugin_id,
                                                                                        plugin_param=plugin_param,
                                                                                        session_status=True)])
                return result.success(SessionPluginInDB.from_orm(db_create_session[0]))
            else:
                log.error(f"can NOT get model setting.")
                return result.success(None)
    except Exception as ex:
        log.error("session: getmodelsettings error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.post("/session/setmodelsettings", response_model=SessionPluginGetModelResponse)
async def setsettings(model: ModelPluginSetRequest, db: Session = Depends(dbcrud.get_db), headers=Depends(get_headers)):
    try:
        result = SessionPluginGetModelResponse
        user_id = headers[const.HTTP_HEADER_USER_ID]
        session_id = model.session_id
        model_id = model.model_id
        plugin_param = model.plugin_param

        # 查询模型列表中数据：
        model_search_results = db.query(models.Model).filter_by(id=model_id).first()

        # 组建路径和插件名
        plugin_path = model_search_results.plugin
        plugin_key = plugin_path.split('.')[-1]

        # 根据名称判断模型插件是否存在（默认：模型插件不改名）
        db_query_plugin = dbcrud.query_plugin_by_key_and_type(plugin_key=plugin_key, plugin_type="model", user_id=user_id)
        if not db_query_plugin:
            log.info(f"Model Plugin: {plugin_key} is NOT exist.")
            return result.success(None)

        # 将“session”中模型插件中只保留一个模型是激活状态
        db_query_plugins = dbcrud.query_session_plugins(session_id=session_id, plugin_type="model", search_type="one_type")
        # for db_query_session_model_plugins, plugin_mo in db_query_plugins:
        if db_query_plugins:
            for db_query_session_model_plugin, plugin_mo in db_query_plugins:
                # for db_query_session_model_plugin in db_query_session_model_plugins:
                if db_query_session_model_plugin.plugin_id == db_query_plugin.plugin_id:
                    session_plugin = {"session_id": session_id, "plugin_id": db_query_session_model_plugin.plugin_id,
                                    "update_val": {"plugin_param": plugin_param, "session_status": True}}
                    db_update_session_plugin = dbcrud.update_session_plugin([SessionUpdateReq(**session_plugin)])
                else:
                    session_plugin = {"session_id": session_id, "plugin_id": db_query_session_model_plugin.plugin_id,
                                    "update_val": {"session_status": False}}
                    db_update_session_plugin = dbcrud.update_session_plugin([SessionUpdateReq(**session_plugin)])

        # 查询session中指定模型插件是否存在
        db_query_session_plugin = dbcrud.query_session_plugin_by_id(session_id=session_id,
                                                                plugin_id=db_query_plugin.plugin_id)
        if db_query_session_plugin:
            return result.success(SessionPluginInDB.from_orm(db_query_session_plugin))
        else:
            plugin_id = db_query_plugin.plugin_id
            db_create_session = dbcrud.create_session_plugin([schemas.SessionPluginBase(session_id=session_id,
                                                                                        plugin_id=plugin_id,
                                                                                        plugin_param=plugin_param,
                                                                                        session_status=True)])
            return result.success(SessionPluginInDB.from_orm(db_create_session[0]))
    except Exception as ex:
        log.error("session: setmodelsettings error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)