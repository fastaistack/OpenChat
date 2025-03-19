from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .router import demo, plugins, model_api, settings_api, knowledge, account_api, chat_session_api, plugin_param_api, longcode_api
from .subapp import chat
from ..projectvar import Projectvar
from ..projectvar import constants as const
from ..projectvar import statuscode as status

from .router.account_api import alchemytool

import os
import json
import threading

from ..logger import Log
from datetime import datetime

import mimetypes
mimetypes.add_type("application/javascript", ".js", True)
mimetypes.add_type("text/css", ".css", True)

start_time = None

log = Log()
app = FastAPI()
gvar = Projectvar()

from fastapi.middleware.cors import CORSMiddleware
# 允许所有来源的跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(demo.router)
app.include_router(plugins.router)
app.include_router(model_api.router)
app.include_router(settings_api.router)
app.include_router(knowledge.router)
app.include_router(chat_session_api.router)
app.include_router(plugin_param_api.router)
app.include_router(longcode_api.router)
app.mount("/chat", chat.chatapi)
app.include_router(plugins.router)
app.include_router(account_api.router)
# app.include_router(openai_api.router)

#  111 与前端部署互斥
dir = os.path.join(gvar.get_home_path(), const.YUAN_WEBUI_PATH)
app.mount("/yuan-chat", StaticFiles(directory=dir), name="dist")
templates = Jinja2Templates(directory=dir)

#  111 与前端部署互斥
# dir = os.path.join(gvar.get_home_path(), const.YUAN_WEBUI_PATH)
# doc_dir = os.path.join(gvar.get_home_path(), const.YUAN_WEBUI_DOC_PATH)
# app.mount("/yuan-chat", StaticFiles(directory=dir), name="dist")
# app.mount("/yuan-doc", StaticFiles(directory=doc_dir), name="dist_doc")
# templates = Jinja2Templates(directory=dir)
# templates_doc = Jinja2Templates(directory=doc_dir)
#  111 end

#  222 与前端部署互斥
def is_login(path: str):
    # print("path = ", path)
    # print("need authorization ? : ", path=="/account/login" or path=="/account/user/login" or path=="/" or path.startswith("/yuan-chat"))
    return path=="/account/login" or path=="/account/user/login" or path=="/" or path.startswith("/yuan-chat")

#  222 与前端部署互斥
# def is_login(path: str):
#     # print("path = ", path)
#     # print("need authorization ? : ", path=="/account/login" or path=="/account/user/login" or path=="/" or path.startswith("/yuan-chat"))
#     return path=="/account/login" or path=="/account/user/login" or path=="/" or path.startswith("/yuan-chat") or path.startswith("/yuan-doc")
#  222 end



@app.middleware("http")
async def authorizaiton(req: Request, call_next):
    headers = dict(req.scope['headers'])
    if not is_login(req.url.path):
        if const.HTTP_HEADER_AUTHORIZATION not in req.headers.keys():
            return Response(json.dumps({"flag": False, "errCode": status.StatusCodeEnum.AUTHORIZATION_FIALEDS.code, "errMsg": status.StatusCodeEnum.AUTHORIZATION_FIALEDS.errmsg}))
        token = req.headers[const.HTTP_HEADER_AUTHORIZATION]
        # 解析token
        code, bearer_token = alchemytool.check_access_token(token)
        # token解析错误
        if code != 0:
            log.error(f"authorizaiton token parse error:{code} message:{bearer_token}")
            return Response(json.dumps({"flag": False, "errCode": status.StatusCodeEnum.AUTHORIZATION_FIALEDS.code, "errMsg": status.StatusCodeEnum.AUTHORIZATION_FIALEDS.errmsg}))

        db_query = alchemytool.select_user_join_role(bearer_token.user_name)
        if not db_query:
            log.error(f"authorizaiton select_user_join_role error user_name:{bearer_token.user_name}")
            return Response(json.dumps({"flag": False, "errCode": status.StatusCodeEnum.AUTHORIZATION_FIALEDS.code, "errMsg": status.StatusCodeEnum.AUTHORIZATION_FIALEDS.errmsg}))

        if not alchemytool.access_perm(db_query[2].role_id, db_query[2].role_name, req.url.path):
            log.error(f"authorizaiton access_perm error role_id:{db_query[2].role_id} role_name:{db_query[2].role_name} path:{req.url.path}")
            return Response(json.dumps({"flag": False, "errCode": status.StatusCodeEnum.AUTHORIZATION_FIALEDS.code, "errMsg": status.StatusCodeEnum.AUTHORIZATION_FIALEDS.errmsg}))

        # userid, userrole = ...
        # update header
        # user_id = "userid-" + db_query[0].user_id
        # user_role = "user-role-" + db_query[2].role_name
        headers[const.HTTP_HEADER_USER_ID] = db_query[0].user_id
        headers[const.HTTP_HEADER_USER_NAME] = db_query[0].user_name
        headers[const.HTTP_HEADER_ROLE_ID] = db_query[2].role_id
        headers[const.HTTP_HEADER_ROLE_NAME] = db_query[2].role_name

    # 默认使用中文
    headers[const.HTTP_HEADER_ACCEPT_LANGUAGE] = "cn"
    if const.HTTP_HEADER_ACCEPT_LANGUAGE in req.headers.keys():
        if str(req.headers[const.HTTP_HEADER_ACCEPT_LANGUAGE]):
            headers[const.HTTP_HEADER_ACCEPT_LANGUAGE] = str(req.headers[const.HTTP_HEADER_ACCEPT_LANGUAGE])
    req.scope['headers'] = [(k,v) for k, v in headers.items()]

    res = await call_next(req)
    return res

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )

import uvicorn
def start_thread():
    uvicorn.run(app, host="0.0.0.0", port=const.YUAN_SERVER_PORT, log_level="error")


def unexpected_exit():
    log.info("守护线程退出")
    knowledge.change_file_status()

def run():
    global start_time
    start_time = datetime.now()

    threading.Thread(target=start_thread, daemon=True).start()

    import atexit  #导入atexit  模块
    atexit.register(unexpected_exit)
