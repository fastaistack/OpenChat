"""Functions that can be used for the most common use-cases for pdf2zh.six"""

from typing import BinaryIO
import numpy as np
import tqdm
import sys
from pymupdf import Font, Document
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pkg.plugins.translator.pdf2zh.converter import TranslateConverter
from pkg.plugins.translator.pdf2zh.pdfinterp import PDFPageInterpreterEx
from pkg.plugins.translator.pdf2zh.doclayout import DocLayoutModel
from pathlib import Path
from typing import Any, List, Optional
import urllib.request
import requests
import tempfile
import os
import io
from pkg.logger import Log
from pkg.server.process import process_translate
from pkg.database import crud
from sqlalchemy.orm import Session


log = Log()

doclayout_model = DocLayoutModel.load_available()

resfont_map = {
    "zh-cn": "china-ss",
    "zh-tw": "china-ts",
    "zh-hans": "china-ss",
    "zh-hant": "china-ts",
    "zh": "china-ss",
    "ja": "japan-s",
    "ko": "korea-s",
}

noto_list = [
    "am",  # Amharic
    "ar",  # Arabic
    "bn",  # Bengali
    "bg",  # Bulgarian
    "chr",  # Cherokee
    "el",  # Greek
    "gu",  # Gujarati
    "iw",  # Hebrew
    "hi",  # Hindi
    # "ja",  # Japanese
    "kn",  # Kannada
    # "ko",  # Korean
    "ml",  # Malayalam
    "mr",  # Marathi
    "ru",  # Russian
    "sr",  # Serbian
    # "zh-cn",# SC
    "ta",  # Tamil
    "te",  # Telugu
    "th",  # Thai
    # "zh-tw",# TC
    "ur",  # Urdu
    "uk",  # Ukrainian
]


def check_files(files: List[str]) -> List[str]:
    files = [
        f for f in files if not f.startswith("http://")
    ]  # exclude online files, http
    files = [
        f for f in files if not f.startswith("https://")
    ]  # exclude online files, https
    missing_files = [file for file in files if not os.path.exists(file)]
    return missing_files


def do_rectangles_overlap(texts_box,page_box): 
    # 去除yolobox中覆盖率高的面积较大的box
    for i,box in enumerate(texts_box):
        if box:
            x1,y1,x2,y2 = box['xyxy']
            for j,box_compare in enumerate(texts_box):
                if box_compare and i!=j :
                    x3,y3,x4,y4 = box_compare['xyxy']
                    if (x2 > x3) and (x1 < x4) and (y2 > y3) and (y1 < y4):
                        area_i = (x2-x1)*(y2-y1)
                        area_j = (x4-x3)*(y4-y3)
                        
                        # 计算覆盖区域的左上角和右下角坐标
                        overlap_x1 = max(x1, x3)
                        overlap_y1 = max(y1, y3)
                        overlap_x2 = min(x2, x4)
                        overlap_y2 = min(y2, y4)
                        width = overlap_x2 - overlap_x1
                        height = overlap_y2 - overlap_y1
                        overlap_area = width * height
                        if overlap_area >= (min(area_i,area_j))/2:
                            # 标识遮挡的位置太大
                            if area_i > area_j: # 将i换成j
                                if not texts_box[i]['remove']:
                                    texts_box[i]['remove'] = True
                                    texts_box[i]['change'] = j
                            else: # 将j换成i
                                if not texts_box[j]['remove']:
                                    texts_box[j]['remove'] = True
                                    texts_box[j]['change'] = i
                        
    for i, box in enumerate(texts_box):
        if box:
            if box['remove']:
                x0,y0,x1,y1 = texts_box[box['change']]['xyxy']
                page_box[y0:y1, x0:x1] = box['change'] # 将需要替换的位置，替换为需要替换的数值
                texts_box[i] = None
    return texts_box

def translate_patch(
    inf: BinaryIO,
    pages: Optional[list[int]] = None,
    vfont: str = "",
    vchar: str = "",
    thread: int = 0,
    doc_zh: Document = None,
    lang_in: str = "",
    lang_out: str = "",
    service: str = "",
    model: str = "",
    resfont: str = "",
    noto: Font = None,
    callback: object = None,
    url : str = "",
    api_key : str = None,
    file_id:str = '',
    db:Session = None,
    **kwarg: Any,
):
    if pages:
        total_pages = len(pages)
    else:
        total_pages = doc_zh.page_count
    rsrcmgr = PDFResourceManager()
    layout = {}
    device = TranslateConverter(
        rsrcmgr, vfont, vchar, thread, layout, lang_in, lang_out, service, model, resfont, noto, url, api_key, file_id, total_pages,db
    )

    assert device is not None
    obj_patch = {}
    interpreter = PDFPageInterpreterEx(rsrcmgr, device, obj_patch)
   

    parser = PDFParser(inf) # 文档关联解释器
    doc = PDFDocument(parser) # PDF文档对象
    with tqdm.tqdm(total=total_pages) as progress:
        for pageno, page in enumerate(PDFPage.create_pages(doc)):
            log.info(f"pageno:{pageno}")
            t_list = [None] * (100 + 1)
            if pages and (pageno not in pages):
                continue
            if callback:
                callback(progress)
            page.pageno = pageno
            pix = doc_zh[page.pageno].get_pixmap()
            image = np.fromstring(pix.samples, np.uint8).reshape(
                pix.height, pix.width, 3
            )[:, :, ::-1]
            page_layout = doclayout_model.predict(image, imgsz=int(pix.height / 32) * 32)[0]
            box = np.ones((pix.height, pix.width))
            h, w = box.shape
            vcls = ["abandon", "figure", "table", "isolate_formula", "formula_caption"]
            for i, d in enumerate(page_layout.boxes): # 坐标系切换，从yolo的坐标系下切换到pdfminer的坐标系下
                if not page_layout.names[int(d.cls)] in vcls:
                    x0, y0, x1, y1 = d.xyxy.squeeze()
                    # np.clip(x,w1,w2)将x限制在w1和w2之间，如果x小于w1，则返回w1，如果x大于w2，则返回w2，否则返回x
                    x0, y0, x1, y1 = (
                        np.clip(int(x0 - 1), 0, w - 1),
                        np.clip(int(h - y1 - 1), 0, h - 1),
                        np.clip(int(x1 + 1), 0, w - 1),
                        np.clip(int(h - y0 + 1), 0, h - 1),
                    )
                    box[y0:y1, x0:x1] = i + 2
                    t_list[i + 2] ={"xyxy":[x0,y0,x1,y1],"text":"","lf": 0,"remove":False,"change":0}
            for i, d in enumerate(page_layout.boxes):
                if page_layout.names[int(d.cls)] in vcls:
                    x0, y0, x1, y1 = d.xyxy.squeeze()
                    x0, y0, x1, y1 = (
                        np.clip(int(x0 - 1), 0, w - 1),
                        np.clip(int(h - y1 - 1), 0, h - 1),
                        np.clip(int(x1 + 1), 0, w - 1),
                        np.clip(int(h - y0 + 1), 0, h - 1),
                    )
                    box[y0:y1, x0:x1] = 0
            # box = do_rectangles_overlap(t_list,box)
            layout[page.pageno] = box
            # 新建一个 xref 存放新指令流
            page.page_xref = doc_zh.get_new_xref()  # hack 插入页面的新 xref
            doc_zh.update_object(page.page_xref, "<<>>")
            doc_zh.update_stream(page.page_xref, b"")
            doc_zh[page.pageno].set_contents(page.page_xref)
            interpreter.process_page(page)
            yield obj_patch,pageno
            progress.update() # 显示进度条
            if (pageno + 1) / total_pages == 1:
                status = 1
            else:
                status = 0
            process_translate.update_translate_item(
                db = db,
                fileid = file_id,
                status = status,
                porcess = (pageno + 1) / total_pages,
                base_lang = lang_in,
                target_lang = lang_out,
                translated_time = ''
            )
    device.close()
    # return obj_patch


def translate_stream(
    stream: bytes,
    pages: Optional[list[int]] = None,
    lang_in: str = "",
    lang_out: str = "",
    service: str = "",
    model: str = "",
    thread: int = 0,
    vfont: str = "",
    vchar: str = "",
    callback: object = None,
    url:str = "",
    api_key : str = None,
    file_id:str = '',
    db:Session = None,
    **kwarg: Any,
):
    font_list = [("tiro", None)]
    noto = None
    if lang_out.lower() in resfont_map:  # CJK
        resfont = resfont_map[lang_out.lower()]
        font_list.append((resfont, None))
    elif lang_out.lower() in noto_list:  # noto
        resfont = "noto"
        ttf_path = os.path.join(tempfile.gettempdir(), "GoNotoKurrent-Regular.ttf")
        if not os.path.exists(ttf_path):
            log.info("Downloading Noto font...")
            urllib.request.urlretrieve(
                "https://github.com/satbyy/go-noto-universal/releases/download/v7.0/GoNotoKurrent-Regular.ttf",
                ttf_path,
            )
        font_list.append(("noto", ttf_path))
        noto = Font("noto", ttf_path)
    else:  # fallback
        resfont = "china-ss"
        font_list.append(("china-ss", None))

    # doc_en = Document(stream=stream) # 原文件
   
    doc_zh = Document(stream=stream) # 翻译后
    page_count = doc_zh.page_count
    # font_list = [("china-ss", None), ("tiro", None)]
    font_id = {}
    for page in doc_zh:
        for font in font_list:
            font_id[font[0]] = page.insert_font(font[0], font[1])
    xreflen = doc_zh.xref_length()
    for xref in range(1, xreflen):
        for label in ["Resources/", ""]:  # 可能是基于 xobj 的 res
            try:  # xref 读写可能出错
                font_res = doc_zh.xref_get_key(xref, f"{label}Font")
                if font_res[0] == "dict":
                    for font in font_list:
                        font_exist = doc_zh.xref_get_key(xref, f"{label}Font/{font[0]}")
                        if font_exist[0] == "null":
                            doc_zh.xref_set_key(
                                xref,
                                f"{label}Font/{font[0]}",
                                f"{font_id[font[0]]} 0 R",
                            )
            except Exception:
                pass

    fp = io.BytesIO()
    doc_zh.save(fp)
    # obj_patch: dict = translate_patch(fp, **locals())
    for obj_patch, pageno in translate_patch(fp, **locals()):
        # log.info(obj_patch)
        for obj_id, ops_new in obj_patch.items():
            # ops_old=doc_en.xref_stream(obj_id)
            doc_zh.update_stream(obj_id, ops_new.encode())
        doc_temp = Document() # 临时文件
        doc_temp.insert_pdf(doc_zh,from_page = pageno,to_page = pageno)
        # doc_en.insert_file(doc_zh)
        # for id in range(page_count):
        #     doc_en.move_page(page_count + id, id * 2 + 1)
        
        yield doc_zh.write(deflate=1), doc_temp.write(deflate=1)


def translate(
    files: list[str],
    output: str = "",
    pages: Optional[list[int]] = None,
    lang_in: str = "",
    lang_out: str = "",
    service: str = "",
    model: str = "",
    thread: int = 0,
    vfont: str = "",
    vchar: str = "",
    callback: object = None,
    url:str="",
    api_key : str = None,
    file_id:str = '',
    db:Session = None,
    **kwarg: Any,
):
    if not files:
        # raise PDFValueError("No files to process.")
        raise "No files to process."

    missing_files = check_files(files)

    if missing_files:
        log.error("The following files do not exist:", file=sys.stderr)
        for file in missing_files:
            log.error(f"  {file}", file=sys.stderr)
        # raise PDFValueError("Some files do not exist.")
        raise "Some files do not exist."

    result_files = []

    for file in files:
        if file is str and (file.startswith("http://") or file.startswith("https://")):
            log.info("Online files detected, downloading...")
            try:
                r = requests.get(file, allow_redirects=True)
                if r.status_code == 200:
                    if not os.path.exists("./translated_files"):
                        log.info("Making a temporary dir for downloading PDF files...")
                        os.mkdir(os.path.dirname("./translated_files"))
                    with open("./translated_files/tmp_download.pdf", "wb") as f:
                        log.info(f"Writing the file: {file}...")
                        f.write(r.content)
                    file = "./translated_files/tmp_download.pdf"
                else:
                    r.raise_for_status()
            except Exception as e:
                # raise PDFValueError(
                #     f"Errors occur in downloading the PDF file. Please check the link(s).\nError:\n{e}"
                # )
                raise f"Errors occur in downloading the PDF file. Please check the link(s).\nError:\n{e}"
        filename = os.path.splitext(os.path.basename(file))[0]

        doc_raw = open(file, "rb")
        s_raw = doc_raw.read() # 返回二进制格式
        # s_mono, s_dual = translate_stream(s_raw, **locals())
        i = 0
        for full_file, temp_file in translate_stream(s_raw, **locals()):
            file_trans = Path(output) / f"{filename}_trans.pdf"
            # file_temp = Path(output) / f"{filename}_temp.pdf"
            doc_full = open(file_trans, "wb")
            doc_full.write(full_file)
            # 添加每页的pdf
            per_page_path = Path(output) / "translated_splited"/ f"{filename}_trans_{str(i)}.pdf"
            per_page = open(per_page_path, "wb")
            per_page.write(temp_file)
            result_files.append(str(file_trans))
            i = i + 1
            yield doc_full,temp_file # 返回字节流
    # return result_files
