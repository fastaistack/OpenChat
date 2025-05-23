import os

from fastapi import Depends, APIRouter, Request
from sqlalchemy.orm import Session
from typing import Union, List, Dict, Optional
from pydantic import BaseModel
from ...projectvar import Projectvar
from ...projectvar.statuscode import StatusCodeEnum as status
from ...logger import Log
from ...database import models, schemas
from ..process import agent_process as dbcrud
from ...server import schemas as server_schemas
from ..depends import get_headers
from ...projectvar import constants as const
import json
from ...database.schemas import AgentBase, AgentInDB, AssistantBase, AssistantInDB
from ...projectvar.statuscode import StatusCodeEnum
from ...database.database import SessionLocal

"""初始化"""
gvar = Projectvar()
log = Log()

router = APIRouter(
    prefix="/agent",
    tags=["agent"],
    responses={404: {"description": "Not found"}},
)


# ----------------------agent------------------------------------
"""请求/响应结构体定义"""


class AgentResponse(server_schemas.CommonResponse):
    resData: Union[str, AgentBase, AgentInDB, None]


class AgentListResponse(server_schemas.CommonResponse):
    resData: Union[List[AgentInDB], str, None]


class AgentCreateRequest(AgentBase):
    pass


class AgentUpdateRequest(BaseModel):
    agent_id: str
    update_val: dict


class AgentDeleteRequest(BaseModel):
    agent_id: str


class AgentGetRequest(BaseModel):
    agent_id: str


class AgentGetListRequest(BaseModel):
    user_id: Optional[str] = None


# class AgentLoadInfoRequest(BaseModel):
#     session_id: str


# 创建智能体
@router.post("/create", response_model=AgentResponse)
async def create_agent(req: AgentCreateRequest, headers=Depends(get_headers)):
    try:
        result = AgentResponse
        user_id = headers[const.HTTP_HEADER_USER_ID]
        db_agent = dbcrud.create_agent(req, user_id=user_id)
        if db_agent:
            return result.success(AgentInDB.from_orm(db_agent))
        return result.success(None)
    except Exception as ex:
        log.error("agent: create error", f"Error details: {str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, f"创建智能体失败: {str(ex)}")


# 更新智能体
@router.post("/update", response_model=AgentResponse)
async def update_agent(req: AgentUpdateRequest, headers=Depends(get_headers)):
    try:
        result = AgentResponse
        user_id = headers[const.HTTP_HEADER_USER_ID]
        # 验证agent是否存在
        agent = dbcrud.get_agent(req.agent_id)
        if not agent:
            return result.fail(StatusCodeEnum.UNKNOWN.code, "智能体不存在")
        
        # 验证用户是否有权限修改
        if agent.user_id != user_id:
            return result.fail(StatusCodeEnum.UNKNOWN.code, "没有权限修改该智能体")
        
        db_agent = dbcrud.update_agent(req.agent_id, req.update_val, user_id=user_id)
        if db_agent:
            return result.success(AgentInDB.from_orm(db_agent))
        return result.fail(StatusCodeEnum.UNKNOWN.code, "更新智能体失败")
    except Exception as ex:
        log.error("agent: update error", f"Error details: {str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, f"更新智能体失败: {str(ex)}")


# 删除智能体
@router.post("/delete", response_model=AgentResponse)
async def delete_agent(req: AgentDeleteRequest, headers=Depends(get_headers)):
    try:
        result = AgentResponse
        user_id = headers[const.HTTP_HEADER_USER_ID]
        if dbcrud.delete_agent(req.agent_id, user_id=user_id):
            return result.success("DELETE AGENT SUCCESS")
        return result.success(None)
    except Exception as ex:
        log.error("agent: delete error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


# 获取智能体列表
@router.get("/getList", response_model=AgentListResponse)
async def get_agent_list(headers=Depends(get_headers)):
    try:
        result = AgentListResponse
        user_id = headers[const.HTTP_HEADER_USER_ID]
        agents = dbcrud.get_agent_list(user_id=user_id)
        if agents:
            return result.success([AgentInDB.from_orm(agent) for agent in agents])
        return result.success(None)
    except Exception as ex:
        log.error("agent: getlist error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


# 获取单个智能体
@router.post("/get", response_model=AgentResponse)
async def get_agent(req: AgentGetRequest):
    try:
        result = AgentResponse
        agent = dbcrud.get_agent(req.agent_id)
        if agent:
            return result.success(AgentInDB.from_orm(agent))
        return result.success(None)
    except Exception as ex:
        log.error("agent: get error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)


# # 加载智能体信息
# @router.post("/loadInfo", response_model=AgentResponse)
# async def load_agent_info(req: AgentLoadInfoRequest):
#     try:
#         result = AgentResponse
#         agent_info = dbcrud.load_agent_info(req.session_id)
#         if agent_info:
#             return result.success(agent_info)
#         return result.success(None)
#     except Exception as ex:
#         log.error("agent: load info error", str(ex))
#         return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

# -----------------------session agent-----------------------------------
"""请求/响应结构体定义"""

class AssistantRequest(BaseModel):
    session_id: str
    agent_id: str
    
class AssistantUpdateRequest(BaseModel):
    session_id: str
    update_val: dict
    
class AssistantResponse(server_schemas.CommonResponse):
    resData: Union[str, AssistantBase, AssistantInDB, None]


class AssistantListResponse(server_schemas.CommonResponse):
    resData: Union[List[AssistantInDB], str, None]

class AssistantGetRequest(BaseModel):
    session_id: str

# 设置会话智能体
@router.post("/session/addAssistant", response_model=AssistantResponse)
async def set_assistant(req: AssistantRequest):
    try:
        result = AssistantResponse
        assistant = dbcrud.set_assistant(req.agent_id, req.session_id)
        if assistant:
            return result.success(AssistantInDB.from_orm(assistant))
        return result.fail(StatusCodeEnum.UNKNOWN.code, "设置会话助手失败：智能体不存在或创建会话失败")
    except Exception as ex:
        log.error(f"agent: set assistant error - {str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, f"设置会话助手失败：{str(ex)}")


# 获取会话智能体
@router.post("/session/getAssistant", response_model=AssistantResponse)
async def get_assistant(req: AssistantGetRequest):
    try:
        result = AssistantResponse
        
        # 检查session_id是否有效
        if not req.session_id:
            log.error("get_assistant error: session_id is empty")
            return result.fail(StatusCodeEnum.PARAM_ERROR.code, "session_id is required")
            
        # 获取assistant
        assistant = dbcrud.get_assistant(req.session_id)
        if assistant:
            return result.success(AssistantInDB.from_orm(assistant))
        return result.success(None)
    except Exception as ex:
        log.error(f"get_assistant error: {str(ex)}")
        log.error(f"Error details: {ex.__class__.__name__}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, str(ex))

# 修改会话智能体
@router.post("/session/updateAssistant", response_model=AssistantResponse)
async def update_assistant(req: AssistantUpdateRequest):
    try:
        result = AssistantResponse
        assistant = dbcrud.update_assistant(req.session_id, req.update_val)
        if assistant:
            return result.success(AssistantInDB.from_orm(assistant))
        return result.fail(StatusCodeEnum.UNKNOWN.code, "更新会话助手失败：会话助手不存在或创建会话失败")
    except Exception as ex:
        log.error(f"agent: update assistant error - {str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, f"更新会话助手失败：{str(ex)}")

# 获取所有助手
@router.get("/getAssistantList", response_model=AssistantListResponse)
async def get_assistant_list():
    try:
        result = AssistantListResponse
        assistants = dbcrud.get_assistant_list()
        if assistants:
            return result.success([AssistantInDB.from_orm(assistant) for assistant in assistants])
        return result.success(None)
    except Exception as ex:
        log.error(f"agent: get assistant list error - {str(ex)}")
        return result.fail(StatusCodeEnum.UNKNOWN.code, f"获取助手列表失败：{str(ex)}") 
