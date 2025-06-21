from fastapi import APIRouter,Request
from pkg.server import schemas as server_schemas
from typing import Union
import requests
from pydantic import BaseModel
import json
from ...projectvar.statuscode import StatusCodeEnum as status
from ..process.process_account import AlchemyTool
from pkg.projectvar import constants as const
from pkg.logger import Log
from pathlib import Path
import hashlib
import os
import zipfile
import io
import threading
import uuid
import shutil
from pkg.server.process import process_download
from pkg.projectvar import *

gvar = Projectvar()

log=Log()
alchemytool = AlchemyTool()

router = APIRouter(
    prefix = "/update",
    tags=["update"],
    responses={404: {"description": "Not found"}},
)

UPDATE_SERVER_URL = const.UPDATE_SERVER_URL

DOWNLOAD_DIR = const.DOWNLOAD_DIR

class UpdateResponse(server_schemas.CommonResponse):
    resData: Union[str, None]
    
class UpdateReceive(BaseModel):
    current_version:str
    last_version:str
    release_time:str
    release_log:str
    is_release:bool
    

class DeleteReceive(BaseModel):
    last_version:str
    current_version:str
     
class DownloadStatusResponse(server_schemas.CommonResponse):
    resData: Union[str, None]


def get_file_hash(file_path: Path) -> str:
    """计算文件的MD5哈希值"""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):  # 分块读取大文件
            hasher.update(chunk)
    return hasher.hexdigest()

def scan_folder(folder: Path) -> dict:
    """扫描文件夹并返回{相对路径: 哈希值}字典"""
    file_dict = {}
    for item in folder.rglob("*"):
        if item.is_file():
            rel_path = str(item.relative_to(folder))
            file_dict[rel_path] = get_file_hash(item)
    return file_dict

# def download_files_from_server(server_url, path_list, download_dir="./download"):
#     """
#     从服务器下载文件到本地指定目录
    
#     参数:
#         server_url (str): 服务器URL，例如 "http://localhost:8000"
#         path_list (list): 要下载的文件路径列表
#         download_dir (str): 本地下载目录，默认为 "./download"
    
#     返回:
#         list: 下载的文件路径列表
#     """
#     log.info("download from server...")
#     # 如果存在，则清空文件夹下的内容
#     folder = Path(download_dir).resolve()
#     if folder.exists() and folder.is_dir():
#         try:
#             shutil.rmtree(folder)  # 递归删除文件夹
#             print(f"已成功删除文件夹: {folder}")
#         except Exception as e:
#             print(f"删除失败: {e}")
#     else:
#         print(f"文件夹不存在，无需删除: {folder}")
    
#     # 确保下载目录存在
#     os.makedirs(download_dir, exist_ok=True)
    
#     db_query = alchemytool.select_user_by_name('hello')
#     # 准备请求数据
#     url = f"{server_url}/download/files"
#     payload = {"user_id":db_query.user_id,"path_list": path_list}
    
#     # 发送请求
#     response = requests.post(url, json=payload,verify=False)
    
#     # 检查响应状态
#     if response.status_code != 200:
#         raise Exception(f"下载失败: {response.status_code} - {response.text}")
    
#     # 获取内容类型
#     content_type = response.headers.get('Content-Type', '')
    
#     log.info("Local unzip...")
#     # 处理响应
#     if 'application/zip' in content_type:
#         # 处理ZIP文件
#         with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
#             # 解压所有文件到下载目录
#             zip_ref.extractall(download_dir)
            
#             # 获取解压后的文件列表
#             extracted_files = [os.path.join(download_dir, name) for name in zip_ref.namelist()]
#             log.info("download complete...")
#             return extracted_files
#     else:
#         # 处理单个文件
#         # 从响应头或URL中获取文件名
#         filename = response.headers.get('Content-Disposition', '').split('filename=')[-1].strip('"')
#         if not filename:
#             # 如果无法从响应头获取文件名，使用路径列表中的第一个文件名
#             filename = os.path.basename(path_list[0])
        
#         # 保存文件
#         file_path = os.path.join(download_dir, filename)
#         with open(file_path, 'wb') as f:
#             f.write(response.content)
#         log.info("download complete...")
#         return [file_path]
    
def download_files_from_server(server_url, path_list, download_dir="./download"):
    """
    从服务器下载文件到本地指定目录
    
    参数:
        server_url (str): 服务器URL，例如 "http://localhost:8000"
        path_list (list): 要下载的文件路径列表
        download_dir (str): 本地下载目录，默认为 "./download"
    
    返回:
        list: 下载的文件路径列表
    """
    log.info("download from server...")
    # 如果存在，则清空文件夹下的内容
    folder = Path(download_dir).resolve()
    if folder.exists() and folder.is_dir():
        try:
            shutil.rmtree(folder)  # 递归删除文件夹
            print(f"已成功删除文件夹: {folder}")
        except Exception as e:
            print(f"删除失败: {e}")
    else:
        print(f"文件夹不存在，无需删除: {folder}")
    
    # 创建下载对象
    client = process_download.FileDownloadClient(base_url=server_url)
    
    # 确保下载目录存在
    os.makedirs(download_dir, exist_ok=True)
    
    db_query = alchemytool.select_user_by_name('hello')
    
    # 准备请求数据

    if const.SYSTEM == const.WINDOWS :
        # win
        url = f"{server_url}/download/files"
        # payload = {"user_id":db_query.user_id,"path_list": path_list} 
        payload = {"user_id":db_query.user_id,"version":const.OPENCHAT_VERSION,"path_list": path_list} 
    else:
        # mac
        url = f"{server_url}/download/files_mac"
        # payload = {"user_id":db_query.user_id,"path_list": [["mac", "OpenChat.dmg"]]} 
        payload = {"user_id":db_query.user_id,"version":const.OPENCHAT_VERSION, "path_list": [["mac", "OpenChat.dmg"]]} 
    
    response = client.download_file(url,payload,download_dir) 
    
    if const.SYSTEM == const.WINDOWS:

        # 处理ZIP文件
        with zipfile.ZipFile(os.path.join(download_dir,"download.zip")) as zip_ref:
            # 解压所有文件到下载目录
            zip_ref.extractall(download_dir)
            
            # 获取解压后的文件列表
            extracted_files = [os.path.join(download_dir, name) for name in zip_ref.namelist()]
            log.info("download complete...")
        os.unlink(os.path.join(download_dir,"download.zip"))
        return extracted_files
    else:
        return []

@router.get('/check_update',response_model=UpdateResponse)
async def check_update():
    result = UpdateResponse
    try:
        response = requests.get(UPDATE_SERVER_URL + "/version/current/" + const.OPENCHAT_VERSION,timeout=2,verify=False)
        current_version_info = json.loads(response.content)
        log.info(f"当前服务器版本信息：{current_version_info['current_version']}")
        ## if current_version_info['current_version'].find('dev-')!=-1:
        ##     # 说明是测试的dev
        ##     # 用于测试时dev更新测试，发版时请取消注释，测试发版时请注释
        ##     log.info(f"版本一致或新版本未发布，不用更新")
        ##     result.flag = True
        ##     result.errMsg = status.OK.errmsg
        ##     result.errCode = status.OK.code
        ##     result.resData = None
        ##     return result
        if current_version_info['current_version'] != const.OPENCHAT_VERSION and current_version_info['is_release'] :
            log.info(f"版本不一致，请更新")
            result.flag = True
            result.errMsg = status.OK.errmsg
            result.errCode = status.OK.code
            result.resData = json.dumps(current_version_info)
            return result
        else:
            log.info(f"版本一致或新版本未发布，不用更新")
            result.flag = True
            result.errMsg = status.OK.errmsg
            result.errCode = status.OK.code
            result.resData = None
            return result
            
    except Exception as e:
        log.error(f"{e}")
        result.flag = True
        result.errMsg = status.UPDATE_CHECK_ERROR.errmsg
        result.errCode = status.UPDATE_CHECK_ERROR.code
        result.resData = None
        return result
        
download_task = {}
@router.get('/start_download',response_model=UpdateResponse)
async def update():
    result = UpdateResponse
    try:
        # 获取文件哈希值
        response = requests.get(UPDATE_SERVER_URL + "/files/hashlist/diff/" + const.OPENCHAT_VERSION,verify=False)
        path_list = json.loads(response.content)
            
        file_list = []
        # 下载文件
        os.makedirs(DOWNLOAD_DIR,exist_ok=True)
        # file_list = download_files_from_server(UPDATE_SERVER_URL,path_list,DOWNLOAD_DIR)
        task_id = str(uuid.uuid4())
        task = threading.Thread(target=download_files_from_server,args=(UPDATE_SERVER_URL,path_list,DOWNLOAD_DIR),daemon=True)
        
        task.start()
        global download_task
        download_task[task_id] = task
        
    except Exception as e:
        result.flag = True
        result.errMsg = status.UPDATE_DOWNLOAD_ERROR.errmsg
        result.errCode = status.UPDATE_DOWNLOAD_ERROR.code
        result.resData = str(e)
        return result
    else:
        result.flag = True
        result.errMsg = status.OK.errmsg
        result.errCode = status.OK.code
        result.resData = json.dumps({"task_id": task_id})
        return result

@router.get('/check_download_status', response_model=DownloadStatusResponse)
def check_status(task_id: str):
    result = DownloadStatusResponse
    global download_task
    task = download_task.get(task_id)
    if task and task.is_alive():# 正在下载
        result.flag = True
        result.errMsg = status.OK.errmsg
        result.errCode = status.OK.code
        result.resData = json.dumps({"task_id": task_id, "status": False,"progress":gvar.get_update_progress()})
        return result
    else:
        progress = gvar.get_update_progress()
        print(f"check_download_status:{progress}")
        progress = float(progress)
        if progress >= 99:
            result.flag = True
            result.errMsg = status.OK.errmsg
            result.errCode = status.OK.code
            result.resData = json.dumps({"task_id": task_id, "status": True,"progress":progress})
            download_task.clear()
            return result
        else:
            result.flag = False
            result.errMsg = status.ERROR.errmsg
            result.errCode = status.ERROR.code
            result.resData = json.dumps({"task_id": task_id, "status": True})
            download_task.clear()
            return result

@router.get('/start_download_test',response_model=UpdateResponse)
async def update():
    result = UpdateResponse
    try:
        # 获取文件哈希值
        response = requests.get(UPDATE_SERVER_URL + "/files/hashlist/diff/" + const.OPENCHAT_VERSION,verify=False)
        path_list = json.loads(response.content)
            
        file_list = []
        # 下载文件
        os.makedirs(DOWNLOAD_DIR,exist_ok=True)
        file_list  = await download_files_from_server(UPDATE_SERVER_URL,path_list,DOWNLOAD_DIR)
        
    except Exception as e:
        result.flag = True
        result.errMsg = status.ERROR.errmsg
        result.errCode = status.ERROR.code
        result.resData = str(e)
        return result
    else:
        result.flag = True
        result.errMsg = status.OK.errmsg
        result.errCode = status.OK.code
        result.resData = json.dumps(file_list)
        return result
    
@router.get('/progress', response_model=DownloadStatusResponse)
def get_update_progress():
    result = DownloadStatusResponse
    progress = gvar.get_update_progress()

    result.flag = True
    result.errMsg = status.OK.errmsg
    result.errCode = status.OK.code
    result.resData = json.dumps({"progress":progress})
    download_task.clear()
    return result
    
@router.get('/exit_immediately')
async def exit_immediately():
    import subprocess
    from pkg.app.app import window
    if constants.SYSTEM == constants.WINDOWS :
        # 清理一下服务器上压缩的文件
        db_query = alchemytool.select_user_by_name('hello')
        response = requests.get(UPDATE_SERVER_URL + "/remove_file/" + db_query.user_id,verify=False)
        # 应用退出
        window.destroy()
        # 子进程启动文件迁移命令
        username = os.getlogin()
        subprocess.run(['icacls','move_files.bat','/grant',f"{username}:F"]) # 修改文件权限
        subprocess.Popen('move_files.bat',stdout=subprocess.DEVNULL)
    else:
        # 获取当前运行目录（打包后就是 MacOS/）
        base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()

        # 脚本路径（与可执行文件同级）
        script_path = os.path.join(base_path, 'update.sh')

        # ✅ 先给脚本加执行权限（冗余处理，也安全）
        subprocess.run(['chmod', '+x', script_path], check=False)

        # ✅ 先启动更新脚本，在独立会话中运行（不受主进程关闭影响）
        subprocess.Popen(
            ['bash', script_path],
            cwd=base_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # ✅ 脱离当前 app 控制
        )

        # ✅ 最后销毁窗口（退出主程序）
        window.destroy()


@router.get('/exit_later',response_model=UpdateResponse)
async def exit_immediately():
    pass



# @router.get('/data_migration',response_model=UpdateResponse)
# async def data_migration():
#     result = UpdateResponse
#     user_home_path = os.path.expanduser('~')
#     db_path = os.path.join(user_home_path,const.OPENCHAT_CACHEPATH)
#     if os.path.exists(os.path.join(db_path,'openchat_old.db')):
#         log.info("存在旧版本openchat_old.db")
#         import pkg.database.update_sql as update_sql
#         # migrate_result = await update_sql.migrate()
#         migrate_result = update_sql.migrate()
#         if migrate_result:
#             log.info("迁移成功")
#             # 将openchat_old.db 重命名
#             import time
#             date = time.strftime("%Y%m%d_%H-%M-%S")
#             os.rename(os.path.join(db_path,'openchat_old.db'), os.path.join(db_path,'openchat_old_' + str(date) + '.db'))
#             result.flag = True
#             result.errMsg = status.OK.errmsg
#             result.errCode = status.OK.code
#             result.resData = "数据迁移成功"
#         else:
#             log.error("迁移失败")
#             result.flag = True
#             result.errMsg = status.ERROR.errmsg
#             result.errCode = status.ERROR.code
#             result.resData = "数据迁移失败"
#     else:
#         log.info("不存在旧版本openchat_old.db")
#         result.flag = True
#         result.errMsg = status.ERROR.errmsg
#         result.errCode = status.ERROR.code
#         result.resData = "不存在旧版本openchat_old.db"
#     return result



def data_migration_immediately():
    try:
        log.info("数据迁移")
        user_home_path = os.path.expanduser('~')
        db_path = os.path.join(user_home_path,const.OPENCHAT_CACHEPATH)
        if os.path.exists(os.path.join(db_path,'openchat_old.db')):
            log.info("存在旧版本openchat_old.db")
            import pkg.database.update_sql as update_sql
            migrate_result = update_sql.migrate()
            if migrate_result:
                log.info("迁移成功")
                # 将openchat_old.db 重命名
                import time
                date = time.strftime("%Y%m%d_%H-%M-%S")
                os.rename(os.path.join(db_path,'openchat_old.db'), os.path.join(db_path,'openchat_old_' + str(date) + '.db'))
                return True
            else:
                log.error("迁移失败")
                return False
        else:
            log.info("不存在旧版本openchat_old.db")
        return True
    except Exception as e:
        log.error(f"data_migration_immediately error: {e}")
        
@router.get('/version/list',response_model=UpdateResponse)
def check_update():
    result = UpdateResponse
    try:
        response = requests.get(UPDATE_SERVER_URL + "/version/list",verify=False)
        current_version_info = json.loads(response.content)
        if response:
            log.info(f"版本列表返回")
            result.flag = True
            result.errMsg = status.OK.errmsg
            result.errCode = status.OK.code
            result.resData = json.dumps(current_version_info)
            return result
        else:
            log.info(f"无版本")
            result.flag = True
            result.errMsg = status.OK.errmsg
            result.errCode = status.OK.code
            result.resData = None
            return result
            
    except Exception as e:
        result.flag = False
        result.errMsg = status.ERROR.errmsg
        result.errCode = status.ERROR.code
        result.resData = str(e)
        return result
    
@router.post('/version/update',response_model=UpdateResponse)
async def update_version(req:Request,version_info:UpdateReceive):
    result = UpdateResponse
    print(f"更新{version_info}")
    try:
        log.info(version_info.model_dump_json())
        response = requests.post(UPDATE_SERVER_URL + "/version/update",json=json.loads(version_info.model_dump_json()),verify=False)
        # current_version_info = json.loads(response.content)
        log.info(f"{response.content},{type(response.content)}")
        response_content = json.loads(response.content)
        log.info(f"{response_content},{type(response_content)}")
        if response_content['result']:
            log.info(f"版本列表返回")
            result.flag = True
            result.errMsg = status.OK.errmsg
            result.errCode = status.OK.code
            result.resData = response_content['msg']
            return result
        else:
            log.info(f"无版本")
            result.flag = False
            result.errMsg = status.OK.errmsg
            result.errCode = status.OK.code
            result.resData = response_content['msg']
            return result
            
    except Exception as e:
        log.error(f"{str(e)}")
        result.flag = False
        result.errMsg = status.ERROR.errmsg
        result.errCode = status.ERROR.code
        result.resData = str(e)
        return result

@router.post('/version/delete',response_model=UpdateResponse)
async def delete_version(req:Request,version_info:DeleteReceive):
    result = UpdateResponse
    try:
        log.info(version_info.model_dump_json())
        response = requests.post(UPDATE_SERVER_URL + "/version/delete",json=json.loads(version_info.model_dump_json()),verify=False)
        # current_version_info = json.loads(response.content)
        response_content = json.loads(response.content)
        if response_content['result']:
            log.info(f"删除成功")
            result.flag = True
            result.errMsg = status.OK.errmsg
            result.errCode = status.OK.code
            result.resData = response_content['msg']
            return result
        else:
            log.info(f"删除失败")
            result.flag = False
            result.errMsg = status.OK.errmsg
            result.errCode = status.OK.code
            result.resData = response_content['msg']
            return result
            
    except Exception as e:
        log.error(f"{str(e)}")
        result.flag = False
        result.errMsg = status.ERROR.errmsg
        result.errCode = status.ERROR.code
        result.resData = str(e)
        return result

@router.post('/version/insert',response_model=UpdateResponse)
async def insert_version(req:Request,version_info:UpdateReceive):
    result = UpdateResponse
    print(f"插入：{version_info}")
    try:
        log.info(version_info.model_dump_json())
        response = requests.post(UPDATE_SERVER_URL + "/version/insert",json=json.loads(version_info.model_dump_json()),verify=False)
        # current_version_info = json.loads(response.content)
        response_content = json.loads(response.content)
        if response_content['result']:
            log.info(f"插入成功")
            result.flag = True
            result.errMsg = status.OK.errmsg
            result.errCode = status.OK.code
            result.resData = response_content['msg']
            return result
        else:
            log.info(f"插入失败")
            result.flag = False
            result.errMsg = status.OK.errmsg
            result.errCode = status.OK.code
            result.resData = response_content['msg']
            return result
            
    except Exception as e:
        log.error(f"{str(e)}")
        result.flag = False
        result.errMsg = status.ERROR.errmsg
        result.errCode = status.ERROR.code
        result.resData = str(e)
        return result