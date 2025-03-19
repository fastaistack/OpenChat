import os
import shutil
from typing import Optional

from ...logger import Log
from fastapi import APIRouter, Depends

from ..depends import get_headers
from ..process import process_setting
from ...projectvar.statuscode import StatusCodeEnum
from ...server import schemas as server_schema
from ...projectvar import constants as const
from pydantic import BaseModel


router = APIRouter(
    prefix="/setting",
    tags=["settings"],
    responses={404: {"description": "Not found"}},
)
log = Log()


class SettingSystemPathInfo(BaseModel):
    config_value: str
    migrate_status: Optional[str] = None


class SettingSystemPathInfoResponse(server_schema.CommonResponse):
    resData: Optional[SettingSystemPathInfo] = None


@router.get("/system/default/path", response_model=SettingSystemPathInfoResponse)
async def get_system_default_path():
    result = SettingSystemPathInfoResponse
    try:
        path = process_setting.get_system_default_path()
        path_info = SettingSystemPathInfo(config_value=path.config_value, migrate_status="")
        result_info = process_setting.get_system_path_migrate_state()
        setting_system_path_info = SettingSystemPathInfo
        setting_system_path_info.config_value = path.config_value
        # calc total status
        status_info = ""
        if result_info.get("knowledge").get("status") == "NOT_MOVED" and result_info.get("model").get("status") == "NOT_MOVED":
            status_info = "NOT_MOVED"
        elif result_info.get("knowledge").get("status") == "MOVING" or result_info.get("model").get("status") == "MOVING":
            status_info = "MOVING"
        elif result_info.get("knowledge").get("status") == "FAILED" or result_info.get("model").get("status") == "FAILED":
            status_info = "FAILED"
        else:
            status_info = "SUCCESS"
        setting_system_path_info.migrate_status = status_info
        return result.success(setting_system_path_info)
    except Exception as ex:
        log.error(f"setting.get_system_default_path error,{str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.put("/system/path/update")
async def update_system_default_path(item: SettingSystemPathInfo):
    result = server_schema.CommonResponse
    try:
        if not os.path.exists(item.config_value):
            return result.fail(StatusCodeEnum.SYSTEM_FILE_PATH_NOT_EXIST.code, StatusCodeEnum.SYSTEM_FILE_PATH_NOT_EXIST.errmsg)

        """获取设置路径所在盘、知识库和模型的占用空间，并判断剩余空间"""
        # 获取设置路径所在盘的空间信息
        total_b, used_b, free_b = shutil.disk_usage(item.config_value[0:2])
        # 获取知识库占用空间信息
        from pkg.server.router import knowledge
        knowledge_volume_result = knowledge.get_move_knowledge_volume()
        if knowledge_volume_result.get("errCode") != 0:
            return result.fail(knowledge_volume_result.get("errCode"), knowledge_volume_result.get("errMsg"))
        knowledge_volume_bytes = knowledge_volume_result.get("volume")
        # 获取模型占用空间
        from pkg.server.process import process_model
        model_volume_result_flag, model_volume_result_volume = process_model.get_models_volum()
        if not model_volume_result_flag:
            return result.fail(StatusCodeEnum.SYSTEM_PATH_MOVE_FAIL.code, StatusCodeEnum.SYSTEM_PATH_MOVE_FAIL.errmsg)
        if free_b <= (knowledge_volume_bytes + model_volume_result_volume):
            return result.fail(StatusCodeEnum.SYSTEM_PATH_SPACE_NOT_ENOUGH.code, StatusCodeEnum.SYSTEM_PATH_SPACE_NOT_ENOUGH.errmsg)

        # 获取系统原配置
        system_default_path = process_setting.get_system_default_path()
        # 更新数据库配置
        operate_flag = process_setting.update_system_default_path(item.config_value)
        if not operate_flag:
            return result.fail(StatusCodeEnum.YUAN_BIZ_DATA_UPDATE_FAILED_ERROR.code, StatusCodeEnum.YUAN_BIZ_DATA_UPDATE_FAILED_ERROR.errmsg)
        # 迁移知识库和模型
        if system_default_path.config_value is not None and system_default_path.config_value != "":
            knowledge_move_result = knowledge.mv_knowledge_file(system_default_path.config_value, item.config_value)
            if not knowledge_move_result.get("flag"):
                # 校验失败，则回退配置
                process_setting.update_system_default_path(system_default_path.config_value)
                return result.fail(knowledge_move_result.get("errCode"), knowledge_move_result.get("errMsg"))
            model_move_result_flag, model_move_result_msg = process_model.move_start()
            if not model_move_result_flag:
                # 校验失败，则回退配置
                process_setting.update_system_default_path(system_default_path.config_value)
                return result.fail(StatusCodeEnum.SYSTEM_PATH_MOVE_FAIL.code, model_move_result_msg)

        return result.success(True)
    except Exception as ex:
        log.error(f"setting.update_system_default_path error,{str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


@router.get("/system/path/migrate/state")
async def get_system_path_migrate_state():
    result = server_schema.CommonResponse
    try:
        result_info = process_setting.get_system_path_migrate_state()
        return result.success(result_info)
    except Exception as ex:
        log.error(f"setting.get_system_path_migrate_state error,{str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

@router.get("/system/default/openchatversion")
async def get_openchat_version():
    """response
        {
            "flag": True,         
            "errCode": 0,
            "errMsg": "success",
            "resData": "v1.0"
        }
    """
    result = server_schema.CommonResponse
    return result.success(const.OPENCHAT_VERSION)