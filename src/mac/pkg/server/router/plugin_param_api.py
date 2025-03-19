from typing import Union
import os
from ...logger import Log
from fastapi import APIRouter, Depends
from ...database import schemas
from ...server import schemas as server_schema
from ..process import process_plugin_param, process_chat, process_model
from ...projectvar import constants as const
from ...projectvar import statuscode
from ..depends import get_headers

router = APIRouter(
    prefix="/plugin-param",
    tags=["plugin-param"],
    responses={404: {"description": "Not found"}}, )

log = Log()


class UserPluginWebSearchParamResponseInfo(server_schema.CommonResponse):
    resData: Union[schemas.UserPluginWebSearchParamInfo, None]


class UserPluginSensitiveParamResponseInfo(server_schema.CommonResponse):
    resData: Union[schemas.SensitiveSettingInfo, None]


@router.get("/web-search/list", response_model=UserPluginWebSearchParamResponseInfo)
async def get_web_search_plugin_param(session_id: str, plugin_id: int, headers=Depends(get_headers)):
    result = UserPluginWebSearchParamResponseInfo
    try:
        session_info = process_chat.get_session_info(session_id, headers[const.HTTP_HEADER_USER_ID])
        if session_info is None:
            return result.fail(statuscode.StatusCodeEnum.DB_NOTFOUND_ERR.code, statuscode.StatusCodeEnum.DB_NOTFOUND_ERR.errmsg)
        plugin_param_list = process_plugin_param.get_web_search_param(headers[const.HTTP_HEADER_USER_ID], session_id, plugin_id)
        result_param = schemas.UserPluginWebSearchParamInfo
        for userPluginParam in plugin_param_list:
            if userPluginParam.param_key == "web_search.retrieve_topk":
                result_param.retrieve_topk = int(userPluginParam.param_value)
            elif userPluginParam.param_key == "web_search.embedding_model_id":
                if userPluginParam.param_value is not None and len(userPluginParam.param_value) > 0:
                    result_param.embedding_model_id = int(userPluginParam.param_value)
                else:
                    result_param.embedding_model_id = None
            elif userPluginParam.param_key == "web_search.style_search":
                result_param.style_search = userPluginParam.param_value
            elif userPluginParam.param_key == "web_search.template":
                result_param.template = userPluginParam.param_value
            elif userPluginParam.param_key == "web_search.web_api_key":
                result_param.web_api_key = userPluginParam.param_value
            else:
                continue
        return result.success(result_param)
    except Exception as ex:
        import traceback
        print(traceback.format_exc())
        log.error(f"plugin_param_api get_web_search_plugin_param error, {str(ex)}")
        return result.fail(statuscode.StatusCodeEnum.UNKNOWN.code, str(ex))


@router.get("/sensitive/list", response_model=UserPluginSensitiveParamResponseInfo)
async def get_sensitive_plugin_param_list(session_id: str, plugin_id: int, headers=Depends(get_headers)):
    result = UserPluginSensitiveParamResponseInfo
    try:
        plugin_param_list = process_plugin_param.get_sensitive_setting_list(headers[const.HTTP_HEADER_USER_ID], session_id, plugin_id)
        return result.success(plugin_param_list)
    except Exception as ex:
        log.error(f"plugin_param_api get_sensitive_plugin_param_list error, {str(ex)}")
        return result.fail(statuscode.StatusCodeEnum.UNKNOWN.code, str(ex))


@router.put("/web-search/update/{session_id}")
async def update_websearch_plugin_param(session_id: str, item: schemas.UserPluginWebSearchParamUpdateInfo, headers=Depends(get_headers)):
    result = server_schema.CommonResponse
    try:
        model_exist = False
        # embedding_model_list = process_model.get_download_embedding_model_list()
        embedding_model_list = process_model.get_download_ollama_embedding_model_list()
        if item.embedding_model_id is not None:
            for model_item in embedding_model_list:
                if model_item.get("id") == item.embedding_model_id:
                    model_exist = True
            if not model_exist:
                return result.fail(statuscode.StatusCodeEnum.DB_NOTFOUND_ERR.code, statuscode.StatusCodeEnum.DB_NOTFOUND_ERR.errmsg)
        if item.style_search is not None and len(item.style_search) > 0:
            if item.style_search not in ["serper", "bing_api", "bing_bs4"]:
                return result.fail(statuscode.StatusCodeEnum.YUAN_MODEL_PARAM_INVALID_ERROR.code,
                                   statuscode.StatusCodeEnum.YUAN_MODEL_PARAM_INVALID_ERROR.errmsg)
        update_result = process_plugin_param.update_web_search(headers[const.HTTP_HEADER_USER_ID], session_id, item)
        if update_result:
            return result.success(True)
        else:
            return result.fail(statuscode.StatusCodeEnum.YUAN_BIZ_DATA_UPDATE_FAILED_ERROR.code, statuscode.StatusCodeEnum.YUAN_BIZ_DATA_UPDATE_FAILED_ERROR.errmsg)
    except Exception as ex:
        log.error(f"plugin_param_api update_websearch_plugin_param error, {str(ex)}")
        return result.fail(statuscode.StatusCodeEnum.UNKNOWN.code, str(ex))


@router.put("/sensitive/update/{session_id}")
async def update_sensitive_plugin_param(item: schemas.SensitiveSettingUpdateInfo, session_id: str, headers=Depends(get_headers)):
    result = server_schema.CommonResponse
    try:
        if item.local_model is not None and item.local_model.model_id is not None and len(item.local_model.filter_model_list) <= 0:
            return result.fail(statuscode.StatusCodeEnum.YUAN_MODEL_PARAM_INVALID_ERROR.code,
                               statuscode.StatusCodeEnum.YUAN_MODEL_PARAM_INVALID_ERROR.errmsg)
        if item.local_model is not None and item.local_model.model_id is not None:
            embedding_model_list = process_model.list([item.local_model.model_id])
            if len(embedding_model_list) <= 0:
                return result.fail(statuscode.StatusCodeEnum.YUAN_MODEL_PARAM_INVALID_ERROR.code,
                               statuscode.StatusCodeEnum.YUAN_MODEL_PARAM_INVALID_ERROR.errmsg)
        if "local_model" in item.style_filter_list and (len(item.local_model.filter_model_list) <= 0 or item.local_model.model_id is None):
            return result.fail(statuscode.StatusCodeEnum.YUAN_MODEL_PARAM_INVALID_ERROR.code, statuscode.StatusCodeEnum.YUAN_MODEL_PARAM_INVALID_ERROR.errmsg)
        update_result = process_plugin_param.update_sensitive_setting_info(headers[const.HTTP_HEADER_USER_ID], session_id, item)
        if update_result:
            return result.success(True)
        else:
            return result.fail(statuscode.StatusCodeEnum.YUAN_BIZ_DATA_UPDATE_FAILED_ERROR.code, statuscode.StatusCodeEnum.YUAN_BIZ_DATA_UPDATE_FAILED_ERROR.errmsg)
    except Exception as ex:
        log.error(f"plugin_param_api update_sensitive_plugin_param error, {str(item)}, {str(ex)}")
        return result.fail(statuscode.StatusCodeEnum.UNKNOWN.code, str(ex))
