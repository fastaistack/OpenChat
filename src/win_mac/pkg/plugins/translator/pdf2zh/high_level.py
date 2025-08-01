"""Functions that can be used for the most common use-cases for pdf2zh.six"""

import asyncio
import io
import os
import re
import sys
import tempfile
import logging
from asyncio import CancelledError
from pathlib import Path
from string import Template
from typing import Any, BinaryIO, List, Optional, Dict

import numpy as np
import requests
import tqdm
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfexceptions import PDFValueError
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from pymupdf import Document, Font

from pkg.plugins.translator.pdf2zh.converter import TranslateConverter
from pkg.plugins.translator.pdf2zh.doclayout import OnnxModel
from pkg.plugins.translator.pdf2zh.pdfinterp import PDFPageInterpreterEx
from pkg.plugins.translator.pdf2zh.doclayout import DocLayoutModel
from pkg.plugins.translator.pdf2zh.config import ConfigManager
from pkg.projectvar import Projectvar
from sqlalchemy.orm import Session
from pkg.server.process import process_translate
from pkg.projectvar import constants as const
from pkg.logger import Log

NOTO_NAME = "noto"
gvar = Projectvar()
log = Log()

logger = logging.getLogger(__name__)

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
    "kn",  # Kannada
    "ml",  # Malayalam
    "mr",  # Marathi
    "ru",  # Russian
    "sr",  # Serbian
    "ta",  # Tamil
    "te",  # Telugu
    "th",  # Thai
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

def assign_if_external_neighbors_leq1(box, y0, y1, x0, x1, value):
    """
    在赋值前检查子区域外部直接邻域是否存在大于1的值
    
    参数:
    box: 二维数组
    y0, y1: 子区域的行范围（不包含y1）
    x0, x1: 子区域的列范围（不包含x1）
    value: 要赋的值
    """
    rows, cols = box.shape
    
    # 初始化标志，表示外部邻域是否存在>1的值
    has_larger_than_1 = False
    
    # 检查左侧邻域（如果存在）
    if x0 > 0:
        left_neighbor = box[y0:y1, x0-1]
        if np.any(left_neighbor > 1):
            has_larger_than_1 = True
    
    # 检查右侧邻域（如果存在）
    if x1 < cols:
        right_neighbor = box[y0:y1, x1]
        if np.any(right_neighbor > 1):
            has_larger_than_1 = True
    
    # 检查上侧邻域（如果存在）
    if y0 > 0:
        top_neighbor = box[y0-1, x0:x1]
        if np.any(top_neighbor > 1):
            has_larger_than_1 = True
    
    # 检查下侧邻域（如果存在）
    if y1 < rows:
        bottom_neighbor = box[y1, x0:x1]
        if np.any(bottom_neighbor > 1):
            has_larger_than_1 = True
    
    # 根据检查结果决定是否赋值
    if has_larger_than_1:
        # 外部邻域存在>1的值，不进行赋值
        return box
    else:
        # 赋值
        box[y0:y1, x0:x1] = value
        return box

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
    noto_name: str = "",
    noto: Font = None,
    callback: object = None,
    cancellation_event: asyncio.Event = None,
    model: OnnxModel = None,
    envs: Dict = None,
    prompt: Template = None,
    ignore_cache: bool = False,
    use_model: str = '',
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
        rsrcmgr,
        vfont,
        vchar,
        thread,
        layout,
        lang_in,
        lang_out,
        service,
        noto_name,
        noto,
        envs,
        prompt,
        ignore_cache,
        use_model,
        url, 
        api_key, 
        file_id, 
        total_pages,
        db
    )

    assert device is not None
    obj_patch = {}
    interpreter = PDFPageInterpreterEx(rsrcmgr, device, obj_patch)
    

    parser = PDFParser(inf)
    doc = PDFDocument(parser)
    with tqdm.tqdm(total=total_pages) as progress:
        for pageno, page in enumerate(PDFPage.create_pages(doc)):
            log.info(f"pageno:{pageno}")
            t_list = [None] * (100 + 1)
            if pages and (pageno not in pages):
                continue
            if callback:
                callback(progress)
            page.pageno = pageno
            pix = doc_zh[page.pageno].get_pixmap() # PyMuPDF创建页面内容的位图图像，提取许多控制图像的变体：分辨率/DPI、色彩空间、透明度、旋转、镜像、位移、剪切
            image = np.fromstring(pix.samples, np.uint8).reshape(
                pix.height, pix.width, 3
            )[:, :, ::-1]
            # page_layout = doclayout_model.predict(image, imgsz=int(pix.height / 32) * 32)[0]
            page_layout = model.predict(image)[0]
            # -------------图像绘制--------------
            # model.save_layout_as_image(image,f"./output/yoloLayout_{str(pageno)}.png")
            # import pdfminerlayout as pf
            # pf.save_as_image("C:\\Users\\litiantian03\\Desktop\\论文-1.pdf",image,"./output/pdfminerLayout.png")
            # # --------------图像绘制-------------
            # kdtree 是不可能 kdtree 的，不如直接渲染成图片，用空间换时间
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
                    # box[y0:y1, x0:x1] = i + 2
                    box = assign_if_external_neighbors_leq1(box, y0, y1, x0, x1, i + 2)
                    # t_list[i + 2] ={"xyxy":[x0,y0,x1,y1],"text":"","lf": 0,"remove":False,"change":0}
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


def translate_stream(
    stream: bytes,
    pages: Optional[list[int]] = None,
    lang_in: str = "",
    lang_out: str = "",
    service: str = "",
    thread: int = 0,
    vfont: str = "",
    vchar: str = "",
    callback: object = None,
    cancellation_event: asyncio.Event = None,
    model: OnnxModel = None,
    envs: Dict = None,
    prompt: Template = None,
    skip_subset_fonts: bool = False,
    ignore_cache: bool = False,
    use_model: str = '',
    url:str = "",
    api_key : str = None,
    file_id:str = '',
    db:Session = None,
    **kwarg: Any,
):
    font_list = [("tiro", None)]

    font_path = download_remote_fonts(lang_out.lower())
    noto_name = NOTO_NAME
    noto = Font(noto_name, font_path)
    font_list.append((noto_name, font_path))

    doc_en = Document(stream=stream)
    stream = io.BytesIO()
    doc_en.save(stream)
    doc_zh = Document(stream=stream)
    page_count = doc_zh.page_count
    # font_list = [("GoNotoKurrent-Regular.ttf", font_path), ("tiro", None)]
    font_id = {}
    for page in doc_zh:
        for font in font_list:
            font_id[font[0]] = page.insert_font(font[0], font[1])
    xreflen = doc_zh.xref_length()
    for xref in range(1, xreflen):
        for label in ["Resources/", ""]:  # 可能是基于 xobj 的 res
            try:  # xref 读写可能出错
                font_res = doc_zh.xref_get_key(xref, f"{label}Font")
                target_key_prefix = f"{label}Font/"
                if font_res[0] == "xref":
                    resource_xref_id = re.search("(\\d+) 0 R", font_res[1]).group(1)
                    xref = int(resource_xref_id)
                    font_res = ("dict", doc_zh.xref_object(xref))
                    target_key_prefix = ""

                if font_res[0] == "dict":
                    for font in font_list:
                        target_key = f"{target_key_prefix}{font[0]}"
                        font_exist = doc_zh.xref_get_key(xref, target_key)
                        if font_exist[0] == "null":
                            doc_zh.xref_set_key(
                                xref,
                                target_key,
                                f"{font_id[font[0]]} 0 R",
                            )
            except Exception:
                pass

    fp = io.BytesIO()
    doc_zh.save(fp)
    for obj_patch, pageno in translate_patch(fp, **locals()):
        # log.info(obj_patch)
        for obj_id, ops_new in obj_patch.items():
            # ops_old=doc_en.xref_stream(obj_id)
            doc_zh.update_stream(obj_id, ops_new.encode())
        doc_temp = Document() # 临时文件
        doc_temp.insert_pdf(doc_zh, from_page = pageno, to_page = pageno)
        # doc_en.insert_file(doc_zh)
        # for id in range(page_count):
        #     doc_en.move_page(page_count + id, id * 2 + 1)
        # if not skip_subset_fonts: # 移除未使用的字符数据，减小文档体积
        #     doc_zh.subset_fonts(fallback=True)
        doc_temp.subset_fonts(fallback=False)
        yield doc_zh.write(deflate=True), doc_temp.write(deflate=True)
    
    # obj_patch: dict = translate_patch(fp, **locals())

    # for obj_id, ops_new in obj_patch.items():
    #     doc_zh.update_stream(obj_id, ops_new.encode())

    # doc_en.insert_file(doc_zh)
    # for id in range(page_count):
    #     doc_en.move_page(page_count + id, id * 2 + 1)
    # if not skip_subset_fonts:
    #     doc_zh.subset_fonts(fallback=True)
    #     doc_en.subset_fonts(fallback=True)
    # return (
    #     doc_zh.write(deflate=True, garbage=3, use_objstms=1),
    #     doc_en.write(deflate=True, garbage=3, use_objstms=1),
    # )


def translate(
    files: list[str],
    output: str = "",
    pages: Optional[list[int]] = None,
    lang_in: str = "",
    lang_out: str = "",
    service: str = "",
    thread: int = 0,
    vfont: str = "",
    vchar: str = "",
    callback: object = None,
    compatible: bool = False,
    cancellation_event: asyncio.Event = None,
    model: OnnxModel = None,
    envs: Dict = None,
    prompt: Template = None,
    skip_subset_fonts: bool = False,
    ignore_cache: bool = False,
    use_model: str = '',
    url:str="",
    api_key : str = None,
    file_id:str = '',
    db:Session = None,
    **kwarg: Any,
):
    os.makedirs(os.path.join(output,'translated_splited'),exist_ok=True)
    if not files:
        raise "No files to process."

    missing_files = check_files(files)

    if missing_files:
        log.error("The following files do not exist:", file=sys.stderr)
        for file in missing_files:
            log.error(f"  {file}", file=sys.stderr)
        raise "Some files do not exist."

    result_files = []

    for file in files:
        if type(file) is str and (
            file.startswith("http://") or file.startswith("https://")
        ):
            log.info("Online files detected, downloading...")
            try:
                r = requests.get(file, allow_redirects=True)
                if r.status_code == 200:
                    with tempfile.NamedTemporaryFile(
                        suffix=".pdf", delete=False
                    ) as tmp_file:
                        log.info(f"Writing the file: {file}...")
                        tmp_file.write(r.content)
                        file = tmp_file.name
                else:
                    r.raise_for_status()
            except Exception as e:
                raise f"Errors occur in downloading the PDF file. Please check the link(s).\nError:\n{e}"
        filename = os.path.splitext(os.path.basename(file))[0]

        # If the commandline has specified converting to PDF/A format
        # --compatible / -cp
        if compatible:
            with tempfile.NamedTemporaryFile(
                suffix="-pdfa.pdf", delete=False
            ) as tmp_pdfa:
                log.info(f"Converting {file} to PDF/A format...")
                # convert_to_pdfa(file, tmp_pdfa.name)
                doc_raw = open(tmp_pdfa.name, "rb")
                os.unlink(tmp_pdfa.name)
        else:
            doc_raw = open(file, "rb")
        s_raw = doc_raw.read()
        doc_raw.close()

        temp_dir = Path(tempfile.gettempdir())
        file_path = Path(file)
        try:
            if file_path.exists() and file_path.resolve().is_relative_to(
                temp_dir.resolve()
            ):
                file_path.unlink(missing_ok=True)
                logger.debug(f"Cleaned temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean temp file {file_path}", exc_info=True)

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
            translating_files = gvar.get_complated_page_count()
            translating_files[file_id] = i
            gvar.set_complated_page_count(translating_files)
            i = i + 1
            doc_full.close()
            per_page.close()
            yield doc_full,temp_file # 返回字节流
        
        remove_unused_fonts(file_trans)
        # s_mono, s_dual = translate_stream(
        #     s_raw,
        #     **locals(),
        # )
        # file_mono = Path(output) / f"{filename}-mono.pdf"
        # file_dual = Path(output) / f"{filename}-dual.pdf"
        # doc_mono = open(file_mono, "wb")
        # doc_dual = open(file_dual, "wb")
        # doc_mono.write(s_mono)
        # doc_dual.write(s_dual)
        # doc_mono.close()
        # doc_dual.close()
        # result_files.append((str(file_mono), str(file_dual)))

    # return result_files


def download_remote_fonts(lang: str):
    lang = lang.lower()
    LANG_NAME_MAP = {
        **{la: "GoNotoKurrent-Regular.ttf" for la in noto_list},
        **{
            la: f"SourceHanSerif{region}-Regular.ttf"
            for region, langs in {
                "CN": ["zh-cn", "zh-hans", "zh","fr"],
                "TW": ["zh-tw", "zh-hant"],
                "JP": ["ja"],
                "KR": ["ko"],
            }.items()
            for la in langs
        },
    }
    font_name = LANG_NAME_MAP.get(lang, "GoNotoKurrent-Regular.ttf")
    
    if const.SYSTEM == const.WINDOWS:
        # font_path = './_internal/fonts/SourceHanSerifCN-Regular.ttf'
        font_path = os.path.join('_internal','fonts',font_name)
    else:
        # macOS 下判断是否为打包运行环境
        if getattr(sys, 'frozen', False):
            font_path = os.path.join(sys._MEIPASS, 'fonts', font_name)
        else:
            font_path = os.path.join('_internal', 'fonts', font_name)
    
    log.info(f"use font: {font_path}")

    return font_path

def remove_unused_fonts(file):
    log.info("去除未使用字体")
    try:
        # 读取文件内容为字节流
        with open(file, "rb") as f:
            stream = f.read()  # 读取为字节流
        # os.unlink(file)
        # 处理文档
        doc_zh = Document(stream=stream)
        doc_zh.subset_fonts(fallback=False)
        full_file = doc_zh.write(deflate=True)
        
        doc_full = open(file, "wb")
        doc_full.write(full_file)
        doc_full.close()

        log.info("字体处理完成并保存")
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        log.error(f"处理字体时出错: {e}")
        raise