import datetime
import io
import json
import os
import shutil
import traceback
import uuid
from threading import Thread
from typing import Optional, Union

from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, Header, Body
from sqlalchemy import select, and_, text, desc
from sqlalchemy.orm import Session

from pkg.server.process import process_setting
from pkg.server.process import process_model
from pkg.plugins.knowledge_base.base import KBServiceFactory

from pkg.projectvar import Projectvar
from pkg.projectvar import constants as const
from pkg.server.depends import get_headers
from pkg.projectvar.statuscode import StatusCodeEnum as status
from pkg.logger import Log
from pkg.database import models, schemas
from pkg.database import crud
from pkg.server import schemas as server_schemas
from pkg.server.process.plugin_process import query_session_plugin_by_id, update_session_tool, query_plugin_by_key
from pkg.server.router.plugins import SessionUpdateReq
from pkg.server.process.biz_enum import FileAnalysisStatus

VECTOR_VERSION = "chromadb"
FILECHAT = "document_chat"
gvar = Projectvar()
log = Log()


class KnowledgeGetResponse(server_schemas.CommonResponse):
    resData: Union[schemas.KnowledgeQuery, None]


class KnowledgeFileGetResponse(server_schemas.CommonResponse):
    resData: Union[schemas.KnowledgeFileQuery, None]


class KnowledgeFileDetail(server_schemas.CommonResponse):
    resData: Union[schemas.KnowledgeFileQuery, None]


class KnowledgeFileCreateResponse(server_schemas.CommonResponse):
    resData: Union[list, None]


router = APIRouter(
    prefix="/knowledge",
    tags=["knowledge"],
    responses={404: {"description": "Not found"}},
)


# 知识库列表获取
@router.get("/list", response_model=KnowledgeGetResponse)
async def api_get_knowledge(req: Request, name: Optional[str] = "", page: int = 1, pagesize: int = 10,
                            db: Session = Depends(crud.get_db)):
    user = get_username_info(req.headers)
    rr = db_query_knowledge(user,name,page,pagesize,db)
    return rr


# 知识库创建
def get_username_info(headers):
    user_name = ""
    for header in headers.raw:
        if header[0] == "user-name":
            user_name = header[1]
            break
    return user_name


@router.post("/create", response_model=KnowledgeFileCreateResponse)
async def api_create_knowledge(req: Request, id: Optional[str] = Form(""), name: str = Form(...),
                               description: Optional[str] = Form(""), knowledge_setting: Optional[str] = Form(""),
                               files: list[UploadFile] = File(...), db: Session = Depends(crud.get_db)):
    # knowledge_params = json.loads(knowledge_setting)
    user = get_username_info(req.headers)
    if knowledge_setting == "" or (
            len(json.loads(knowledge_setting)) == 1 and json.loads(knowledge_setting)["embed_model"] != ""):
        knowledgequeried = db.query(models.Setting).filter(and_(models.Setting.config_key == VECTOR_VERSION)).all()
        # 查询不到，获取默认配置
        if len(knowledgequeried) == 0:
            global_path = process_setting.get_system_default_path().config_value
            file_local_path = os.path.join(global_path, VECTOR_VERSION)
            chromadb = {
                "global_param": {"chromadb_persist_path": file_local_path, "embed_model": ""},
                "storage_param": {"chunk_size": 1000, "overlap_size": 120},
                "query_param": {"search_type": "similarity", "k": 4, "score_threshold": 0.5, "fetch_k": 20,
                                "lambda_mult": 0.5, "distance_strategy": "l2", "prompt_template": ""}}
        else:
            chromadb = json.loads(knowledgequeried[0].config_value)
        if len(json.loads(knowledge_setting)) == 1:
            chromadb["global_param"]["embed_model"] = json.loads(knowledge_setting)["embed_model"]
        knowledge_setting = json.dumps(chromadb)
    rr = db_create_knowledge(
        models.Knowledge(id=id, name=name, description=description, user=user, config=knowledge_setting), files, db)
    return rr


# @router.post("/create", response_model=server_schemas.CommonResponse)
# async def api_create_knowledge(req:Request,id:Optional[str]=Form(""),name: str =Form(...),description: Optional[str]=Form("") ,files:list[UploadFile]=File(...), db: Session = Depends(crud.get_db)):
#     user = get_username_info(req.headers)
#     rr = db_create_knowledge(models.Knowledge(id=id,name=name,description =description),files,db)
#     return rr
# 知识库删除
@router.delete("/delete/{id}", response_model=server_schemas.CommonResponse)
async def api_delete_knowledge(req: Request, id: str, db: Session = Depends(crud.get_db)):
    user = get_username_info(req.headers)
    rr = db_delete_knowledge(id, db)
    return rr


# 知识库更新描述
@router.post("/update/{id}", response_model=server_schemas.CommonResponse)
async def api_update_knowledge_description(req: Request, id: str, update: schemas.KnowledgeUpdateBase,
                                           db: Session = Depends(crud.get_db)):
    user = get_username_info(req.headers)
    if len(update.user) == 0:
        update.user = [user]
    else:
        for us in update.user:
            if us == user:
                continue
            from pkg.server.router.account_api import alchemytool
            if alchemytool.select_user_by_name(us) == None:
                return server_schemas.CommonResponse(flag=False, errCode=status.AUTHORIZATION_ERROR.code,
                                                     errMsg=f"{us}{status.AUTHORIZATION_ERROR.errmsg}")
    rr = db_update_knowledge_description(id, update, db)
    # rr = db_update_knowledge_description(models.Knowledge(id=id, description=update.description), db)
    return rr


# 知识库更新文件
@router.post("/update/{id}/files", response_model=KnowledgeFileCreateResponse)
async def api_update_knowledge(req: Request, id: str, description: Optional[str] = "knowledge",
                               files: list[UploadFile] = File(...), db: Session = Depends(crud.get_db)):
    user = get_username_info(req.headers)
    # rr = db_update_knowledge(models.Knowledge(id=id, description=description), files, db)
    rr = db_upload_file_only(models.Knowledge(id=id, description=description), files, db)  
    return rr

# 仅仅上传文件到数据库中给保存
def db_upload_file_only(knowledge, files, db):
    result = KnowledgeFileCreateResponse
    result.flag = True
    knowledgequeried = db.query(models.Knowledge).filter(models.Knowledge.id == knowledge.id).all()
    
    file_id_list = []
    for file in files:
        knowledgeFileQuery = db.query(models.KnowledgeFile).filter(
                and_(models.KnowledgeFile.knowledgeid == knowledge.id,
                     models.KnowledgeFile.name == file.filename)).all()
        if len(knowledgeFileQuery) == 0:
            file_id = uuid.uuid1().hex
            # insert data
            newknowledgefile = models.KnowledgeFile(id=file_id, 
                                                    name=file.filename, 
                                                    knowledgeid=knowledge.id,
                                                    size=format_file_size(file.size), 
                                                    bytetotal=file.size,
                                                    createtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                    status = FileAnalysisStatus.PENDING.value,
                                                    process = 0.0)
            db.add(newknowledgefile)
            db.commit()
            db.refresh(newknowledgefile)
        else:
            file_id = knowledgeFileQuery[0].id
            knowledge_file = {}
            # knowledge_file["name"] = file.filename
            knowledge_file["size"] = format_file_size(file.size)
            knowledge_file["bytetotal"] = file.size
            knowledge_file["createtime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # update data
            db.query(models.KnowledgeFile).filter(models.KnowledgeFile.id == knowledgeFileQuery[0].id).update(
                knowledge_file)
            db.commit()
        save_file_local(f'{knowledgequeried[0].name}_{knowledgequeried[0].id}', file)
        file_id_list.append(file_id)
    result.errCode = status.OK.code
    result.errMsg = status.OK.errmsg
    result.resData = file_id_list
    return result

# 知识库文件获取
@router.get("/{id}/files", response_model=KnowledgeFileGetResponse)
async def api_get_knowledge_files(req: Request, id: str, page: int = 0, pagesize: int = 10,
                                  db: Session = Depends(crud.get_db)):
    user = get_username_info(req.headers)
    rr = db_get_knowledge_files(id, page, pagesize, db)
    return rr


# 知识库中文件删除
@router.delete("/file/{id}/delete", response_model=server_schemas.CommonResponse)
async def api_delete_knowledge_files(req: Request, id: str, db: Session = Depends(crud.get_db)):
    user = get_username_info(req.headers)
    rr = db_delete_knowledge_files(id, db)
    return rr

from concurrent.futures import ThreadPoolExecutor
import threading
# from multiprocessing.dummy import Pool as ThreadPool
# task_pool = ThreadPool(processes = 4)
lock =  threading.Lock()
executor =  ThreadPoolExecutor(max_workers=1)
tasks = []
# 启用多线程分析
def file_start_analyzing(file_id, db):
    try:
        file = db.query(models.KnowledgeFile).filter(models.KnowledgeFile.id == file_id).first()
        knowledge_id = file.knowledgeid
        file_name = file.name
        knowledgequeried = db.query(models.Knowledge).filter(models.Knowledge.id == knowledge_id).all()
        # task_pool.apply_async(adapter_vector_file_add, (knowledgequeried[0], VECTOR_VERSION, file_name,file_id,db))
        task = executor.submit(adapter_vector_file_add,knowledgequeried[0], VECTOR_VERSION,file_name,file_id,db)
        tasks.append({"knowledge_id":knowledge_id, "file_id":file_id,"task":task})
        return
    except Exception as e:
        log.error(('{0}'.format(e)))
        
def file_stop_analysis():
    while tasks:
        task = tasks.pop(0)
        result = task['task'].cancel()
        log.info(f"{task['file_id']}分析线程关闭, 结果为：{result}")
    executor.shutdown(wait=False)
    log.info("文件线程分析关闭")

# 应用打开前或退出后未解析完成的文件需将其状态置为解析失败
def change_file_status():
    from pkg.database import models
    from pkg.database.database import SessionLocal

    try:
        db = SessionLocal()
        files = db.query(models.KnowledgeFile).filter(models.KnowledgeFile.status == 1).all()
        for file in files:
            log.info(f"正在解析文件为{file.name}")
            file.status = -1
            db.add(file)
            db.commit()
            db.refresh(file)
        log.info("文件状态更新完成")
    except Exception as e:
        log.error(('{0}'.format(e)))
    

@router.post("/file/{id}/analysis")
async def api_file_analysis(req: Request, id: str, db: Session = Depends(crud.get_db)):
    try:
        file = db.query(models.KnowledgeFile).filter(models.KnowledgeFile.id == id).first()
        file.status = FileAnalysisStatus.PROCESSING.value
        db.add(file)
        db.commit()
        db.refresh(file)
    except Exception as e:
        log.error(('{0}'.format(e)))
    file_start_analyzing(id,db)
    return 

# 查看知识库文件详情
# 创建一个 Base 模型，用于表示其他的 JSON 信息

@router.post("/file/{id}/detail")
async def api_detail_knowledge_file(req: Request, id: str, db: Session = Depends(crud.get_db)):
    user = get_username_info(req.headers)
    # 模拟其他的 JSON 信息
    # json_info = schemas.AdditionalInfo(message="Image loaded successfully", status="OK")
    knowledgequeried = db.query(models.KnowledgeFile).filter(models.KnowledgeFile.id == id).join(models.Knowledge,
                                                                                                 models.KnowledgeFile.knowledgeid == models.Knowledge.id).all()
    if len(knowledgequeried) == 0:

        return StreamingResponse(io.BytesIO("find file error"))
        # with open(os.path.join(file_local_path, knowledgequeried[0].name), 'rb') as f:
    else:
        global_path = process_setting.get_system_default_path().config_value
        file_local_path = os.path.join(global_path, "knowledge",
                                       f'{knowledgequeried[0].knowledge.name}_{knowledgequeried[0].knowledge.id}')
        if not os.path.exists(file_local_path):
            os.makedirs(file_local_path)
        # 读取face.png
        #
        file_data = open(os.path.join(file_local_path, knowledgequeried[0].name), 'rb').read()
        # 使用 StreamingResponse 返回字节流和其他的 JSON 信息
        return StreamingResponse(io.BytesIO(file_data),
                                 headers={"Content-Type": 'application/octet-stream',
                                          'Content-Disposition': f'attachment; filename={knowledgequeried[0].name.encode("utf-8")}'})


class KnowledgeSessionResponse(server_schemas.CommonResponse):
    resData: Union[dict, None]


# 向量库全局配置获取
@router.get("/config/{name}", response_model=KnowledgeSessionResponse)
async def api_get_knowledge_global_config(req: Request, name: str, db: Session = Depends(crud.get_db)):
    user = get_username_info(req.headers)
    rr = db_get_knowledge_global_config(name, db)
    return rr


# 向量库全局配置更新
@router.post("/config/{name}", response_model=KnowledgeSessionResponse)
async def api_update_knowledge_global_config(req: Request, name: str, update: schemas.KnowledgeGlobalConfigUpdateBase,
                                             db: Session = Depends(crud.get_db)):
    user = get_username_info(req.headers)
    rr = db_update_knowledge_global_config(name, update, user, db)
    return rr


@router.get("/{id}/session", response_model=KnowledgeSessionResponse)
async def api_get_knowledge_session(req: Request, id: str, db: Session = Depends(crud.get_db)):
    user = get_username_info(req.headers)
    rr = db_get_knowledge_config(id, db)
    return rr

# 文档对话配置获取
@router.get("/filechat/config", response_model=KnowledgeSessionResponse)
async def api_get_knowledge_filechat_config(req:Request,sessionid: Optional[str]= "",db: Session = Depends(crud.get_db)):
    user = get_username_info(req.headers)
    rr = db_get_knowledge_filechat_config(sessionid,db)
    return rr
# 文档对话配置获取
def db_get_knowledge_filechat_config(sessionid, db):
    result = KnowledgeSessionResponse
    result.flag = True
    try:
        if sessionid != "":
            # 获取文档对话的session配置
            knowledgelist = db.query(models.Knowledge).filter(
                and_(models.Knowledge.id == sessionid, models.Knowledge.type == "0")).order_by(
                desc(models.Knowledge.createtime)).all()
            if len(knowledgelist) != 0:
                config = json.loads(knowledgelist[0].config)
                result.resData = config[FILECHAT]
            else:
                # 获取文档对话的全局配置
                knowledgequeried = db.query(models.Setting).filter(
                    and_(models.Setting.config_key == FILECHAT)).all()
                result.resData = json.loads(knowledgequeried[0].config_value)
        else:
            # 获取文档对话的全局配置
            knowledgequeried = db.query(models.Setting).filter(
                and_(models.Setting.config_key == FILECHAT)).all()
            result.resData = json.loads(knowledgequeried[0].config_value)
        result.errCode = status.OK.code
        result.errMsg = status.OK.errmsg
    except Exception as e:
        log.error(('[knowledge management - db_get_knowledge_global_config] database knowledge query global config error:{0}'.format(e)))
        print(traceback.format_exc())
        result.flag = False
        result.errCode = status.ERROR.code
        result.errMsg = status.ERROR.errmsg
        result.resData = {}
    return result

# 文档对话配置更新
@router.post("/filechat/config", response_model=KnowledgeSessionResponse)
async def api_update_knowledge_filechat_config(req:Request,update: schemas.KnowledgeFileChatConfig,db: Session = Depends(crud.get_db)):
    user = get_username_info(req.headers)
    rr = db_update_knowledge_filechat_config(update,user,db)
    return rr

# 文档对话配置更新
def db_update_knowledge_filechat_config(update, user, db):
    result = KnowledgeSessionResponse
    result.flag = True
    try:
        if update.sessionid == "":
            # 更新文档对话的全局配置
            chatconfig = {"config_key": FILECHAT}
            tmp = {"embed_model": update.embed_model, "embed_param": update.embed_param}
            chatconfig["config_value"] = json.dumps(tmp)
            db.query(models.Setting).filter(models.Setting.config_key == FILECHAT).update(chatconfig)
            db.commit()

        else:
            knowledge_queried = db.query(models.Knowledge).filter(models.Knowledge.id == update.sessionid).all()
            if len(knowledge_queried) != 0:
                knowledge_config = json.loads(knowledge_queried[0].config)
                # 更新文档对话的session配置
                knowledgeUpdate = {}
                tmp = {"embed_model": update.embed_model, "embed_param": update.embed_param}
                knowledge_config[FILECHAT] = tmp
                knowledgeUpdate["config"] = json.dumps(knowledge_config)
                db.query(models.Knowledge).filter(models.Knowledge.id == update.sessionid).update(knowledgeUpdate)
                db.commit()
            else:
                # 对话框，文件新建一个临时知识库
                kid = update.sessionid
                name = f'tmp_{update.sessionid}'
                type = "0"
                knowledgequeried = db.query(models.Setting).filter(
                    and_(models.Setting.config_key == VECTOR_VERSION)).all()
                # 查询不到，获取默认配置
                if len(knowledgequeried) == 0:
                    global_path = process_setting.get_system_default_path().config_value
                    file_local_path = os.path.join(global_path, VECTOR_VERSION)
                    global_param = {"chromadb_persist_path": file_local_path, "embed_model": ""}
                else:
                    global_param = json.loads(knowledgequeried[0].config_value)["global_param"]
                document_config = db.query(models.Setting).filter(and_(models.Setting.config_key == FILECHAT)).all()
                full_config = json.loads(knowledgequeried[0].config_value)
                full_config[FILECHAT] = json.loads(document_config[0].config_value)
                full_config = json.dumps(full_config)
                # insert data
                newknowledge = models.Knowledge(id=kid, name=name, type=type,
                                                description="", user=user,
                                                config=(full_config),
                                                createtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                db.add(newknowledge)
                db.commit()
                db.refresh(newknowledge)

        result.errCode = status.OK.code
        result.errMsg = status.OK.errmsg
        result.resData = {}
    except Exception as e:
        log.error((
                      '[knowledge management - db_update_knowledge_filechat_config] database knowledge query global config error:{0}'.format(
                          e)))
        result.flag = False
        print(traceback.format_exc())
        result.errCode = status.ERROR.code
        result.errMsg = status.ERROR.errmsg
        result.resData = {}
    return result

# 向量库全局配置获取
def db_get_knowledge_global_config(name, db):
    result = KnowledgeSessionResponse
    result.flag = True
    try:
        knowledgequeried = db.query(models.Setting).filter(and_(models.Setting.config_key == name)).all()
        # 查询不到，获取默认配置
        if len(knowledgequeried) == 0:
            result.errCode = status.OK.code
            result.errMsg = status.OK.errmsg
            if VECTOR_VERSION == "chromadb":
                global_path = process_setting.get_system_default_path().config_value
                file_local_path = os.path.join(global_path, VECTOR_VERSION)
                result.resData = {"chromadb_persist_path": file_local_path, "embed_model": ""}
            else:
                result.resData = {"milvus_db_host": "127.0.0.1", "milvus_db_port": "19530", "milvus_db_user": "",
                                  "milvus_db_password": ""}
            return result
        else:
            config = json.loads(knowledgequeried[0].config_value)["global_param"]
            # query_config = config["query_param"]
            result.resData = config
        result.errCode = status.OK.code
        result.errMsg = status.OK.errmsg
    except Exception as e:
        log.error(('[knowledge management - db_get_knowledge_global_config] database knowledge query global config error:{0}'.format(e)))
        print(traceback.format_exc())
        result.flag = False
        result.errCode = status.ERROR.code
        result.errMsg = status.ERROR.errmsg
        result.resData = {}
    return result

# 向量库全局配置获取
def db_update_knowledge_global_config(name, update, user, db):
    result = KnowledgeSessionResponse
    result.flag = True
    try:
        knowledgequeried = db.query(models.Setting).filter(and_(models.Setting.config_key == name)).all()
        # 查询不到，直接新增配置
        if len(knowledgequeried) == 0:
            # insert data
            newknowledge = models.Setting(id=10000, user_id=user, config_key=name,
                                          config_value=(update.model_dump_json()))
            db.add(newknowledge)
            db.commit()
            db.refresh(newknowledge)
        else:
            # 更新现有配置
            knowledgeUpdate = {}
            knowledgeUpdate["config_key"] = name
            oldconfig = json.loads(knowledgequeried[0].config_value)
            oldconfig["global_param"] = json.loads(update.model_dump_json())
            knowledgeUpdate["config_value"] = json.dumps(oldconfig)
            # knowledgeUpdate["config_value"] = (oldconfig)
            db.query(models.Setting).filter(models.Setting.config_key == name).update(knowledgeUpdate)
            db.commit()
        result.errCode = status.OK.code
        result.errMsg = status.OK.errmsg
        result.resData = {}
    except Exception as e:
        log.error(('[knowledge management - db_update_knowledge_global_config] database knowledge query global config error:{0}'.format(e)))
        print(traceback.format_exc())
        result.flag = False
        result.errCode = status.ERROR.code
        result.errMsg = status.ERROR.errmsg
        result.resData = {}
    return result


# 根据知识库id查询检索配置
def db_get_knowledge_config(id, db):
    result = KnowledgeSessionResponse
    result.flag = True
    try:
        knowledgequeried = db.query(models.Knowledge).filter(models.Knowledge.id == id).all()
        if len(knowledgequeried) == 0:
            result.errCode = status.OK.code
            result.errMsg = status.OK.errmsg
            result.resData = {}
            return result
        else:
            config = json.loads(knowledgequeried[0].config)
            query_config = config["query_param"]
            result.resData = query_config
        result.errCode = status.OK.code
        result.errMsg = status.OK.errmsg
    except Exception as e:
        log.error(('[knowledge management - db_get_knowledge_config] database knowledge query config error:{0}'.format(e)))
        print(traceback.format_exc())
        result.flag = False
        result.errCode = status.ERROR.code
        result.errMsg = status.ERROR.errmsg
        result.resData = {}
    return result


# 查看知识库文件详情
def db_detail_knowledge_files(id, db):
    result = server_schemas.CommonResponse
    result.flag = True
    try:
        knowledgequeried = db.query(models.KnowledgeFile).filter(models.KnowledgeFile.id == id).join(models.Knowledge,
                                                                                                     models.KnowledgeFile.knowledgeid == models.Knowledge.id).all()
        if len(knowledgequeried) == 0:
            result.errCode = status.OK.code
            result.errMsg = status.OK.errmsg
            result.resData = {}
            return result
        else:
            global_path = process_setting.get_system_default_path().config_value
            file_local_path = os.path.join(global_path, "knowledge",
                                           f'{knowledgequeried[0].knowledge.name}_{knowledgequeried[0].knowledge.id}')
            if not os.path.exists(file_local_path):
                os.makedirs(file_local_path)
            with open(os.path.join(file_local_path, knowledgequeried[0].name), 'rb') as f:
                result.resData = {"data": f.readlines()}

        result.errCode = status.OK.code
        result.errMsg = status.OK.errmsg
    except Exception as e:
        log.error(('[knowledge management - db_detail_knowledge_files] database knowledge create error:{0}'.format(e)))
        print(traceback.format_exc())
        result.flag = False
        result.errCode = status.ERROR.code
        result.errMsg = status.ERROR.errmsg
        result.resData = {}
    return result


# 知识库表格填充以及知识库关联的文件列表
# 字节自适应转化单位KB、MB、GB
def format_file_size(value):
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = 1024.0
    for i in range(len(units)):
        if (value / size) < 1:
            return "%.2f%s" % (value, units[i])
        value = value / size


def save_file_local(knowledge_name, file_upload):
    global_path = process_setting.get_system_default_path().config_value
    file_local_path = os.path.join(global_path, "knowledge", knowledge_name)
    if not os.path.exists(file_local_path):
        os.makedirs(file_local_path)
    with open(os.path.join(file_local_path, file_upload.filename), 'wb') as f:
        f.write(file_upload.file.read())
    # word 转pdf
    # if file_upload.name.index(".doc") >= 0 or file_upload.name.index(".docx") >= 0:
    #     convert_doc_to_pdf(file.)


def db_update_knowledge_description(id, knowledge, db):
    result = server_schemas.CommonResponse
    result.flag = True
    try:
        knowledgeUpdate = {}
        knowledgequeried = db.query(models.Knowledge).filter(models.Knowledge.id == id).all()
        if len(knowledgequeried) == 0:
            result.errCode = status.OK.code
            result.errMsg = status.OK.errmsg
            result.resData = {}
            return result
        if knowledge.description != "":
            # 更新知识库描述
            knowledgeUpdate["description"] = knowledge.description
        old_config = json.loads(knowledgequeried[0].config)
        old_config["query_param"] = json.loads(knowledge.knowledge_setting)
        knowledgeUpdate["config"] = json.dumps(old_config)
        knowledgeUpdate["user"] = ",".join(knowledge.user)
        knowledgeUpdate["createtime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.query(models.Knowledge).filter(models.Knowledge.id == id).update(knowledgeUpdate)
        db.commit()
        result.errCode = status.OK.code
        result.errMsg = status.OK.errmsg
        result.resData = {}
    except Exception as e:
        log.error(('[knowledge management - db_update_knowledge_description] database knowledge create error:{0}'.format(e)))
        print(traceback.format_exc())
        result.flag = False
        result.errCode = status.ERROR.code
        result.errMsg = status.ERROR.errmsg
        result.resData = {}
    return result


def db_update_knowledge(knowledge, files, db):
    start = datetime.datetime.now()
    result = KnowledgeFileCreateResponse
    result.flag = True
    try:
        knowledgeUpdate = {}
        knowledgequeried = db.query(models.Knowledge).filter(models.Knowledge.id == knowledge.id).all()
        if len(knowledgequeried) == 0:
            result.errCode = status.OK.code
            result.errMsg = status.OK.errmsg
            result.resData = []
            return result
        if knowledge.description != "":
            # 更新知识库描述
            knowledgeUpdate["description"] = knowledge.description
        knowledgeUpdate["createtime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.query(models.Knowledge).filter(models.Knowledge.id == knowledge.id).update(knowledgeUpdate)
        db.commit()
        file_id_list = []
        # 操作知识库文件
        for file in files:
            knowledgeFileQuery = db.query(models.KnowledgeFile).filter(
                and_(models.KnowledgeFile.knowledgeid == knowledge.id,
                     models.KnowledgeFile.name == file.filename)).all()
            if len(knowledgeFileQuery) == 0:
                file_id = uuid.uuid1().hex
                # insert data
                newknowledgefile = models.KnowledgeFile(id=file_id, name=file.filename, knowledgeid=knowledge.id,
                                                        size=format_file_size(file.size), bytetotal=file.size,
                                                        createtime=datetime.datetime.now().strftime(
                                                            "%Y-%m-%d %H:%M:%S"))
                db.add(newknowledgefile)
                db.commit()
                db.refresh(newknowledgefile)
            else:
                file_id = knowledgeFileQuery[0].id
                knowledge_file = {}
                # knowledge_file["name"] = file.filename
                knowledge_file["size"] = format_file_size(file.size)
                knowledge_file["bytetotal"] = file.size
                knowledge_file["createtime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # update data
                db.query(models.KnowledgeFile).filter(models.KnowledgeFile.id == knowledgeFileQuery[0].id).update(
                    knowledge_file)
                db.commit()
            file_id_list.append(file_id)
            # 文件保存
            save_file_local(f'{knowledgequeried[0].name}_{knowledgequeried[0].id}', file)
            start_vector = datetime.datetime.now()
            adapter_vector_file_add(knowledgequeried[0], VECTOR_VERSION, file.filename, file_id)
            log.info(
                ('[knowledge management - db_update_knowledge] process vector addfile time:{0}'.format(
                    (datetime.datetime.now() - start_vector).total_seconds())))

            # 调用知识库向量创建接口 TODO
        result.errCode = status.OK.code
        result.errMsg = status.OK.errmsg
        result.resData = file_id_list
    except Exception as e:
        log.error(('[knowledge management - db_update_knowledge] database knowledge update error:{0}'.format(e)))
        print(traceback.format_exc())
        result.flag = False
        result.errCode = status.ERROR.code
        result.errMsg = e
        result.resData = []

    log.info(('[knowledge management - db_update_knowledge] total knowledge update time:{0}'.format(
        (datetime.datetime.now() - start).total_seconds())))
    return result


def db_create_knowledge(knowledge, files, db):
    start = datetime.datetime.now()
    result = KnowledgeFileCreateResponse
    result.flag = True
    try:
        # 对话框，文件新建一个临时知识库
        if knowledge.id != "":
            kid = knowledge.id
            knowledge.name = f'tmp_{knowledge.id}'
            type = "0"
        else:
            # 根据知识库名称判断是否存在
            knowledgequerybyname = db.query(models.Knowledge).filter(models.Knowledge.name == knowledge.name).all()
            if len(knowledgequerybyname) > 0:
                result.flag = False
                result.errCode = status.KNOWLEDGE_EXIST_ERROR.code
                result.errMsg = status.KNOWLEDGE_EXIST_ERROR.errmsg
                result.resData = []
                return result
            kid = uuid.uuid1().hex
            type = "1"
        knowledgequery = db.query(models.Knowledge).filter(models.Knowledge.id == kid).all()
        # 刷新一下参数配置信息
        if len(knowledgequery) !=0 :
            cf = json.loads(knowledgequery[0].config)
            cf['global_param']['embed_model'] = json.loads(knowledge.config)['global_param']['embed_model']
            knowledgequery[0].config = json.dumps(cf)
            db.add(knowledgequery[0])
            db.commit()
            db.refresh(knowledgequery[0])
        if len(knowledgequery) == 0:
            full_config = json.loads(knowledge.config)
            knowledgequeried = db.query(models.Setting).filter(
                and_(models.Setting.config_key == VECTOR_VERSION)).all()
            # 查询不到，获取默认配置
            if len(knowledgequeried) == 0:
                global_path = process_setting.get_system_default_path().config_value
                file_local_path = os.path.join(global_path, VECTOR_VERSION)
                global_param = {"chromadb_persist_path": file_local_path, "embed_model": ""}
            else:
                global_param = json.loads(knowledgequeried[0].config_value)["global_param"]
            if ("global_param" in full_config ) and ("storage_param" in full_config) and ("query_param" in full_config):
                if full_config["global_param"]["embed_model"] == "":
                    full_config["global_param"] = global_param
            else:
                if not ("global_param" in full_config) or full_config["global_param"]["embed_model"] == "":
                    full_config["global_param"] = global_param
                if not ("storage_param" in full_config):
                    full_config["storage_param"] = json.loads(knowledgequeried[0].config_value)["storage_param"]
                if not ("query_param" in full_config):
                    full_config["query_param"] = json.loads(knowledgequeried[0].config_value)["query_param"]
            if not (FILECHAT  in full_config):
                document_config =  db.query(models.Setting).filter(and_(models.Setting.config_key == FILECHAT)).all()
                full_config[FILECHAT] = json.loads(document_config[0].config_value)
            full_config = json.dumps(full_config)
            # insert data
            newknowledge = models.Knowledge(id=kid, 
                                            name=knowledge.name, 
                                            type=type, 
                                            description=knowledge.description,
                                            user=knowledge.user, 
                                            config=(full_config),
                                            createtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            db.add(newknowledge)
            db.commit()
            db.refresh(newknowledge)
            start_vector = datetime.datetime.now()
            adapter_vector_create(newknowledge, VECTOR_VERSION)
            log.info(
                ('[knowledge management - db_create_knowledge] process vector  create time:{0}'.format(
                    (datetime.datetime.now() - start_vector).total_seconds())))
        else:
            # 临时知识库
            newknowledge = knowledgequery[0]
        # 操作知识库文件
        file_id_list = []
        for file in files:
            if file.filename == "" and file.size == 0:
                continue
            knowledgeFileQuery = db.query(models.KnowledgeFile).filter(
                and_(models.KnowledgeFile.knowledgeid == kid, models.KnowledgeFile.name == file.filename)).all()
            if len(knowledgeFileQuery) == 0:
                file_id = uuid.uuid1().hex
                # insert data
                newknowledgefile = models.KnowledgeFile(id=file_id, 
                                                        name=file.filename, 
                                                        knowledgeid=kid,
                                                        size=format_file_size(file.size), 
                                                        bytetotal=file.size,
                                                        createtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                        status = FileAnalysisStatus.PENDING.value,
                                                        process = 0.0)
                db.add(newknowledgefile)
                db.commit()
                db.refresh(newknowledgefile)
            else:
                file_id = knowledgeFileQuery[0].id
                knowledge_file = {}
                # knowledge_file["name"] = file.filename
                knowledge_file["size"] = format_file_size(file.size)
                knowledge_file["bytetotal"] = file.size
                knowledge_file["createtime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # update data
                db.query(models.KnowledgeFile).filter(models.KnowledgeFile.id == knowledgeFileQuery[0].id).update(
                    knowledge_file)
                db.commit()
            file_id_list.append(file_id)
            # 文件保存
            save_file_local(f'{knowledge.name}_{kid}', file)
            start_vector = datetime.datetime.now()
            if type == '0': # 临时向量库，需要执行文件解析写入向量库
                adapter_vector_file_add(newknowledge, VECTOR_VERSION, file.filename, file_id, db)
            log.info(('[knowledge management - db_create_knowledge] process vector addfile time:{0}'.format(
                (datetime.datetime.now() - start_vector).total_seconds())))
            # cursor.execute(insert_file_sql)
            # 调用知识库向量创建接口

        result.errCode = status.OK.code
        result.errMsg = status.OK.errmsg
        result.resData = file_id_list
    except Exception as e:
        log.error(('[knowledge management - db_create_knowledge] database knowledge create error:{0}'.format(e)))
        print(traceback.format_exc())
        result.flag = False
        result.errCode = status.ERROR.code
        result.errMsg = e
        result.resData = []
    log.info(('[knowledge management - db_create_knowledge] total knowledge create time:{0}'.format(
        (datetime.datetime.now() - start).total_seconds())))
    return result


# 知识库列表获取
def db_query_knowledge(user,name, page, pagesize, db):
    result = KnowledgeGetResponse
    result.flag = True
    try:
        # 创建游标
        # knowledgelist = db.query(models.Knowledge).filter(
        #     and_(models.Knowledge.name.like("%" + name + "%") if name != '' else text(""),models.Knowledge.type=="1"),models.Knowledge.user.like("%" + user + "%")).order_by(desc(models.Knowledge.createtime)
        #     ).limit(pagesize).offset(pagesize * (page - 1)).all()
        # Knowledgecount = db.query(models.Knowledge).filter(
        #     and_(models.Knowledge.name.like("%" + name + "%") if name != '' else text(""),models.Knowledge.type=="1"),models.Knowledge.user.like("%" + user + "%")).order_by(
        #     desc(models.Knowledge.createtime)).count()
        knowledgelistall = db.query(models.Knowledge).filter(
            and_(models.Knowledge.name.like("%" + name + "%") if name != '' else text(""),
                 models.Knowledge.type == "1")).order_by(desc(models.Knowledge.createtime)).all()
        knowledgefilter = []
        for know in knowledgelistall:
            us = know.user.split(",")
            if user in us:
                knowledgefilter.append(know)
        Knowledgecount = len(knowledgefilter)
        # 根据前端页码数进行过滤获取
        knowledgelist = []
        if Knowledgecount < pagesize * page:  # 列表末尾
            for i in range(pagesize * (page - 1), Knowledgecount):
                knowledgelist.append(knowledgefilter[i])
        else:
            for i in range(pagesize * (page - 1), pagesize * page):
                knowledgelist.append(knowledgefilter[i])
        knowledge_return = []
        for tmp in knowledgelist:
            file_list = db.query(models.KnowledgeFile).filter(
                and_(models.KnowledgeFile.knowledgeid == tmp.id)).order_by(
                models.KnowledgeFile.createtime).all()
            count = len(file_list)
            volume = 0
            for file in file_list:
                volume = volume + file.bytetotal
            volume_str = f'{format_file_size(volume)}'
            knowledge_return.append(schemas.KnowledgeJoinFile(id=tmp.id, name=tmp.name, description=tmp.description,
                                                              createtime=tmp.createtime, user=tmp.user.split(","),
                                                              config=json.loads(tmp.config), type=tmp.type, count=count,
                                                              volume=volume_str))

        result.errCode = status.OK.code
        result.errMsg = status.OK.errmsg
        result.resData = {"data": knowledge_return, "page": page, "pagesize": pagesize, "total": Knowledgecount}
    except Exception as e:
        log.error(('[knowledge management - db_query_knowledge] database knowledge query error:{0}'.format(e)))
        print(traceback.format_exc())
        result.flag = False
        result.errCode = status.ERROR.code
        result.errMsg = status.ERROR.errmsg
        result.resData = {}
    return result


# 知识库列表删除
def db_delete_knowledge(id, db):
    start = datetime.datetime.now()
    result = server_schemas.CommonResponse
    result.flag = True
    try:
        # 删除线程中该知识库的解析任务
        for task in tasks:
            if task['knowledge_id'] == id:
                r = task['task'].cancel()
                log.info(f"删除{task['file_id']}的解析任务为 {r}")
        tasks.clear()
        # 删除知识库的文件
        knowledgelist = db.query(models.KnowledgeFile).filter(models.KnowledgeFile.knowledgeid == id).delete(
            synchronize_session=False)
        # 删除本地文件
        knowledgequeried = db.query(models.Knowledge).filter(models.Knowledge.id == id).all()
        global_path = process_setting.get_system_default_path().config_value
        print(os.path.join(global_path, "knowledge"))
        import shutil
        shutil.rmtree(os.path.join(global_path, "knowledge",
                                   f'{knowledgequeried[0].name}_{knowledgequeried[0].id}'), ignore_errors=True)
        # os.removedirs(os.path.join(global_path, "knowledge",
        #                                    f'{knowledgequeried[0].name}_{knowledgequeried[0].id}'))
        # 向量库删除
        # vector_type = get_vector_type(knowledgequeried[0].config)
        start_vector = datetime.datetime.now()
        adapter_vector_delete(knowledgequeried[0], VECTOR_VERSION)
        log.info(
            ('[knowledge management - db_delete_knowledge] process vector  delete time:{0}'.format(
                (datetime.datetime.now() - start_vector).total_seconds())))

        # 删除知识库
        knowledgelist = db.query(models.Knowledge).filter(
            and_(models.Knowledge.id == id)).delete(synchronize_session=False)
        db.commit()
        db.query(models.KnowledgeFile).filter(
            and_(models.KnowledgeFile.knowledgeid == id)).delete(synchronize_session=False)
        db.commit()
        result.errCode = status.OK.code
        result.errMsg = status.OK.errmsg
        result.resData = {}
    except Exception as e:
        log.error(('[knowledge management - db_delete_knowledge] database knowledge delete error:{0}'.format(e)))
        print(traceback.format_exc())
        result.flag = False
        result.errCode = status.ERROR.code
        result.errMsg = e
        result.resData = {}
    log.info(('[knowledge management - db_delete_knowledge] total knowledge delete time:{0}'.format(
        (datetime.datetime.now() - start).total_seconds())))
    return result


# 获取知识库文件列表
def db_get_knowledge_files(id, page, pagesize, db):
    result = KnowledgeFileGetResponse
    result.flag = True
    try:
        # 根据id查询知识库下的文件列表
        knowledgelist = db.query(models.KnowledgeFile).filter(
            and_(models.KnowledgeFile.knowledgeid == id)).order_by(
            models.KnowledgeFile.createtime).limit(pagesize).offset(pagesize * (page - 1)).all()
        Knowledgecount = db.query(models.KnowledgeFile).filter(
            and_(models.KnowledgeFile.knowledgeid == id)).order_by(
            models.KnowledgeFile.createtime).count()
        db.commit()
        # print(knowledgelist)
        result.errCode = status.OK.code
        result.errMsg = status.OK.errmsg
        result.resData = {"data": knowledgelist, "page": page, "pagesize": pagesize, "total": Knowledgecount}
    except Exception as e:
        log.error(('[knowledge management - db_get_knowledge_files] database knowledge delete error:{0}'.format(e)))
        print(traceback.format_exc())
        result.flag = False
        result.errCode = status.ERROR.code
        result.errMsg = status.ERROR.errmsg
        result.resData = {}
    return result


# 删除知识库中的文件
def db_delete_knowledge_files(id, db):
    start = datetime.datetime.now()
    result = server_schemas.CommonResponse
    result.flag = True
    # 查询线程任务列表，删除线程任务
    for task in tasks:
        if task['file_id'] == id:
            log.info(f"删除{task['file_id']}的解析任务")
            task['task'].cancel()
            tasks.remove(task)
    try:
        # 根据id查询
        knowledgelist = db.query(models.KnowledgeFile).filter(
            and_(models.KnowledgeFile.id == id)).all()
        # 查询对应的知识库配置信息
        knowledgequeried = db.query(models.Knowledge).filter(models.Knowledge.id == knowledgelist[0].knowledgeid).all()
        if len(knowledgequeried) == 0:
            log.info(f'[knowledge management - db_delete_knowledge_files] 查询知识库失败，{knowledgelist[0].knowledgeid}')
        # 删除向量库中的文件
        # vector_type = get_vector_type(knowledgequeried[0].config)
        start_vector = datetime.datetime.now()
        adapter_vector_file_delete(knowledgequeried[0], VECTOR_VERSION, knowledgelist[0].name, knowledgelist[0].id)
        log.info(
            ('[knowledge management - db_delete_knowledge_files] process vector delfile time:{0}'.format(
                (datetime.datetime.now() - start_vector).total_seconds())))

        # 删除本地文件 todo
        global_path = process_setting.get_system_default_path().config_value
        file_local = os.path.join(global_path, "knowledge", f'{knowledgequeried[0].name}_{knowledgequeried[0].id}',
                                  knowledgelist[0].name)
        print(f'delete local file: {file_local}')
        os.remove(file_local)
        # 删除根据id删除
        knowledgelist = db.query(models.KnowledgeFile).filter(
            and_(models.KnowledgeFile.id == id)).delete(synchronize_session=False)
        db.commit()
        print(knowledgelist)
        result.errCode = status.OK.code
        result.errMsg = status.OK.errmsg
        result.resData = {}
    except Exception as e:
        log.error(('[knowledge management - db_delete_knowledge_files] database knowledge file delete error:{0}'.format(e)))
        print(traceback.format_exc())
        result.flag = False
        result.errCode = status.ERROR.code
        result.errMsg = e
        result.resData = {}
    log.info(('[knowledge management - db_delete_knowledge_files] total knowledge file delete time:{0}'.format(
        (datetime.datetime.now() - start).total_seconds())))
    return result


# 获取向量库类型
# def get_vector_type(config):
#     storage = json.loads(config)["storage_param"]
#     if "index_params" in storage.keys():
#         return "milvus"
#     else:
#         return "chromadb"

# 向量库创建
def adapter_vector_create(knowledge, vector_type):
    params_dict = {}
    params_dict["kb_name"] = knowledge.name
    params_dict["vs_type"] = vector_type
    params_dict["global_param"] = json.loads(knowledge.config)["global_param"]
    params_dict["storage_param"] = json.loads(knowledge.config)["storage_param"]
    params_dict["query_param"] = json.loads(knowledge.config)["query_param"]
    kb_svc = KBServiceFactory.get_service(params_dict)
    # 创建知识库
    kb_svc.create_kb()


# 向量库删除
def adapter_vector_delete(knowledge, vector_type):
    params_dict = {}
    params_dict["kb_name"] = knowledge.name
    params_dict["vs_type"] = vector_type
    params_dict["global_param"] = json.loads(knowledge.config)["global_param"]
    params_dict["storage_param"] = json.loads(knowledge.config)["storage_param"]
    params_dict["query_param"] = json.loads(knowledge.config)["query_param"]
    kb_svc = KBServiceFactory.get_service(params_dict)
    # 创建知识库
    kb_svc.drop_kb()


# 向量库文件添加
def adapter_vector_file_add(knowledge, vector_type, filename, fileid, db):
    from ...plugins.knowledge_base.utils import KnowledgeFile
    try:
        params_dict = {}
        params_dict["kb_name"] = knowledge.name
        params_dict["vs_type"] = vector_type
        params_dict["global_param"] = json.loads(knowledge.config)["global_param"]
        params_dict["storage_param"] = json.loads(knowledge.config)["storage_param"]
        params_dict["query_param"] = json.loads(knowledge.config)["query_param"]
        # 增加一个参数平台如轨迹流动、ollama
        kb_svc = KBServiceFactory.get_service(params_dict)
        global_path = process_setting.get_system_default_path().config_value
        file_local_path = os.path.join(global_path, "knowledge", f'{knowledge.name}_{knowledge.id}')
        log.info(f"file_local_path:{file_local_path}")
        with lock:
            log.info(f"线程 {threading.current_thread().name} ++++++++++++++++ {filename} 获得锁 ++++++++++++++++")
            kb_svc.add_files([
                KnowledgeFile(
                    kb_name=params_dict["kb_name"],
                    file_name=os.path.join(file_local_path, filename),
                    file_id=fileid,
                )
            ])
        log.info(f"线程 {threading.current_thread().name} ---------------- {filename} 释放锁 ----------------")
        # 更新数据库中文件状态
        file = db.query(models.KnowledgeFile).filter(models.KnowledgeFile.id == fileid).first()
        if file: 
            file.status = FileAnalysisStatus.DONE.value
            file.process = 100.0
            db.add(file)
            db.commit()
            db.refresh(file)
        # tasks列表移除
        for task in tasks:
            if task['file_id'] == fileid:
                tasks.remove(task)
        return
    except Exception as e:
        log.error('{0}'.format(e))
        file = db.query(models.KnowledgeFile).filter(models.KnowledgeFile.id == fileid).first()
        if file: 
            file.status = FileAnalysisStatus.FAILED.value
            file.process = 0.0
            db.add(file)
            db.commit()
            db.refresh(file)
        return


# 向量库文件删除
def adapter_vector_file_delete(knowledge, vector_type, filename, fileid):
    from ...plugins.knowledge_base.utils import KnowledgeFile
    params_dict = {}
    params_dict["kb_name"] = knowledge.name
    params_dict["vs_type"] = vector_type
    params_dict["global_param"] = json.loads(knowledge.config)["global_param"]
    params_dict["storage_param"] = json.loads(knowledge.config)["storage_param"]
    params_dict["query_param"] = json.loads(knowledge.config)["query_param"]
    kb_svc = KBServiceFactory.get_service(params_dict)
    global_path = process_setting.get_system_default_path().config_value
    file_local_path = os.path.join(global_path, "knowledge", f'{knowledge.name}_{knowledge.id}')
    kb_svc.delete_file(
        KnowledgeFile(
            kb_name=params_dict["kb_name"],
            file_name=os.path.join(file_local_path, filename),
            file_id=fileid,
        )
    )


def get_knowledge_by_id(id):
    from pkg.database import models
    from pkg.database.database import SessionLocal
    db = SessionLocal()
    knowledgequeried = db.query(models.Knowledge).filter(models.Knowledge.id == id).all()
    if len(knowledgequeried) == 0:
        return
    params_dict = {}
    params_dict["kb_name"] = knowledgequeried[0].name
    params_dict["vs_type"] = VECTOR_VERSION
    params_dict["global_param"] = json.loads(knowledgequeried[0].config)["global_param"]
    params_dict["storage_param"] = json.loads(knowledgequeried[0].config)["storage_param"]
    params_dict["query_param"] = json.loads(knowledgequeried[0].config)["query_param"]
    return params_dict


def clean_konwledge_by_session(sessionid, *filelist):
    try:
        start = datetime.datetime.now()
        from pkg.database import models
        from pkg.database.database import SessionLocal
        db = SessionLocal()
        # step 1: 根据sessionid 查询知识库
        knowledgequeried = db.query(models.Knowledge).filter(models.Knowledge.id == sessionid).all()
        if len(knowledgequeried) == 0:
            log.info(('[knowledge management - clean_konwledge_by_session] knowledge not found:{0}'.format(sessionid)))
            return
        if len(filelist) == 0:  # 操作整个知识库
            # step 2: 删除对应的知识库
            # 查询对应的知识库配置信息
            start_vector = datetime.datetime.now()
            adapter_vector_delete(knowledgequeried[0], VECTOR_VERSION)
            log.info(
                ('[knowledge management - clean_konwledge_by_session] process vector  delete time:{0}'.format(
                    (datetime.datetime.now() - start_vector).total_seconds())))
            # step 3：删除知识库对应的本地文件以及文件夹
            global_path = process_setting.get_system_default_path().config_value
            print(os.path.join(global_path, "knowledge"))
            import shutil
            shutil.rmtree(os.path.join(global_path, "knowledge",
                                       f'{knowledgequeried[0].name}_{knowledgequeried[0].id}'), ignore_errors=True)
            # step 4：数据库中删除对应的记录
            db.query(models.Knowledge).filter(
                and_(models.Knowledge.id == sessionid)).delete(synchronize_session=False)
            db.commit()
            db.query(models.KnowledgeFile).filter(
                and_(models.KnowledgeFile.knowledgeid == sessionid)).delete(synchronize_session=False)
            db.commit()
        else:  # 操作知识库中的文件
            # 根据id查询
            knowledgefilelist = db.query(models.KnowledgeFile).filter(
                and_(models.KnowledgeFile.id == sessionid)).all()
            filter_kfile = []
            for kfile in knowledgefilelist:
                for filename in filelist:
                    if kfile.name == filename:
                        filter_kfile.append(kfile)
                        break
                # 根据id查询
                knowledgelist = db.query(models.KnowledgeFile).filter(
                    and_(models.KnowledgeFile.id == kfile.id)).all()
                # 删除向量库中的文件
                # vector_type = get_vector_type(knowledgequeried[0].config)
                start_vector = datetime.datetime.now()
                adapter_vector_file_delete(knowledgequeried[0], VECTOR_VERSION, knowledgelist[0].name,
                                           knowledgelist[0].id)
                log.info(
                    ('[knowledge management - db_delete_knowledge_files] process vector delfile time:{0}'.format(
                        (datetime.datetime.now() - start_vector).total_seconds())))

                # 删除本地文件 todo
                global_path = process_setting.get_system_default_path().config_value
                file_local = os.path.join(global_path, "knowledge",
                                          f'{knowledgequeried[0].name}_{knowledgequeried[0].id}',
                                          knowledgelist[0].name)
                print(f'delete local file: {file_local}')
                os.remove(file_local)
                # 删除根据id删除
                db.query(models.KnowledgeFile).filter(
                    and_(models.KnowledgeFile.id == kfile.id)).delete(synchronize_session=False)
                db.commit()

    except Exception as e:
        print(traceback.format_exc())
        log.error(('[knowledge management - clean_konwledge_by_session] clean knowledge: {0}, error:{1}'.format(sessionid,e)))
    log.info(('[knowledge management - clean_konwledge_by_session] total session delete time:{0}'.format(
        (datetime.datetime.now() - start).total_seconds())))

# 知识库相关文件迁移
def mv_knowledge_file(oldpath, newpath):
    # log.info("[knowledge management - mv_knowledge_file] old path :{0},new path :{1}".format(oldpath,newpath))
    from pkg.database.database import SessionLocal
    db = SessionLocal()
    # step 1: 根据名称 查询迁移进度
    knownledge_log = db.query(models.OptLog).filter(models.OptLog.name == "knowledge_management").all()
    result = {"flag": True, "errCode": status.OK.code, "errMsg": status.OK.errmsg}
    if len(knownledge_log) !=0:
        if knownledge_log[0].status == 1:
            log.info("[knowledge management - mv_knowledge_file] 知识库正在迁移中请稍后 :{0}".format(knownledge_log[0]))
            result["resData"] = {"status":False,"message":"知识库正在迁移中请稍后"}
            return result
        else:
            result["resData"] = {"status": True, "message": "知识库可以迁移"}
    else:
        result["resData"] = {"status": True, "message": "知识库未迁移过"}
    # 创建 Thread 实例
    t1 = Thread(target=cp_knowledge_file, args=(oldpath, newpath))
    # 启动线程运行
    t1.start()
    return result

def cp_knowledge_file(oldpath, newpath):
    log.info("[knowledge management - mv_knowledge_file] old path :{0},new path :{1}".format(oldpath, newpath))
    from pkg.database.database import SessionLocal
    db = SessionLocal()
    try:
        target_path = os.path.join(newpath, "knowledge")
        if not os.path.exists(target_path):
            # 如果目标路径不存在原文件夹的话就创建
            os.makedirs(target_path)
        source_path = os.path.join(oldpath, "knowledge")
        if not os.path.exists(source_path):
            # 如果目标路径存在原文件夹的话就先删除
            # shutil.rmtree(target_path)
            log.error("{0} dir not exits".format(source_path))
            return
        filename = os.listdir(source_path)
        total_knowledge = len(filename)
        move = 0
        # step 1: 根据名称 查询迁移进度
        knownledge_log = db.query(models.OptLog).filter(models.OptLog.name == "knowledge_management").all()
        if len(knownledge_log) == 0 and total_knowledge!=0:
            # insert data
            kid = uuid.uuid1().hex
            inprocess = json.dumps({"total": total_knowledge, "move": 0})
            newlog = models.OptLog(id=kid, name="knowledge_management", status=1, inprocess=inprocess,
                                   reason="in process",
                                   createtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            db.add(newlog)
            db.commit()
            db.refresh(newlog)
        for i in filename:
            target = os.path.join(target_path, i)
            shutil.copytree(os.path.join(source_path, i), target,dirs_exist_ok=True)
            move = move + 1
            if move == total_knowledge:
                opt_update = {"createtime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": 2,
                              "reason": "success",
                              "inprocess": json.dumps({"total": total_knowledge, "move": move})}
            else:
                opt_update = {"createtime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": 1,
                              "reason": "success", "inprocess": json.dumps({"total": total_knowledge, "move": move})}
            db.query(models.OptLog).filter(models.OptLog.name == "knowledge_management").update(opt_update)
            db.commit()
        log.info("[knowledge management - mv_knowledge_file] move success")
    except Exception as e:
        log.error(e)
        print(traceback.format_exc())
        opt_update = {"createtime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": 3,
                      "reason": f"{e}"}
        db.query(models.OptLog).filter(models.OptLog.name == "knowledge_management").update(opt_update)
        db.commit()
# 获取知识库迁移的进度
def get_move_knowledge_process():
    from pkg.database.database import SessionLocal
    db = SessionLocal()
    result = {"flag": True, "errCode": status.OK.code, "errMsg": status.OK.errmsg}
    # step 1: 根据名称 查询迁移进度
    knownledge_log = db.query(models.OptLog).filter(models.OptLog.name == "knowledge_management").all()
    if len(knownledge_log) == 0:
        result["resData"] = {"status": 0, "message": "无正在迁移的知识库",
                             "total": 0, "moved": 0}
        return result

    inprocess = json.loads(knownledge_log[0].inprocess)
    result["resData"] = {"status":knownledge_log[0].status,"message":knownledge_log[0].reason,"total":inprocess["total"],"moved":inprocess["move"]}
    return result

# 获取知识库的存储空间
def get_move_knowledge_volume():
    from pkg.database.database import SessionLocal
    db = SessionLocal()
    try:
        knowledgelist = db.query(models.Knowledge).filter().order_by(desc(models.Knowledge.createtime)).all()
        volume = 0
        for tmp in knowledgelist:
            file_list = db.query(models.KnowledgeFile).filter(
                and_(models.KnowledgeFile.knowledgeid == tmp.id)).order_by(
                models.KnowledgeFile.createtime).all()
            for file in file_list:
                volume = volume + file.bytetotal
        result = {"flag": True, "errCode": status.OK.code, "errMsg": status.OK.errmsg,"volume": volume}
    except Exception as e:
        log.error(('[knowledge management - get_move_knowledge_volume] get_move_knowledge_volume error:{0}'.format(e)))
        print(traceback.format_exc())
        result.flag = False
        result.errCode = status.ERROR.code
        result.errMsg = status.ERROR.errmsg
        result.resData = {}
    return result


#######################################knowledge params based on session ############################################
@router.post("/{knowledge_id}/session/{session_id}", response_model=KnowledgeSessionResponse)
async def api_get_knowledge_config_by_session(
        req: Request,
        knowledge_id: str,
        session_id: str,
        payload: schemas.GetKnowledgeSessionConfigPayload,
        db: Session = Depends(crud.get_db),
        headers=Depends(get_headers),
):
    response = KnowledgeSessionResponse
    user_id = headers[const.HTTP_HEADER_USER_ID]
    db_query_plugin = query_plugin_by_key(plugin_key=payload.plugin_key, user_id=user_id)
    if db_query_plugin and hasattr(db_query_plugin, "plugin_id"):
        plugin_id = db_query_plugin.plugin_id
    else:
        log.error(f"No plugin_id found in query_plugin_by_key with user_id: [{user_id}]; plugin_key: [{payload.plugin_key}].")
        return response.fail(status.ERROR.code, status.ERROR.errmsg)
    log.debug(f"Getting knowledge params in session: knowledge_id: [{knowledge_id}],"
              f"session_id: [{session_id}]; plugin_id: [{plugin_id}]")

    try:
        plugin_param_dict = {}
        # 先从插件管理获取
        db_query = query_session_plugin_by_id(session_id, plugin_id)
        if db_query and hasattr(db_query, "plugin_param"):
            plugin_param = db_query.plugin_param
            plugin_param_dict = json.loads(plugin_param)

        if not plugin_param_dict:
            # None, init for next step.
            plugin_param_dict = {}

        # if knowledge_id not in plugin_param_dict.keys():
        #     # 插件管理中没有对应knowledge_id的配置，从知识库配置中获取
        #     log.info(
        #         f"No params found in plugin manager with knowledge_id: [{knowledge_id}], session_id: [{session_id}]."
        #         f"Using default params while knowledge base created.")
        #     knowledge_plugin_param_dict = get_knowledge_by_id(knowledge_id)
        #     if not knowledge_plugin_param_dict:
        #         log.error(f"No params found in knowledge base with knowledge_id: [{knowledge_id}]")
        #     else:
        #         log.info("Start update plugin params...")
        #         # 更新
        #         plugin_param_dict.setdefault(knowledge_id, knowledge_plugin_param_dict)
        #         session_updates = {
        #             "session_id": session_id,
        #             "plugin_id": plugin_id,
        #             "update_val": {
        #                 "plugin_param": json.dumps(plugin_param_dict),
        #             },
        #         }
        #         db_update = update_session_tool([SessionUpdateReq(**session_updates)])
        #         if db_update[0] is None:
        #             log.error("Error happened while update_session_tool, please check.")
        #             return response.fail(status.ERROR.code, status.ERROR.errmsg)
        #         else:
        #             log.info("update plugin params succeeded.")
        #               rr = db_get_knowledge_config(knowledge_id, db)
        #               return rr
        if not plugin_param_dict or knowledge_id not in plugin_param_dict.keys():
            flag = set_knowledge_config(knowledge_id, session_id, plugin_id, plugin_param_dict)
            if flag != status.OK.code:
                return response.fail(status.ERROR.code, status.ERROR.errmsg)
            else:
                rr = db_get_knowledge_config(knowledge_id, db)
                return rr
        query_config = plugin_param_dict[knowledge_id].get("query_param", {})
        if not query_config:
            result = response.fail(status.ERROR.code, status.ERROR.errmsg)
        else:
            result = response.success(query_config)
    except Exception as e:
        log.error(f"[get_knowledge_config_by_session] failed, error: [{e}]")
        result = response.fail(status.ERROR.code, status.ERROR.errmsg)

    return result


def set_knowledge_config(knowledge_id, session_id, plugin_id, params_dict):
    # 插件管理中没有对应knowledge_id的配置，从知识库配置中获取
    log.info(
        f"No params found in plugin manager with knowledge_id: [{knowledge_id}], session_id: [{session_id}]."
        f"Using default params while knowledge base created.")
    knowledge_plugin_param_dict = get_knowledge_by_id(knowledge_id)
    if not knowledge_plugin_param_dict:
        log.error(f"No params found in knowledge base with knowledge_id: [{knowledge_id}]")
    else:
        log.info("Start update plugin params...")
        # 更新
        params_dict.setdefault(knowledge_id, knowledge_plugin_param_dict)
        session_updates = {
            "session_id": session_id,
            "plugin_id": plugin_id,
            "update_val": {
                "plugin_param": json.dumps(params_dict),
            },
        }
        db_update = update_session_tool([SessionUpdateReq(**session_updates)])
        if db_update[0] is None:
            log.error("Error happened while update_session_tool, please check.")
            return status.ERROR.code
        else:
            log.info("update plugin params succeeded.")
            return status.OK.code
    return status.OK.code


@router.post("/{knowledge_id}/session/{session_id}/update", response_model=dict)
async def api_update_knowledge_config_by_session(
        req: Request,
        knowledge_id: str,
        session_id: str,
        payload: schemas.UpdateKnowledgeSessionConfigPayload,
        headers=Depends(get_headers),
):
    response = server_schemas.CommonResponse

    user_id = headers[const.HTTP_HEADER_USER_ID]
    db_query_plugin = query_plugin_by_key(plugin_key=payload.plugin_key, user_id=user_id)
    if db_query_plugin and hasattr(db_query_plugin, "plugin_id"):
        plugin_id = db_query_plugin.plugin_id
    else:
        log.error(f"No plugin_id found in query_plugin_by_key with user_id: [{user_id}]; plugin_key: [{payload.plugin_key}].")
        return response.fail(status.ERROR.code, status.ERROR.errmsg)

    user = get_username_info(req.headers)
    if payload.user is None:
        payload.user = user
    else:
        for us in payload.user:
            if us == user:
                continue
            from pkg.server.router.account_api import alchemytool
            if alchemytool.select_user_by_name(us) == None:
                return server_schemas.CommonResponse(
                    flag=False,
                    errCode=status.AUTHORIZATION_ERROR.code,
                    errMsg=f"{us}{status.AUTHORIZATION_ERROR.errmsg}"
                )

    # 先获取当前session下的知识库参数
    log.debug(f"Getting knowledge params in session: knowledge_id: [{knowledge_id}],"
              f"session_id: [{session_id}]; plugin_id: [{plugin_id}]")
    try:
        db_query = query_session_plugin_by_id(session_id, plugin_id)
        plugin_param = db_query.plugin_param
        plugin_param_dict = json.loads(plugin_param)
        if not plugin_param or knowledge_id not in plugin_param:
            # 插件管理中没有参数，报错
            log.error(
                f"No params found in plugin manager with knowledge_id: [{knowledge_id}];"
                f"session_id: [{session_id}]; plugin_id: [{plugin_id}].")
            return response.fail(status.ERROR.code, status.ERROR.errmsg)

        query_param = json.loads(payload.knowledge_setting)
        plugin_param_dict[knowledge_id]["query_param"] = query_param
        log.debug(f"Query param from payload: [{query_param}]")
        session_updates = {
            "session_id": session_id,
            "plugin_id": plugin_id,
            "update_val": {
                "plugin_param": json.dumps(plugin_param_dict),
            },
        }
        log.debug(f"Start update plugin params with updates info: [{session_updates}]")
        db_update = update_session_tool([SessionUpdateReq(**session_updates)])
        if db_update[0] is None:
            log.error("Error happened while update_session_tool, please check.")
            result = response.fail(status.ERROR.code, status.ERROR.errmsg)
        else:
            log.debug(f"Update plugin params done! Return [{db_update[0]}]")
            result = response.success({})
    except Exception as e:
        log.error(f"[update_knowledge_config_by_session] failed, error: [{e}]")
        result = response.fail(status.ERROR.code, status.ERROR.errmsg)
    return result


@router.get("/{knowledge_id}/current_embedding_info", response_model=KnowledgeSessionResponse)
async def api_get_knowledge_current_embedding_info(
        req: Request,
        knowledge_id: str,
        headers=Depends(get_headers),
        db: Session = Depends(crud.get_db),
):
    response = KnowledgeSessionResponse
    res_data = {}

    user_id = headers[const.HTTP_HEADER_USER_ID]
    try:
        # embedding_list = process_model.get_download_embedding_model_list()
        embedding_list = process_model.get_download_ollama_embedding_model_list()
        if not embedding_list:
            log.error(
                f"No available embedding model, please download in model market first.")
            return response.fail(status.YUAN_MODEL_NOT_EXIST_ERROR.code, status.YUAN_MODEL_NOT_EXIST_ERROR.errmsg)
        log.debug(f"Getting [{len(embedding_list)}] embedding model(s).")
        # res_data.setdefault("embedding_list", embedding_list)

        # check knowledgebase exists or not.
        kb_file = db.query(models.Knowledge).outerjoin(
            models.KnowledgeFile,
            models.Knowledge.id == models.KnowledgeFile.knowledgeid
        ).filter(
            models.KnowledgeFile.knowledgeid == knowledge_id,
            models.Knowledge.id == models.KnowledgeFile.knowledgeid
        ).all()
        if kb_file:
            log.debug(f"knowledgebase [{knowledge_id}] already exist, embedding model can't be modified.")
            config = json.loads(kb_file[0].config)
            local_path = config["global_param"]["embed_model"]
            name = os.path.basename(local_path)
            is_editable = False
            is_available = any(embedding["name"] == name for embedding in embedding_list)
        else:
            log.debug(f"No knowledgebase with kb_id [{knowledge_id}] exist.")
            name = embedding_list[0]["name"]
            local_path = embedding_list[0]["local_path"]
            is_editable = True
            is_available = True

        res_data.setdefault("name", name)
        res_data.setdefault("local_path", local_path)
        res_data.setdefault("is_editable", is_editable)
        res_data.setdefault("is_available", is_available)
        return response.success(res_data)
    except Exception as e:
        log.error(f"Error happened in current_embedding_info. error msg: [{e}].")
        return response.fail(status.ERROR.code, status.ERROR.errmsg)


