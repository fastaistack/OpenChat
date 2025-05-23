from fastapi import APIRouter,Request,Depends,UploadFile, File
from pkg.plugins.translator.translate_text import translate_text
from pkg.plugins.translator import translate_pdf
from pkg.plugins.translator.translate_doc import translate_file as translate_doc_file
from pkg.plugins.translator.translate_txt import translate_txt
from ...projectvar import Projectvar
from ...projectvar.statuscode import StatusCodeEnum as status
from pkg.server import schemas as server_schemas
from typing import Union,List,Dict
from pkg.database import crud
from sqlalchemy.orm import Session
import os
import io
from pkg.server.process import process_setting
from pkg.logger import Log
from fastapi.responses import StreamingResponse
import uuid
from datetime import datetime
from pkg.server.process import process_translate
import time
import datetime
import shutil
import functools
from pkg.plugins.translator.utils import convert_docx_first_page_to_image,txt_to_image,pdf_first_page_to_image,image_to_base64
import fitz
from pymupdf import Font, Document
from concurrent.futures import ThreadPoolExecutor

t = ThreadPoolExecutor(max_workers=1)
def get_username_info(headers):
    user_name = ""
    for header in headers.raw:
        if header[0] == "user-name":
            user_name = header[1]
            break
    return user_name
log = Log()

##翻译response
class TranslatedtextResponse(server_schemas.CommonResponse):
    resData: Union[str, None]

class TranslatedfileResponse(server_schemas.CommonResponse):
    resData: Union[str, None]

class TranslatedfileProgressResponse(server_schemas.CommonResponse):
    resData: Union[Dict, None]

class TranslatedfileStatusResponse(server_schemas.CommonResponse):
    resData: Union[Dict, None]

class TranslationfilehistoryResponse(server_schemas.CommonResponse):
    resData: Union[List, None]

class TranslationtexthistoryResponse(server_schemas.CommonResponse):
    resData: Union[List, None]

##术语表response
class GlossaryResponse(server_schemas.CommonResponse):
    resData: Union[str, None]

class GlossaryitemResponse(server_schemas.CommonResponse):
    resData: Union[List, None]

class GlossarywordResponse(server_schemas.CommonResponse):
    resData: Union[List, None]

gvar = Projectvar()

router = APIRouter(
    prefix = "/translator",
    tags=["translator"],
    responses={404: {"description": "Not found"}},
)

base_lang = ""
target_lang = ""
language_map = {
    "zh": "Chinese",
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
}

#翻译历史接口
@router.get("/file/history", response_model=TranslationfilehistoryResponse)
async def api_get_translate_file_history(req: Request,db: Session = Depends(crud.get_db)):
    username = get_username_info(req.headers)
    data = []
    file_list = process_translate.get_translate_item_list(db)
    if file_list:
        for item in file_list:
            data.append({
                "fileid":item.fileid,
                "file_name":item.file_name,
                "create_time":item.upload_time,
                "status":item.status,
                "ocr_status":item.ocr_status,
                "progress":item.process,
                "ocr_progress":item.ocr_process,
                "pic":item.pic
            })
        return TranslationfilehistoryResponse(
            flag = True,
            errMsg = status.OK.errmsg,
            errCode = status.OK.code,
            resData = data
        )
    else :
        return TranslationfilehistoryResponse(
            flag = True,
            errMsg = status.OK.errmsg,
            errCode = status.OK.code,
            resData = data
        )

@router.delete("/file/history/{fileid}/delete",response_model=TranslatedfileResponse)
async def api_delete_translate_file_history(req: Request,fileid:str,db: Session = Depends(crud.get_db)):
    if process_translate.delete_translate_item(db,fileid):
        if os.path.exists(os.path.join('translation',fileid)):
            shutil.rmtree(os.path.join('translation',fileid))
        return TranslatedfileResponse(
            flag = True,
            errMsg = status.OK.errmsg,
            errCode = status.OK.code,
            resData = "success"
        )
    else:
        return TranslatedfileResponse(
            flag = False,
            errMsg = status.OPENCHAT_BIZ_DATA_UPDATE_FAILED_ERROR.errmsg,
            errCode = status.OPENCHAT_BIZ_DATA_UPDATE_FAILED_ERROR.code,
            resData = "failed"
        )

@router.get('/file/history/{fileid}/export')
async def get_file_history_export(req: Request,fileid:str,db: Session = Depends(crud.get_db)):
    db_item = process_translate.get_translate_item(db,fileid)
    name = db_item.file_name
    file_local_path = db_item.translated_file_path
    if not os.path.exists(file_local_path):
        return StreamingResponse(io.BytesIO("find file error"))
    else:
        file_data = open(file_local_path, 'rb').read()
        return StreamingResponse(io.BytesIO(file_data),
                                 headers={ "Content-Type": 'application/octet-stream',
                                           "Content-Disposition": f"attachment; filename={name.encode('utf-8')}"})
@router.get("/file/translated/{fileid}/status",response_model=TranslatedfileStatusResponse)
async def api_get_translate_file_status(req: Request,fileid:str,db: Session = Depends(crud.get_db)):
    status_item = process_translate.get_translate_status_item(db,fileid)
    return TranslatedfileStatusResponse(
        flag = True,
        errMsg = status.OK.errmsg,
        errCode = status.OK.code,
        resData = {"status":status_item.status,
                   "ocr_status":status_item.ocr_status}
    )

@router.post("/file/translate/{fileid}/stop",response_model=TranslatedfileResponse)
async def api_stop_translate_file(req: Request,fileid:str,db: Session = Depends(crud.get_db)):
    db_item_status = process_translate.get_translate_status_item(db,fileid)
    if db_item_status.status == 0:
        gvar.set_needstop(fileid)
        process_translate.set_translate_status_item(db,fileid,2)
        process_translate.set_translate_process_item(db,fileid,0)
        process_translate.set_ocr_status(db,fileid,False)
        process_translate.set_ocr_process_item(db,fileid,0)
        for i,task in enumerate(tasks):
            if task['file_id'] == fileid:
                task['task'].cancel()
                tasks.remove(task)
                log.info(f"{task['file_id']}翻译线程关闭")
                break
        return TranslatedfileResponse(
            flag = True,
            errMsg = status.OK.errmsg,
            errCode = status.OK.code,
            resData = "success"
        )
    return TranslatedfileResponse(
        flag = True,
        errMsg = status.OK.errmsg,
        errCode = status.OK.code,
        resData = "failed"
    )

@router.post("/text", response_model=TranslatedtextResponse)
async def api_get_translate_text(req: Request,receive:dict,db: Session = Depends(crud.get_db)):
    global base_lang,target_lang
    base_lang = language_map.get(receive.get("source"))
    target_lang = language_map.get(receive.get("target"))
    result_text = translate_text(receive.get("text"),base_lang,target_lang)
    process_translate.create_translate_text_item(
        db=db,
        origin_text = receive.get("text"),
        transed_text = result_text,
        base_lang = base_lang,
        target_lang = target_lang,
        create_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    result = TranslatedtextResponse
    result.flag = True
    result.errMsg = status.OK.errmsg
    result.errCode = status.OK.code
    result.resData = result_text
    return result

@router.get("/text/result",response_model=TranslationtexthistoryResponse)
async def get_text_export(req: Request,db: Session = Depends(crud.get_db)):
    data = []
    file_list = process_translate.get_translate_text_item_list(db)
    for item in file_list:
        data.append({
            "id":item.id,
            "origin_text":item.origin_text,
            "transed_text":item.transed_text,
            "base_lang":item.base_lang,
            "target_lang":item.target_lang,
            "create_time":item.create_time
        })
    return TranslationtexthistoryResponse(
        flag = True,
        errMsg = status.OK.errmsg,
        errCode = status.OK.code,
        resData = data
    )

@router.delete("/text/result/{id}/delete",response_model=TranslatedfileResponse)
async def delete_text_export(req: Request,id:int,db: Session = Depends(crud.get_db)):
    process_translate.delete_translate_text_item(db,id)
    return TranslatedfileResponse(
        flag = True,
        errMsg = status.OK.errmsg,
        errCode = status.OK.code,
       resData = "success"
    )

@router.post("/base_target_lang",response_model=TranslatedfileResponse)
async def get_base_target_lang(req: Request,receive:dict):
    global base_lang,target_lang
    base_lang = language_map.get(receive.get("source"))
    target_lang = language_map.get(receive.get("target"))
    return TranslatedfileResponse(
        flag = True,
        errMsg = status.OK.errmsg,
        errCode = status.OK.code,
        resData = "success"
    )

@router.post("/file/upload",response_model=TranslatedfileResponse)
async def upload_translated_file(req: Request,files: UploadFile = File(...),db: Session = Depends(crud.get_db)):
    ##创建本地文件夹，保存文件，
    try:
        global_path = process_setting.get_system_default_path().config_value
        fileid = uuid.uuid1().hex
        file_local_path = os.path.join(global_path,"translation",fileid)
        if not os.path.exists(file_local_path):
            os.makedirs(file_local_path)
        with open(os.path.join(file_local_path, files.filename), 'wb') as f:
            f.write(files.file.read())
        
        filetype = files.filename.split('.')[-1]
        image_path = ""
        image_base64 = ""
        global base_lang,target_lang
        process_translate.create_translate_item(
            db = db,
            fileid = fileid,
            base_lang = base_lang,
            target_lang = target_lang,
            file_name = files.filename,
            source_file_path = os.path.join(file_local_path, files.filename),
            upload_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status = -1,
            process = 0.0,
            image_base64 = image_base64
        )
        if filetype == 'pdf':
            image_path = pdf_first_page_to_image(os.path.join(file_local_path, files.filename),output_image_path=os.path.join(file_local_path, files.filename.split('.')[0]+'.png'))
        elif filetype == 'docx':
            image_path = convert_docx_first_page_to_image(os.path.join(file_local_path, files.filename),output_image_path=os.path.join(file_local_path, files.filename.split('.')[0]+'.png'))
        elif filetype == 'txt':
            image_path = txt_to_image(os.path.join(file_local_path, files.filename),output_image_path=os.path.join(file_local_path, files.filename.split('.')[0]+'.png'))
        
        if image_path:
            image_base64 = image_to_base64(image_path)

        process_translate.update_translate_item_img(db,fileid,image_base64)

        return TranslatedfileResponse(
            flag = True,
            errMsg = status.OK.errmsg,
            errCode = status.OK.code,
            resData = fileid)
    except Exception as e:
        log.error(('[translation - file_upload] file upload error:{0}'.format(e)))
        return TranslatedfileResponse(
            flag = False,
            errMsg = status.UNKNOWN.errmsg,
            errCode = status.UNKNOWN.code,
            resData = "fail"
        )

@router.get("/file/{fileid}/name",response_model=TranslatedfileResponse)
async def get_file_name(req:Request,fileid:str,db:Session = Depends(crud.get_db)):
    db_translate_item = process_translate.get_translate_item(db,fileid)
    return TranslatedfileResponse(
        flag = True,
        errMsg = status.OK.errmsg,
        errCode = status.OK.code,
        resData = db_translate_item.file_name
    )

@router.post("/file/{fileid}/detail")
async def tobetranslated_file_detail(req:Request,fileid:str,db:Session = Depends(crud.get_db)):
    user = get_username_info(req.headers)
    db_translate_item = process_translate.get_translate_item(db,fileid)
    name = db_translate_item.file_name
    # global_path = process_setting.get_system_default_path().config_value
    # file_local_path = os.path.join(global_path,"translation")
    file_local_path = db_translate_item.source_file_path
    if not os.path.exists(file_local_path):
        return StreamingResponse(io.BytesIO("find file error"))
    else:
        file_data = open(file_local_path, 'rb').read()
        return StreamingResponse(io.BytesIO(file_data),
                                 headers={ "Content-Type": 'application/octet-stream',
                                           "Content-Disposition": f"attachment; filename={name.encode('utf-8')}"})

@router.post("/file/{fileid}/translated/detail")
async def translated_file_detail(req:Request,fileid:str,db:Session = Depends(crud.get_db)):
    user = get_username_info(req.headers)
    file_local_path = ""
    name = ""
    while True:
        db_translate_item = process_translate.get_translate_item(db,fileid)
        if db_translate_item.translated_file_path:
            name = db_translate_item.file_name
    # global_path = process_setting.get_system_default_path().config_value
    # file_local_path = os.path.join(global_path,"translation")
            file_local_path = db_translate_item.translated_file_path
            break
        else:
            continue
    file_data = open(file_local_path, 'rb').read()
    return StreamingResponse(io.BytesIO(file_data),
                                 headers={ "Content-Type": 'application/octet-stream',
                                           "Content-Disposition": f"attachment; filename={name.encode('utf-8')}"})

def translated_callback(future,db,file_id,status,porcess,base_lang,target_lang):
    try:
        result = future.result()
        log.info(f"result:{result}")
    except Exception as e:
        import traceback
        log.error(traceback.format_exc())
        log.error(f"translated_callback:{e}")
        # 重置状态
        process_translate.update_translate_item(db, file_id,status=status,porcess=porcess,base_lang=base_lang,target_lang=target_lang)
        process_translate.set_ocr_status(db, file_id,False)
        process_translate.set_ocr_process_item(db, file_id,0)
        # 删除当前任务
        translating_file_list = gvar.get_needstop()
        if file_id in translating_file_list:
            gvar.delete_needstop(file_id)
        log.info("翻译异常退出")

tasks = [] # 翻译列表

@router.get("/file/{file_id}/pdf/page/count")
async def get_pdf_page_count(req:Request,file_id:str,db:Session = Depends(crud.get_db)):
    item = process_translate.get_translate_item(db=db,fileid=file_id)
    with fitz.open(item.source_file_path) as pdf_document:
        page_count = pdf_document.page_count
    return TranslatedfileResponse(
                flag = True,
                errMsg = status.OK.errmsg,
                errCode = status.OK.code,
                resData = str(page_count)
            )
    
@router.get("/file/{file_id}/pdf/translated_page/{page_count}")
async def get_pdf_page_count(req:Request,file_id:str,page_count:str,db:Session = Depends(crud.get_db)):
    item = process_translate.get_translate_item(db=db,fileid=file_id)
    path = item.translated_file_path.split('.pdf')[0] + "_" + page_count + ".pdf"
    print(f"translated_page:{path}")
    name = item.file_name
    try:
        file_data = open(path, 'rb').read()
    except Exception as e:
        log.error(str(e))
        return StreamingResponse(None)
    return StreamingResponse(io.BytesIO(file_data),
                            headers={
                                "Content-Type": 'application/octet-stream',
                                "Content-Disposition": f"attachment; filename={name.encode('utf-8')}"})

@router.get("/file/{file_id}/pdf/source_page/{page_count}")
async def get_pdf_page_count(req:Request,file_id:str,page_count:str,db:Session = Depends(crud.get_db)):
    item = process_translate.get_translate_item(db=db,fileid=file_id)
    path = item.source_file_path
    name = item.file_name
    try:
        file_data = open(path, 'rb').read()
    except Exception as e:
        log.error(str(e))
        return StreamingResponse(None)
    doc_source = Document(stream=file_data) # 加载整个PDF文档
    fp = io.BytesIO() # 创建内存缓冲区
    doc_source.save(fp) # 将文档保存在缓冲区
    doc_page = Document() # 创建新的空白文档
    doc_page.insert_pdf(doc_source,from_page=int(page_count),to_page=int(page_count)) # 插入指定页码的内容
    
    return StreamingResponse(io.BytesIO(doc_page.write(deflate=1)),
                                headers={
                                    "Content-Type": 'application/octet-stream',
                                    "Content-Disposition": f"attachment; filename={name.encode('utf-8')}"})

@router.post("/file/{fileid}/translate")
async def translate_allfile(req:Request,fileid:str,db:Session = Depends(crud.get_db)):
    try:
        db_translate_item = process_translate.get_translate_item(db,fileid)
        name = db_translate_item.file_name
        file_local_path = db_translate_item.source_file_path
        if not os.path.exists(file_local_path):
            return StreamingResponse(io.BytesIO("find file error"))
        else:
            ##根据文件类型判断使用哪个翻译器
            file_type = name.split('.')[-1]
            global base_lang,target_lang
            process_translate.update_translate_item(db, fileid,status=0,porcess=0,base_lang=base_lang,target_lang=target_lang)
            process_translate.set_ocr_status(db, fileid,False)
            process_translate.set_ocr_process_item(db, fileid,0)
            if file_type == 'docx':
                result = t.submit(translate_doc_file,input_file = os.path.join(file_local_path),base_lang = base_lang, target_language=target_lang,fileid=fileid)
            elif file_type == 'pdf':
                # OpenAI Ollama
                model_info = gvar.get_model_info()
                if model_info['api_key'] == 'ollama':
                    url = model_info['url'] + '/v1'
                else:
                    url = model_info['url']

                result = t.submit(translate_pdf.translate_file,
                                file_id = fileid,
                                file_type="File",
                                file_input=file_local_path,
                                link_input="",
                                service = "OpenAI",
                                model = model_info['model_selected'],
                                lang_from=base_lang,
                                lang_to=target_lang,
                                page_range="All",
                                url = url,
                                api_key = model_info['api_key'],
                                db = db,
                                enhance=False)
                
            elif file_type == 'txt':
                result = t.submit(translate_txt,input_file = os.path.join(file_local_path), base_lang = base_lang,target_language=target_lang,fileid=fileid)

            result.add_done_callback(functools.partial(translated_callback,db=db,file_id=fileid,status=-2,porcess=0,base_lang=base_lang,target_lang=target_lang))
            tasks.append({"file_id":fileid,"task":result})
            return TranslatedfileResponse(
                flag = True,
                errMsg = status.OK.errmsg,
                errCode = status.OK.code,
                resData = "success"
            )
    except Exception as e:
        log.error(f"translate_allfile:{str(e)}")
        process_translate.update_translate_item(db, fileid,status=-1,porcess=0,base_lang=base_lang,target_lang=target_lang)
        process_translate.set_ocr_status(db, fileid,False)
        process_translate.set_ocr_process_item(db, fileid,0)
        return TranslatedfileResponse(
                flag = False,
                errMsg = status.OPENCHAT_TRNASLATED_ERROR.errmsg,
                errCode = status.ERROR.code,
                resData = f"{e}"
            )

@router.post("/file/history/{id}/export",response_model=server_schemas.CommonResponse)
async def translated_file_export(req:Request,id:str,path:str,db:Session = Depends(crud.get_db)):
    """
    id:file_id
    path:save_path
    """
    response = server_schemas.CommonResponse
    result = process_translate.get_translate_item(db,id)
    translated_path = result.translated_file_path
    os.makedirs(path,exist_ok=True)
    import shutil
    save_path = shutil.copy(translated_path,path)
    if save_path:
        response.flag = True
        response.errMsg = status.OK.errmsg
        response.errCode = status.OK.code
        response.resData = "success"
    else:
        response.flag = False
        response.errMsg = status.ERROR.errmsg
        response.errCode = status.ErrOR.code
        response.resData = "failure"
    return response

## 术语表接口
@router.post("/glossary/open",response_model=GlossaryResponse)
async def open_glossary(req: Request,receive:dict):
    if receive.get('state','close') == "open":
        gvar.set_glossary(receive.get('id',-1))
        print('gvar.set_glossary(id)',gvar.get_glossary())
        return GlossaryResponse(
            flag = True,
            errMsg=status.OK.errmsg,
            errCode=status.OK.code,
            resData="success")
    else:
        gvar.set_glossary(-1)
        print('gvar.set_glossary(id)',gvar.get_glossary())
        return GlossaryResponse(
            flag = True,
            errMsg=status.OK.errmsg,
            errCode=status.OK.code,
            resData="success")



@router.post("/glossary/item/create", response_model=GlossaryResponse)
async def create_glossary_item(req: Request, receive:dict, db: Session = Depends(crud.get_db)):
    name = receive.get("name")
    field = receive.get("field")
    total_num_words = receive.get("total_num_words",0)
    result = process_translate.create_glossary_item(db,total_num_words,name,field)
    if result:
        response = GlossaryResponse
        response.flag = True
        response.errMsg = status.OK.errmsg
        response.errCode = status.OK.code
        response.resData = "success"
        return response
    else :
        response = GlossaryResponse
        response.flag = False
        response.errMsg = status.OPENCHAT_BIZ_DATA_CREATE_FAILED_ERROR.errmsg
        response.errCode = status.OPENCHAT_BIZ_DATA_CREATE_FAILED_ERROR.code
        response.resData = "failed"
        return response
    
@router.get("/glossary/item/list",response_model=GlossaryitemResponse)
async def get_glossary_item_list(req: Request, db: Session = Depends(crud.get_db)):
    glossary_item_list = process_translate.get_glossary_item_list(db)
    data = []
    if glossary_item_list:
        for item in glossary_item_list:
            data.append({
                "id":item.id,
                "name":item.name,
                "field":item.field,
                "total_num_words":item.total_num_words
            })
    return GlossaryitemResponse(
        flag = True,
        errMsg=status.OK.errmsg,
        errCode=status.OK.code,
        resData=data)

@router.post("/glossary/item/update/{id}",response_model=GlossaryResponse)
async def update_glossary_item(req: Request, id:int,total_num_words:int,db: Session = Depends(crud.get_db)):

    result = process_translate.set_glossary_item(db,id,total_num_words)
    if result:
        return GlossaryResponse(
        flag = True,
        errMsg=status.OK.errmsg,
        errCode=status.OK.code,
        resData="success")
    else:
        return GlossaryResponse(
        flag = False,
        errMsg=status.OPENCHAT_BIZ_DATA_UPDATE_FAILED_ERROR.errmsg,
        errCode=status.OPENCHAT_BIZ_DATA_UPDATE_FAILED_ERROR.code,
        resData="failed")
    
@router.delete("/glossary/item/delete/{id}",response_model=GlossaryResponse)
async def delete_glossary_item(req: Request, id:int ,db:Session = Depends(crud.get_db)):
    result = process_translate.delete_glossary_item(db,id)
    if result:
        return GlossaryResponse(
        flag=True,
        errMsg=status.OK.errmsg,
        errCode=status.OK.code,
        resData="success")
    else:
        return GlossaryResponse(
        flag = False,
        errMsg=status.OPENCHAT_BIZ_DATA_UPDATE_FAILED_ERROR.errmsg,
        errCode=status.OPENCHAT_BIZ_DATA_UPDATE_FAILED_ERROR.code,
        resData="failed"
        )
    
@router.post("/glossary/word/create",response_model=GlossaryResponse)
async def create_glossary_word(req:Request,receive:dict,db:Session = Depends(crud.get_db)):
    result = process_translate.create_glossary_word(
        db = db,
        base_lang = receive.get("base_lang"),
        base_language = receive.get("base_language"),
        target_lang = receive.get("target_lang"),
        target_language = receive.get("target_language"),
        glossary_id = receive.get("glossary_id")
    )
    if result:
        return GlossaryResponse(
        flag = True,
        errMsg=status.OK.errmsg,
        errCode=status.OK.code,
        resData="success")
    else:
        return GlossaryResponse(
        flag = False,
        errMsg=status.OPENCHAT_BIZ_DATA_CREATE_FAILED_ERROR.errmsg,
        errCode=status.OPENCHAT_BIZ_DATA_CREATE_FAILED_ERROR.code,
        resData="failed"
        )
    
@router.get("/glossary/word/list/{glossary_id}",response_model=GlossarywordResponse)
async def get_glossary_word_list(req:Request,glossary_id:str,db: Session = Depends(crud.get_db)):
    db_glossary_word_list = process_translate.get_glossary_word_list(db,glossary_id)
    data = []
    for item in db_glossary_word_list:
        data.append({
            "id":item.id,
            "base_language":item.base_language,
            "base_lang":item.base_lang,
            "target_language":item.target_language,
            "target_lang":item.target_lang,
            "target_language":item.target_language,
            "target_lang":item.target_lang,
        })
    return GlossarywordResponse(
        flag = True,
        errMsg=status.OK.errmsg,
        errCode=status.OK.code,
        resData=data
    )

@router.get("/glossary/word/index/{id}", response_model=GlossarywordResponse)
async def get_glossary_word(req: Request,id:int,base_language:str,db:Session = Depends(crud.get_db)):
    data = []
    glossary_word = process_translate.get_glossary_word(db,base_language)
    for item in glossary_word:
        data.append({
            "glossary_id":item.glossary_id,
            "id":item.id,
            "base_lang":item.base_lang,
            "base_language":item.base_language,
            "target_lang":item.target_lang,
            "target_language":item.target_language
        })
    if glossary_word:
        return GlossarywordResponse(
            flag = True,
            errMsg=status.OK.errmsg,
            errCode=status.OK.code,
            resData=data
        )
    else:
        return GlossarywordResponse(
            flag = False,
            errMsg=status.DB_NOTFOUND_ERR.errmsg,
            errCode=status.DB_NOTFOUND_ERR.code,
            resData=data
        )


@router.delete("/glossary/word/delete/{id}", response_model=GlossaryResponse)
async def delete_glossary_word(req:Request,id:int,db:Session = Depends(crud.get_db)):
    result = process_translate.delete_glossary_word(db,id)
    if result:
        return GlossaryResponse(
            flag = True,
            errMsg=status.OK.errmsg,
            errCode=status.OK.code,
            resData="success"
        )
    else:
        return GlossaryResponse(
            flag = False,
            errMsg=status.DB_NOTFOUND_ERR.errmsg,
            errCode=status.DB_NOTFOUND_ERR.code,
            resData="failed"
        )

@router.post("/glossary/word/update",response_model=GlossaryResponse)
async def glossary_word_update(req:Request, receive:dict,db:Session = Depends(crud.get_db)):

    result = process_translate.set_glossary_word(
        db=db,
        base_lang = receive.get("base_lang"),
        base_language = receive.get("base_language"),
        target_lang = receive.get("target_lang"),
        target_language = receive.get("target_language"),
        id = receive.get("id")
    )

    if result:
        return GlossaryResponse(
            flag = True,
            errMsg=status.OK.errmsg,
            errCode=status.OK.code,
            resData="success"
        )
    else:
        return GlossaryResponse(
            flag = False,
            errMsg=status.DB_NOTFOUND_ERR.errmsg,
            errCode=status.DB_NOTFOUND_ERR.code,
            resData="failed"
        )
    

##进度条接口

@router.get("/file/progress/{fileid}",response_model=TranslatedfileProgressResponse)
async def get_translate_progress(req:Request,fileid:str,db:Session = Depends(crud.get_db)):
    result = process_translate.get_translateitem_progress(db,fileid)
    if result:
        return TranslatedfileProgressResponse(
            flag = True,
            errMsg=status.OK.errmsg,
            errCode=status.OK.code,
            resData={
                "process":result.process,
                "ocr_process":result.ocr_process
            }
        )
    else :
        return TranslatedfileProgressResponse(
            flag = True,
            errMsg=status.OK.errmsg,
            errCode=status.OK.code,
            resData=result
        )
