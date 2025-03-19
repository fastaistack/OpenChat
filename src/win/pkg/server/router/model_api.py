from fastapi import APIRouter

from pkg.server.process import process_model
from pydantic import BaseModel
from typing import Optional, List, Union
from ...server import schemas as server_schemas
from ...projectvar.statuscode import StatusCodeEnum as status
from pkg.server.process.biz_enum import ModelStatus, ModelType
import json

router = APIRouter(
    prefix="/models",
    tags=["models"],
    responses={404: {"description": "Not found"}},
)


class ModelBaseInfo(BaseModel):
    id: int
    name: str
    status: int

class ModelUrlInfo(BaseModel):
    id:int
    url:str
    api_key:str

class ModelUrlInfoResponseInfo(server_schemas.CommonResponse):
    resData: Union[ModelUrlInfo, None]


class ModelBaseInfoResponseInfo(server_schemas.CommonResponse):
    resData: Union[ModelBaseInfo, None]


class ModelPreciseInfo(BaseModel):
    id: int
    name: str
    model_pic: str
    precise_option: list[str]
    precise_load: Optional[str] = None
    url:Optional[str] = None
    api_key:Optional[str] = None
    key:Optional[str] = None


class ModelBaseInfoResponse(server_schemas.CommonResponse):
    resData: Union[list[ModelPreciseInfo], None]


# 已下载（本地）模型列表
@router.get("/download/list", response_model=ModelBaseInfoResponse)
async def download_list():
    result = ModelBaseInfoResponse
    model_list = process_model.get_download_model_list()
    if len(model_list) <= 0:
        return result.success([])
    model_precise_list = []
    for model in model_list:
        #model_precise = ModelPreciseInfo(id=model.id, name=model.name, precise_option=[], precise_load="")
        precise_option = []
        if model.precision_list is not None and len(model.precision_list) > 0:
            precise_option = json.loads(model.precision_list)
            # print(model.api_key)
            if model.api_key:
                api_key = model.api_key
            else:
                api_key = ''
            if model.url:
                url = model.url
            else:
                url = ''
        model_precise = ModelPreciseInfo(id=model.id, name=model.name, model_pic=model.pic, precise_option=precise_option, precise_load=model.precision_selected,url=url,api_key=api_key,key=model.key)
        model_precise_list.append(model_precise)
    return result.success(model_precise_list)

# 更新模型url和api_key
@router.post("/update/urlapikey")
async def update_url_and_api_key(modelurlinfo:ModelUrlInfo):
    result = ModelUrlInfoResponseInfo
    model_info = process_model.update_url_and_api_key(modelurlinfo.id,modelurlinfo.url,modelurlinfo.api_key)
    return result.success(None)


# 已下载（本地）embedding模型列表
@router.get("/download/embedding/list")
async def download_embedding_list():
    result = server_schemas.CommonResponse
    # model_list = process_model.get_download_embedding_model_list()
    model_list = process_model.get_download_ollama_embedding_model_list()
    return result.success(model_list)


@router.get("/download/sensitive/list")
async def download_sensitive_list():
    result = server_schemas.CommonResponse
    model_list = process_model.get_download_model_list_by_type(ModelType.PLUGIN.value)
    return result.success(model_list)


# 当前加载模型
@router.get("/loaded/info")
async def get_loaded_model_info():
    result = server_schemas.CommonResponse
    model_list = process_model.get_loaded_model_info()
    if len(model_list) > 0:
        model = model_list[0]
        model_precise = ModelPreciseInfo(id=model.id, name=model.name, model_pic=model.pic,
            precise_option=json.loads(model.precision_list), precise_load=model.precision_selected)
        return result.success(model_precise)
    return result.success(None)


# 当前加载中或已加载的模型
@router.get("/current_load_status/info")
async def get_current_load_status_info():
    result = ModelBaseInfoResponseInfo
    model_list = process_model.get_model_info_by_status([ModelStatus.LOAD_SUCCESS.status, ModelStatus.LOADING.status, ModelStatus.LOAD_FAILED.status])
    if len(model_list) > 0:
        if model_list[0].status == ModelStatus.LOAD_FAILED.status:
            return result.fail(status.YUAN_MODEL_LOAD_FAILED_ERROR.code, status.YUAN_MODEL_LOAD_FAILED_ERROR.errmsg)
        model_info = ModelBaseInfo(id=model_list[0].id, name=model_list[0].name, status=model_list[0].status)
        # model_info.id = model_list[0].id
        # model_info.name=model_list[0].name
        # model_info.status=model_list[0].status
        return result.success(model_info)
    return result.success(None)


class ModelIdInfo(BaseModel):
    id: int
    precision_selected: str = None
    type: int = 1  # 1-加载；2-卸载


# 卸载/加载模型
@router.put("/load")
async def load_model(info: ModelIdInfo):
    result = server_schemas.CommonResponse
    if info.id is None or info.type is None or info.type not in [1, 2]:
        return result.fail(status.YUAN_MODEL_PARAM_INVALID_ERROR.code, status.YUAN_MODEL_PARAM_INVALID_ERROR.errmsg)
    model_list = process_model.get_download_model_list()
    exist_flag = False
    for model in model_list:
        if model.id == info.id:
            exist_flag = True
    if not exist_flag:
        return result.fail(status.YUAN_MODEL_NOT_EXIST_ERROR.code, status.YUAN_MODEL_NOT_EXIST_ERROR.errmsg)
    # for model in model_list:
    #     if model.status == ModelStatus.LOADING.status and model.id != info.id:
    #         return result.fail(status.YUAN_MODEL_LOAD_FAILED_ERROR.code, status.YUAN_MODEL_LOAD_FAILED_ERROR.errmsg)
    load_flag = process_model.load_model(info.id, info.precision_selected, info.type)
    if not load_flag:
        return result.fail(status.YUAN_MODEL_LOAD_FAILED_ERROR.code, status.YUAN_MODEL_LOAD_FAILED_ERROR.errmsg)
    return result.success({"result": True})

# 下载载模型
@router.put("/download")
async def download_model(info: ModelIdInfo):
    result = server_schemas.CommonResponse
    if info.id is None:
        return result.fail(status.YUAN_MODEL_PARAM_INVALID_ERROR.code, \
                                                  status.YUAN_MODEL_PARAM_INVALID_ERROR.errmsg)
    download_flag, exception_msg  = process_model.download_model(info.id)
    if not download_flag:
        return result.fail(status.YUAN_MODEL_DOWNLOAD_FAILED_ERROR.name, \
                                    f"{status.YUAN_MODEL_PARAM_INVALID_ERROR.errmsg}  {exception_msg}")
    else:
        return result.success(None)

class ModelQueryCond(BaseModel):
    id: Optional[List[int]] = None
    status: Optional[List[int]] = None
    name: Optional[List[str]] = None
    pageNo: Optional[int] = None
    pageSize: Optional[int] = None


# 模型列表
@router.post("/list")
async def download_list(cond: ModelQueryCond):
    result = server_schemas.CommonResponse
    models = process_model.list(cond.id, cond.status, cond.name, cond.pageNo, cond.pageSize)
    return result.success({"models" : models})

@router.post("/download_start")
async def download_start(info: ModelIdInfo):
    result = server_schemas.CommonResponse
    flag,message = process_model.download_start(info.id)
    if flag is False:
        return result.fail(status.YUAN_MODEL_DOWNLOAD_FAILED_ERROR.name, \
                           f"{status.YUAN_MODEL_DOWNLOAD_FAILED_ERROR.errmsg}  {message}")
    else:
        return result.success(None)

@router.post("/download_pause")
async def download_pause(info: ModelIdInfo):
    result = server_schemas.CommonResponse
    flag,message = process_model.download_pause(info.id)
    if flag is False:
        return result.fail(status.ERROR.name, \
                           f"{status.ERROR.errmsg}  {message}")
    else:
        return result.success(None)
    
@router.post("/download_continue")
async def download_continue(info: ModelIdInfo):
    result = server_schemas.CommonResponse
    flag,message = process_model.download_continue(info.id)
    if flag is False:
        return result.fail(status.ERROR.name, \
                           f"{status.ERROR.errmsg}  {message}")
    else:
        return result.success(None)
    
@router.post("/download_stop")
async def download_stop(info: ModelIdInfo):
    result = server_schemas.CommonResponse
    flag,message = process_model.download_stop(info.id)
    if flag is False:
        return result.fail(status.ERROR.name, \
                           f"{status.ERROR.errmsg}  {message}")
    else:
        return result.success(None)
    
@router.post("/download_progress")
async def download_progress():
    result = server_schemas.CommonResponse
    flag, data = process_model.download_progress()
    if flag is False:
        return result.fail(status.ERROR.name, \
                           status.ERROR.errmsg)
    else:
        return result.success({"progresses" : data})


@router.post("/delete")
async def delete_model(info: ModelIdInfo):
    result = server_schemas.CommonResponse
    flag,message = process_model.delete_model(info.id)
    if flag is False:
        return result.fail(status.ERROR.name, \
                           f"{status.ERROR.errmsg}  {message}")
    else:
        return result.success(None)
    
@router.post("/move_start")
async def move_start():
    result = server_schemas.CommonResponse
    flag, message = process_model.move_start()
    if flag is False:
        return result.fail(status.ERROR.name, \
                           f"{status.ERROR.errmsg}  {message}")
    else:
        return result.success(None)

@router.post("/move_progress")
async def move_progress():
    result = server_schemas.CommonResponse
    flag, data = process_model.move_progress()
    if flag is False:
        return result.fail(status.ERROR.name, \
                           status.ERROR.errmsg)
    else:
        return result.success({"progresses" : data})
    
@router.post("/get_models_volum")
async def get_models_volum():
    result = server_schemas.CommonResponse
    data = process_model.get_models_volum()
    return result.success({"size" : data})