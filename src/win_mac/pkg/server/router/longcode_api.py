from fastapi import APIRouter, UploadFile, Depends

from ...projectvar import Projectvar
from ...projectvar import constants as const
from ..depends import get_headers
from ...server import schemas as server_schemas
from ...projectvar.statuscode import StatusCodeEnum as status

import os
import shutil
import zipfile
import chardet
    
gvar = Projectvar()

router = APIRouter(
    prefix = "/longcode",
    tags=["longcode"],
    responses={404: {"description": "Not found"}},
)

def compose_repo(input_path, userid):
    if os.path.exists(input_path):
        if os.path.isfile(input_path):
            # 输入不是文件夹，是一个文件
            return False
    else:
        # 路径不存在
        return False
    
    norm_path = os.path.normpath(input_path)
    head_path, repo_name = os.path.split(norm_path)

    # 组装仓库py文件
    # text = '<repo_name>' + repo_name
    text = ''
    for root, _, files in os.walk(norm_path):
        for file in files:
            if file.endswith('.py'):
                try:
                    with open(os.path.join(root, file), 'rb') as f:
                        rawdata = f.read()          
                        result = chardet.detect(rawdata)
                        content = rawdata.decode(result['encoding'])
                        text += content.replace('\n', '<n>') + '<n>'
                except Exception as e:
                    continue
    
    # py文件组装失败
    if text == '':
        return False            

    # 删除原始文件
    try:
        shutil.rmtree(norm_path)
    except FileNotFoundError:
        # 删除文件夹失败
        return False

    try:
        # 写入文件
        with open(os.path.join(head_path, userid+'_longcode.txt'), 'w') as o_file:
            o_file.write(text)
    except:
        return False

    return True

@router.post("/upload", response_model=server_schemas.CommonResponse)
async def upload(file: UploadFile, headers=Depends(get_headers)):
    res = server_schemas.CommonResponse
    userid = headers[const.HTTP_HEADER_USER_ID]
    savePath = os.path.join(gvar.get_cache_path(), userid)
    if not os.path.exists(savePath):
        os.mkdir(savePath)
        
    save_file = os.path.join(savePath, file.filename)
    content = await file.read()
    with open(save_file, 'wb') as fb:
        fb.write(content)
    
    with zipfile.ZipFile(save_file, 'r') as zip_ref:
        zip_ref.extractall(savePath)
    
    os.remove(save_file)
    
    if compose_repo(savePath, userid):
        res.errCode = status.OK.code
        res.errMsg = status.OK.errmsg
        res.flag = True
    else:
        res.errCode = status.ERROR.code
        res.errMsg = status.ERROR.errmsg
        res.flag = True

    return res

@router.post("/clean", response_model= server_schemas.CommonResponse)
async def clean(headers=Depends(get_headers)):
    res = server_schemas.CommonResponse
    userid = headers[const.HTTP_HEADER_USER_ID]
    longcode_file = os.path.join(gvar.get_cache_path(), userid) + "_longcode.txt"
    os.remove(longcode_file)
    res.flag = True
    res.errCode = status.OK.code
    res.errMsg = status.OK.errmsg
    return res