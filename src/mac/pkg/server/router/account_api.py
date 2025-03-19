from fastapi import APIRouter, Request, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel

from ...projectvar import Projectvar
from ...projectvar import constants as const
from ..depends import get_headers
import os

from ...server.schemas import CommonResponse
from typing import Union, List
from ...projectvar.statuscode import StatusCodeEnum
from ...logger import Log
from ...database.schemas import *
from ..process.process_account import AlchemyTool
from pkg.server.process.plugin_process import plugins_init

#gvar = Projectvar()

router = APIRouter(
    prefix = "/account",
    tags=["account"],
    responses={404: {"description": "Not found"}},
)

log = Log()

class DemoParam(BaseModel):
    demo: str

class DemoOutput(DemoParam):
    user_id: str
    

class AccountResponse(CommonResponse):
    resData: Union[str, OutputListPlus, UserInDBPlus, UserInDB, RoleInDB, UserRoleInDB, PermInDB, RolePermInDB, DemoOutput, TokenBase, None]

alchemytool = AlchemyTool()

@router.post("/hello", response_model=AccountResponse)
async def account_hello(demo: DemoParam, headers=Depends(get_headers)):
    # print("account_hello", headers)
    # print("account_hello", headers[const.HTTP_HEADER_USER_ID])
    # print("account_hello", headers[const.HTTP_HEADER_USER_NAME])
    # print("account_hello", headers[const.HTTP_HEADER_ROLE_ID])
    # print("account_hello", headers[const.HTTP_HEADER_ROLE_NAME])
    user_id = headers[const.HTTP_HEADER_USER_ID]
    try:
        result = AccountResponse
        user_base = UserBase(**{"user_name":"hello", "password": "hello", "salt": "hello", "mobile": "18777778888"})
        alchemytool.test()
        return result.success(DemoOutput(**demo.__dict__, user_id=user_id))
    except Exception as ex:
        log.error("get_model_infer_setting_info error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)
    
def orm_user_plus(db_list: list):
    if len(db_list) < 3:
        return None
    user_indb = UserInDB.from_orm(db_list[0])

    user_role_id = ""
    if db_list[1]:
        user_role_id = db_list[1]

    role_id = ""
    role_name = ""
    description = ""
    parent_id = ""
    if db_list[2]:
        role_id = db_list[2].role_id
        role_name = db_list[2].role_id
        description = db_list[2].description
        parent_id = db_list[2].parent_id
    return UserInDBPlus(**user_indb.dict(), user_role_id=user_role_id, role_id=role_id, role_name=role_name, description=description, parent_id=parent_id)

@router.post("/user/login", response_model=AccountResponse)
async def account_user_login(user_name:str = "hello"):
    # print(f"\n\nInfo.account_user_login username:{user_name} password:{user_name}")
    try:
        result = AccountResponse
        db_query = alchemytool.select_user_by_name(user_name)
        if not db_query:
            log.error(f"Info.account_user_login username:{user_name} not exist")
            return result.fail(StatusCodeEnum.AUTHORIZATION_ERROR.code, StatusCodeEnum.AUTHORIZATION_ERROR.errmsg)

        # # 验证密码是否正确
        # if not alchemytool.verify_password(form_data.password, db_query.password):
        #     log.error(f"Info.account_user_login password: error")
        #     return result.fail(StatusCodeEnum.AUTHORIZATION_ERROR.code, StatusCodeEnum.AUTHORIZATION_ERROR.errmsg)

        # 创建token    
        code, access_token = alchemytool.generate_access_token(db_query.user_name)
        code, refresh_token = alchemytool.generate_refresh_token(db_query.user_name)
        
        # 初始化插件
        plugins_init(db_query.user_id)
        
        return result.success(TokenBase(access_token=access_token, refresh_token=refresh_token))
    except Exception as ex:
        log.error("account_user_login error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

@router.post("/login", response_model=AccountResponse)
async def account_login(form_data: OAuth2PasswordRequestForm = Depends()):
    # print(f"\n\nInfo.account_login username:{form_data.username} password:{form_data.password}")
    try:
        result = AccountResponse
        db_query = alchemytool.select_user_by_name(form_data.username)
        if not db_query:
            log.error(f"Info.account_login username:{form_data.username} not exist")
            return result.fail(StatusCodeEnum.AUTHORIZATION_ERROR.code, StatusCodeEnum.AUTHORIZATION_ERROR.errmsg)

        # 验证密码是否正确
        if not alchemytool.verify_password(form_data.password, db_query.password):
            log.error(f"Info.account_login password: error")
            return result.fail(StatusCodeEnum.AUTHORIZATION_ERROR.code, StatusCodeEnum.AUTHORIZATION_ERROR.errmsg)

        # 创建token    
        code, access_token = alchemytool.generate_access_token(db_query.user_name)
        code, refresh_token = alchemytool.generate_refresh_token(db_query.user_name)
        
        # 初始化插件
        plugins_init(db_query.user_id)
        
        return result.success(TokenBase(access_token=access_token, refresh_token=refresh_token))
    except Exception as ex:
        log.error("account_login error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)
    
@router.get("/token", response_model=AccountResponse)
async def account_token(headers=Depends(get_headers)):
    # print("account_token", headers)
    # print("account_token", headers[const.HTTP_HEADER_USER_ID])
    # print("account_token", headers[const.HTTP_HEADER_USER_NAME])
    # print("account_token", headers[const.HTTP_HEADER_ROLE_ID])
    # print("account_token", headers[const.HTTP_HEADER_ROLE_NAME])
    user_id = headers[const.HTTP_HEADER_USER_ID]
    user_name = headers[const.HTTP_HEADER_USER_NAME]
    try:
        result = AccountResponse
        db_query = alchemytool.select_user_join_role(user_name)
        # print("access_token", db_query)
        if db_query:
            # print(f"\n\nInfo.account_token username:{user_name} exist")
            return result.success(orm_user_plus(db_query))
        log.error(f"\n\nInfo.account_token username:{user_name} not exist")
        return result.fail(StatusCodeEnum.AUTHORIZATION_ERROR.code, StatusCodeEnum.AUTHORIZATION_ERROR.errmsg)
    except Exception as ex:
        log.error("account_token error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

    
@router.post("/user/create", response_model=AccountResponse)
async def account_register(user_base: UserBase, headers=Depends(get_headers)):
    user_id = headers[const.HTTP_HEADER_USER_ID]
    try:
        result = AccountResponse
        # print(f"\n\nInfo.account_register user_base:{user_base}")
        db_query = alchemytool.create_user(user_base, user_id)
        if db_query:
            return result.success(orm_user_plus(db_query))
        else:
            return result.success(None)
    except Exception as ex:
        log.error("account_register error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

# 获取所有用户 权限可以为空
@router.post("/user/list", response_model=AccountResponse)
async def account_list(page_param: PageParamBase, headers=Depends(get_headers)):
    # print("account_list", headers)
    # print("account_list", headers[const.HTTP_HEADER_USER_ID])
    # print("account_list", headers[const.HTTP_HEADER_USER_ROLE])
    # print(f"\n\nInfo.account_list user_base:", page_param.model_dump())
    try:
        result = AccountResponse
        total, db_query = alchemytool.select_user_outerjoin_roles(page_param)
        # user_outputs = OutputListPlus(page=page_param.page, pagesize=page_param.pagesize)
        user_outputs = OutputListPlus(**page_param.model_dump())
        for db_list in db_query:
            user_indb_plus = orm_user_plus(db_list)
            if user_indb_plus:
                user_outputs.data.append(user_indb_plus)
        # user_outputs.total = len(user_outputs.data)
        user_outputs.total = total
        return result.success(user_outputs)
    except Exception as ex:
        log.error("account_list error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)
    
@router.delete("/user/delete/{user_id}", response_model=AccountResponse)
async def account_delete(user_id: str, headers=Depends(get_headers)):
    # log.error(f"\n\nInfo.account_delete user_id:{user_id}")
    try:
        result = AccountResponse
        db_query = alchemytool.delete_user(user_id)
        if db_query:
            return result.success(UserInDB.from_orm(db_query))
        else:
            return result.success(None)
    except Exception as ex:
        log.error("account_delete error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

# 角色创建
@router.post("/role/create", response_model=AccountResponse)
async def role_create(role_base: RoleBase, headers=Depends(get_headers)):
    try:
        result = AccountResponse
        # print(f"\n\nInfo.role_create role_base:{role_base}")
        db_location = alchemytool.create_role(role_base)
        if db_location:
            return result.success(RoleInDB.from_orm(db_location))
        else:
            return result.success(None)
    except Exception as ex:
        log.error("role_create error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

# 角色列表，只列举出角色信息
@router.post("/role/list", response_model=AccountResponse)
async def role_list(page_param: PageParamBase, headers=Depends(get_headers)):
    try:
        result = AccountResponse
        # print(f"\n\nInfo.role_list role_base:")
        total, db_query = alchemytool.select_roles(page_param)
        role_outputs = OutputListPlus(**page_param.model_dump())
        for db_orm in db_query:
            role_outputs.data.append(RoleInDB.from_orm(db_orm))
        role_outputs.total = total
        return result.success(role_outputs)
    except Exception as ex:
        log.error("role_list error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)
    
# 如果用户已经绑定了角色 此时删除
# 如果权限已经绑定了角色 此时删除
@router.delete("/role/delete/{role_id}", response_model=AccountResponse)
async def role_delete(role_id: str, headers=Depends(get_headers)):
    try:
        result = AccountResponse
        # print(f"\n\nInfo.role_delete role_id:", role_id)
        db_query = alchemytool.delete_role(role_id)
        if db_query:
            return result.success(RoleInDB.from_orm(db_query))
        return result.success(None)
    except Exception as ex:
        log.error("role_delete error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

# 可以多次创建， 这样用户可以与多个角色创建链接
@router.post("/user/role/create", response_model=AccountResponse)
async def user_role_create(user_role_base: UserRoleBase, headers=Depends(get_headers)):
    try:
        result = AccountResponse
        # print(f"\n\nInfo.user_role_create user_role_base:{user_role_base}")
        db_location = alchemytool.create_user_role(user_role_base)
        if db_location:
            return result.success(UserRoleInDB.from_orm(db_location))
        return result.success(None)
    except Exception as ex:
        log.error("user_role_create error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)
    
# 可以直接删除， 这样用户与角色断开链接
@router.delete("/user/role/delete/{user_role_id}", response_model=AccountResponse)
async def user_role_delete(user_role_id: str, headers=Depends(get_headers)):
    try:
        result = AccountResponse
        # print(f"\n\nInfo.user_role_delete user_role_param:{user_role_id}")
        db_location = alchemytool.delete_user_role(user_role_id)
        if db_location:
            return result.success(UserRoleInDB.from_orm(db_location))
        return result.success(None)
    except Exception as ex:
        log.error("user_role_delete error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

# 获取用户权限 权限不为空
@router.post("/user/role/list", response_model=AccountResponse)
async def user_role_list(page_param: PageParamBase, headers=Depends(get_headers)):
    try:
        result = AccountResponse
        def orm_user_role_plus(db_list: list):
            if len(db_list) < 3:
                return None
            user_role_indb = UserRoleInDB.from_orm(db_list[0])
        
            user_name = ""
            state = 1
            if db_list[1]:
                user_name=db_list[1].user_name
                state=db_list[1].state
        
            role_name = ""
            description = ""
            if db_list[2]:
                role_name=db_list[2].role_name
                description=db_list[2].description
            return UserRoleInDBPlus(**user_role_indb.dict(), user_name=user_name, state=state, role_name=role_name, description=description)

        total, db_query = alchemytool.select_user_roles(page_param)
        # print(f"\n\nInfo.user_role_list user_role_param:", db_query)
        user_role_outputs = OutputListPlus(**page_param.model_dump())
        for db_list in db_query:
            user_role = orm_user_role_plus(db_list)
            if user_role:
                user_role_outputs.data.append(user_role.__dict__)
        user_role_outputs.total = total
        return result.success(user_role_outputs)
    except Exception as ex:
        log.error("user_role_list error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

# 创建权限
@router.post("/permission/create", response_model=AccountResponse)
async def perm_create(perm_base: PermBase, headers=Depends(get_headers)):
    try:
        result = AccountResponse
        # print(f"\n\nInfo.perm_create perm_base:{perm_base}")
        db_location =  alchemytool.create_perm(perm_base)
        if db_location:
            return result.success(PermInDB.from_orm(db_location))
        return result.success(None)
    except Exception as ex:
        log.error("perm_create error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

# curl -X 'POST' -i "http://localhost:9009/permission/update" -H 'Content-Type: application/json' -d '{"perm_name":"创建用户", "uri": "account/create"}'
@router.post("/permission/update", response_model=AccountResponse)
async def perm_update(perm_indb: PermInDB, headers=Depends(get_headers)):
    try:
        result = AccountResponse
        # print(f"\n\nInfo.perm_update perm_indb:{perm_indb}")
        db_location =  alchemytool.update_perm(perm_indb)
        if db_location:
            return result.success(PermInDB.from_orm(db_location))
        return result.success(None)
    except Exception as ex:
        log.error("perm_update error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

# 删除权限
@router.delete("/permission/delete/{perm_id}", response_model=AccountResponse)
async def perm_delete(perm_id: str, headers=Depends(get_headers)):
    try:
        result = AccountResponse
        # print(f"\n\nInfo.perm_delete perm_param:{perm_id}")
        db_query =  alchemytool.delete_perm(perm_id)
        if db_query:
            return result.success(PermInDB.from_orm(db_query))
        return result.success(None)
    except Exception as ex:
        log.error("perm_delete error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

# 查看权限列表
@router.post("/permission/list", response_model=AccountResponse)
async def perm_list(page_param: PageParamBase, headers=Depends(get_headers)):
    try:
        result = AccountResponse
        # print(f"\n\nInfo.perm_list perm_param")
        total, db_query =  alchemytool.select_perms(page_param)
        perm_output_list = OutputListPlus(**page_param.model_dump())
        for db_orm in db_query:
            perm_output_list.data.append(PermInDB.from_orm(db_orm))
        perm_output_list.total = total
        return result.success(perm_output_list)
    except Exception as ex:
        log.error("perm_list error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

# 可以多次创建， 这样角色可以与多个权限创建链接
@router.post("/role/permission/create", response_model=AccountResponse)
async def role_perm_create(role_perm_base: RolePermBase, headers=Depends(get_headers)):
    try:
        result = AccountResponse
        # print(f"\n\nInfo.role_perm_create role_perm_base:{role_perm_base}")
        db_location = alchemytool.create_role_perm(role_perm_base)
        if db_location:
            return result.success(RolePermInDB.from_orm(db_location))
        return result.success(None)
    except Exception as ex:
        log.error("role_perm_create error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)
    
# 可以直接删除， 这样角色与权限断开链接
@router.delete("/role/permission/delete/{role_perm_id}", response_model=AccountResponse)
async def role_perm_delete(role_perm_id: str, headers=Depends(get_headers)):
    # print(f"\n\nInfo.role_perm_delete role_perm_param:{role_perm_id}")
    try:
        result = AccountResponse
        db_location = alchemytool.delete_role_perm(role_perm_id)
        if db_location:
            return result.success(UserRoleInDB.from_orm(db_location))
        return result.success(None)
    except Exception as ex:
        log.error("role_perm_create error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)

@router.post("/role/permission/list", response_model=AccountResponse)
async def role_perm_list(page_param: PageParamBase, headers=Depends(get_headers)):
    def orm_role_perm_plus(db_list: list):
        if len(db_list) < 3:
            return None
        role_perm_indb = RolePermInDB.from_orm(db_list[0])
    
        role_name = ""
        description = ""
        if db_list[1]:
            role_name=db_list[1].role_name
            description=db_list[1].description
        
        perm_name = ""
        perm_uri = ""
        if db_list[2]:
            perm_name = db_list[2].perm_name
            perm_uri = db_list[2].perm_uri
            
        return RolePermInDBPlus(**role_perm_indb.dict(), role_name=role_name, description=description, perm_name=perm_name, perm_uri=perm_uri)

    try:
        result = AccountResponse
        # print(f"\n\nInfo.role_perm_list role_perm_param:")
        total, db_query = alchemytool.select_role_perms(page_param)
        role_perm_outputs = OutputListPlus(**page_param.model_dump())
        for db_list in db_query:
            role_perm_outputs.data.append(orm_role_perm_plus(db_list))
        role_perm_outputs.total = total
        return result.success(role_perm_outputs)
    except Exception as ex:
        log.error("role_perm_list error", str(ex))
        return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)
    
# @router.post("/role/permissions", response_model=AccountResponse)
# async def role_perms(page_param: PageParamBase, headers=Depends(get_headers)):
#     def orm_role_perm_dict(page_param: PageParamBase, total: int, db_query: list):
#         role_perms_outputs = OutputListPlus(**page_param.model_dump())
#         role_id = ""
#         role_indb_dict = None
#         for db_list in db_query:
#             role_indb = RoleInDB.from_orm(db_list[0])
#             if role_id != role_indb.role_id:
#                 if role_indb_dict:
#                     role_perms_outputs.data.append(role_indb_dict)
#                 role_indb_dict = RoleInDBDict(**role_indb.dict())
#                 role_id = role_indb.role_id
            
#             if db_list[2]:
#                 perm_indb = PermInDB.from_orm(db_list[2])
#                 role_indb_dict.perms.append(perm_indb)
#         if role_indb_dict:
#             role_perms_outputs.data.append(role_indb_dict)
#         role_perms_outputs.total = total
#         return role_perms_outputs
    
#     try:
#         result = AccountResponse
#         # print(f"\n\nInfo.role_perms role_perm_param:")
#         total, db_query = alchemytool.select_role_outjoin_perms(page_param)
#         return result.success(orm_role_perm_dict(page_param, total, db_query))
#     except Exception as ex:
#         log.error("role_perm_list error", str(ex))
#         return result.fail(StatusCodeEnum.UNKNOWN.code, StatusCodeEnum.UNKNOWN.errmsg)
