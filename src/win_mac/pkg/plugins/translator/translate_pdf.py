import os
import shutil
from pathlib import Path
from pkg.plugins.translator.pdf2zh.high_level import translate
from pkg.server.process import process_translate
from pkg.projectvar import Projectvar
from pkg.projectvar import constants as consts
from pkg.server.process import process_setting

import fitz
from pkg.plugins.translator import pdf_ocr
from pkg.plugins.translator.base_translator import (
    BaseTranslator,
    OllamaPDFTranslator,
    OpenAIPDFTranslator,
    
)
from pkg.logger import Log
import requests
import cgi

log = Log()
gvar = Projectvar()

ocr_language_map ={
    "English":'eng',
    "Chinese":'chi_sim',
    "Japanese":'jpn',
    "Korean":'kor',
    "French": "fra",
    }

ocr_language_paddle_map ={
    "English":'en',
    "Chinese":'ch',
    "Japanese":'japan',
    "Korean":'korean ',
    "French": "french",
    }

service_map: dict[str, BaseTranslator] = {
    "Ollama": OllamaPDFTranslator,
    "OpenAI": OpenAIPDFTranslator,
}
lang_map = {
    "Chinese": "zh",
    "English": "en",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Korean": "ko",
    "Russian": "ru",
    "Spanish": "es",
    "Italian": "it",
}
page_map = {
    "All": None,
    "First": [0],
    "First 5 pages": list(range(0, 5)),
}

flag_demo = False
if os.getenv("PDF2ZH_DEMO"):
    flag_demo = True
    service_map = {
        "Ollama": OllamaPDFTranslator,
    }
    page_map = {
        "First": [0],
        "First 20 pages": list(range(0, 20)),
    }
    client_key = os.getenv("PDF2ZH_CLIENT_KEY")
    server_key = os.getenv("PDF2ZH_SERVER_KEY")


def verify_recaptcha(response):
    recaptcha_url = "https://www.google.com/recaptcha/api/siteverify"
    log.info("reCAPTCHA", server_key, response)
    data = {"secret": server_key, "response": response}
    result = requests.post(recaptcha_url, data=data).json()
    log.info("reCAPTCHA", result.get("success"))
    return result.get("success")


def download_with_limit(url, save_path, size_limit):
    chunk_size = 1024
    total_size = 0
    with requests.get(url, stream=True, timeout=10) as response:
        response.raise_for_status()
        content = response.headers.get("Content-Disposition")
        try:  # filename from header
            _, params = cgi.parse_header(content)
            filename = params["filename"]
        except Exception:  # filename from url
            filename = os.path.basename(url)
        with open(save_path / filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                total_size += len(chunk)
                if size_limit and total_size > size_limit:
                    raise "Exceeds file size limit"
                file.write(chunk)
    return save_path / filename


# 判断pdf是否能读取出内容
def is_text_based_pdf(filename):
    doc = fitz.open(filename)
    for page in doc:
        if page.get_text(): 
            # log.info(page.get_text())
            return True
    return False

def translate_file(
    file_id,
    file_type,
    file_input,
    service,
    model,
    link_input,
    lang_from,
    lang_to,
    page_range,
    enhance=False,
    url = "",
    api_key = None,
    db = None,
    *envs,
):
    if consts.SYSTEM == consts.WINDOWS:
        output = Path(os.path.join("translation",file_id))
    else:
        global_path = process_setting.get_system_default_path().config_value
        output = Path(os.path.join(global_path,"translation",file_id))
    output.mkdir(parents=True, exist_ok=True)
    
    process_translate.update_translate_item(db, file_id,status=0,porcess=0,base_lang=lang_from,target_lang=lang_to)
    process_translate.update_translate_finalpath(db=db,fileid=file_id,translated_path="",status=0,translated_time="")
    #执行ocr
    if not is_text_based_pdf(file_input) or enhance:
        process_translate.set_ocr_status(db,file_id,True)
        log.info(f"{file_input} 执行OCR")
        log.info(f"ocr_language_map[lang_from]:{ocr_language_map[lang_from]}")
        lang = ocr_language_map[lang_from]
        file_input = pdf_ocr.trans_(file_input,lang,output,file_id,db)
        process_translate.set_ocr_status(db,file_id,False)
        if file_input == '': # OCR时终止进程
            translating_file_list = gvar.get_needstop()
            if file_id in translating_file_list:
                log.info("pdf清空翻译状态")
                # 重置状态
                process_translate.set_ocr_status(db,file_id,False)
                process_translate.set_ocr_process_item(db,file_id,0)
                process_translate.update_translate_item(
                        db = db,
                        fileid = file_id,
                        status = -1,
                        porcess = 0,
                        base_lang = lang_from,
                        target_lang = lang_to,
                        translated_time = ''
                    )
                # 移除正在翻译的列表
                gvar.delete_needstop(file_id)
                return ""
  
    if file_type == "File":
        if not file_input:
            Log.info("No input.原因是ocr时退出")
            return ''
        # 默认已上传成功
        file_path = file_input
        # file_path = shutil.copy(file_input, output) # 文件保存至此的路径下
    else:
        if not link_input:
            raise "No input"
        file_path = download_with_limit(
            link_input,
            output,
            5 * 1024 * 1024 if flag_demo else None,
        )
    
    filename = os.path.splitext(os.path.basename(file_path))[0]
    # file_raw = output / f"{filename}.pdf"
    # 执行翻译的文件名
    file_raw = file_path
    file_mono = output / f"{filename}_trans.pdf"
    
    # 文件写入数据库
    
    translator = service_map[service]
    selected_page = page_map[page_range]
    lang_from = lang_map[lang_from]
    lang_to = lang_map[lang_to]

    log.info(f"Files before translation: {os.listdir(output)}")

    param = {
        "files": [str(file_raw)],
        "pages": selected_page,
        "lang_in": lang_from,
        "lang_out": lang_to,
        "service": f"{translator.name}",
        "output": output,
        "thread": 4,
        "callback": "",
        "model":model,
        "url":url,
        "api_key":api_key,
        "file_id":file_id,
        "db":db,
    }
    log.info(f"param:{param}")
    process_translate.update_translate_item(db, file_id,status=0,porcess=0,translated_path=str(file_mono),base_lang=lang_from,target_lang=lang_to)
    for full_stream, temp_stream in translate(**param):
        translating_file_list = gvar.get_needstop()
        if file_id in translating_file_list: # 翻译时终止线程
            log.info("终止pdf翻译")
            break
        log.info(f"Files after translation: {os.listdir(output)}")
        # yield str(file_mono)
        # yield str(file_mono), temp_stream
    
    # 清空翻译状态
    if file_id in translating_file_list:
        log.info("pdf清空翻译状态")
        # 重置状态
        process_translate.set_ocr_status(db,file_id,False)
        process_translate.set_ocr_process_item(db,file_id,0)
        process_translate.update_translate_item(
                db = db,
                fileid = file_id,
                status = -1,
                porcess = 0,
                base_lang = lang_from,
                target_lang = lang_to,
                translated_time = ''
            )
        # 移除正在翻译的列表
        gvar.delete_needstop(file_id)

    return str(file_mono)