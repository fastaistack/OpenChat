import fitz
import numpy as np
import time
from PIL import Image, ImageDraw
import cv2
import os
import time
import pytesseract
from pytesseract import Output
from pkg.logger import Log
from pkg.plugins.translator.pdf2zh.doclayout import DocLayoutModel
from pkg.projectvar import Projectvar
from pkg.server.process import process_translate

zoom = 4.0 # 图片缩放系数
crop_img_list = []
texts_list = []
max_cls = 0
translated_path = 'translated_files'
log = Log()
gvar = Projectvar()

def stop_ocr_process(file_id):
    translating_file_list = gvar.get_needstop()
    if file_id in translating_file_list:
        log.info("ocr终止pdf翻译")
        return True
    else:
        return False
    
def reset_translated_status(db,file_id):
    translating_file_list = gvar.get_needstop()
    if file_id in translating_file_list:
        # 重置状态
        process_translate.set_ocr_status(db,file_id,False)
        process_translate.set_ocr_process_item(db,file_id,0)
        process_translate.update_translate_item(
                db = db,
                fileid = file_id,
                status = -1,
                porcess = 0,
                base_lang = "",
                target_lang = "",
                translated_time = ''
            )
        # 移除正在翻译的列表
        gvar.delete_needstop(file_id)

def pdf_to_image(db,pdf_path,file_id):
    doc = fitz.open(pdf_path)
    page_box_list = []
    save_path_list = []
    start_time = time.time()
    for pg in range(doc.page_count):
        # 判断是否需要终止此线程
        if stop_ocr_process(file_id):
            return [],[]
        page = doc[pg]
        rotate = int(0)
        # 每个尺寸的缩放系数为zoom，这将为我们生成分辨率提高zoom^2的图像。
        trans = fitz.Matrix(zoom, zoom).prerotate(rotate)
        pix = page.get_pixmap(matrix=trans, alpha=False)
        image = np.fromstring(pix.samples, np.uint8).reshape(
                pix.height, pix.width, 3
            )[:, :, ::-1]
        start_time = time.time()
        page_box = doclayout_yolo(image,pix,pg)
        log.info(f"doclayout_yolo waste time:{time.time()-start_time}s")
        page_box_list.append(page_box)
        pdf_to_img_path = os.path.join(translated_path,'output','pdf_to_img')
        os.makedirs(pdf_to_img_path,exist_ok=True)
        # ./translated_files/output/pdf_to_img/0.png
        img_save_path = os.path.join(pdf_to_img_path,'%s.png' % pg )  
        save_path_list.append(img_save_path)
        pix.save(img_save_path)
        log.info(f"page pix height:{pix.height},width:{pix.width}")
        log.info(f"pdf_to_image + doclayout：{pg/(doc.page_count*3)}")
        process_translate.set_ocr_process_item(db,file_id,pg/(doc.page_count*3))
    doc.close()
    return save_path_list,page_box_list


def doclayout_yolo(image,pix,page_num):
    c_list = []
    t_list = [None] * (100 + 1)
    img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)


    model = DocLayoutModel.load_available()
    page_layout = model.predict(image)[0]
    doclayout_path = os.path.join(translated_path,"output",'doclayout')
    os.makedirs(doclayout_path,exist_ok=True)
    model.save_layout_as_image(image,os.path.join(doclayout_path,"%s.png" % page_num))
    box = np.ones((pix.height, pix.width))
    h, w = box.shape
    vcls = ["abandon", "figure", "table", "isolate_formula", "formula_caption"]
    for i, d in enumerate(page_layout.boxes):
        if not page_layout.names[int(d.cls)] in vcls:
            x0, y0, x1, y1 = d.xyxy.squeeze()
            x0, y1, x1, y0 = (
                np.clip(int(x0 - 1), 0, w - 1),
                np.clip(int(y1 - 1), 0, h - 1),
                np.clip(int(x1 - 1), 0, w - 1),
                np.clip(int(y0 - 1), 0, h - 1),
            )
            draw.rectangle([(x0, y0), (x1, y1)], outline='green')
            draw.text((x0, y0, i+2), f"{x0, y0 , i+2}", fill="blue")
            draw.text((x1-8, y1-8, i+2), f"{x1, y1 , i+2}", fill="blue")
            box[y0:y1, x0:x1] = i + 2
            global max_cls
            if max_cls <= i + 2:
                max_cls = i + 2
            global texts
            t_list[i + 2] ={"xyxy":[x0,y0,x1,y1],"text":"","lf": 0}
    for i, d in enumerate(page_layout.boxes): # abandon的
        if page_layout.names[int(d.cls)] in vcls:
            x0, y0, x1, y1 = d.xyxy.squeeze()
            x0, y1, x1, y0 = (
                np.clip(int(x0 - 1), 0, w - 1),
                np.clip(int(y1 - 1), 0, h - 1),
                np.clip(int(x1 - 1), 0, w - 1),
                np.clip(int(y0 - 1), 0, h - 1),
            )
            c_list.append([x0, y0, x1, y1])
            draw.rectangle([(x0, y0), (x1, y1)], outline='red')
            draw.text((x0, y0), f"{x0, y0}", fill="blue")
            box[y0:y1, x0:x1] = 0
    global crop_img_list, texts_list
    crop_img_list.append(c_list) # crop_img_list 对应page_num下标
    texts_list.append(t_list)
    doclayout_path = os.path.join(translated_path,"output",'doclayout')
    os.makedirs(doclayout_path,exist_ok=True)
    # ./translated_files/output/doclayout_abandon/0.png
    img.save(os.path.join(doclayout_path,'%s.png' % page_num))
    return box


# def calculate_fontsize(text, box_w, box_h, line):
#     """
#     计算文本应选取的字号大小。

#     :param text: 要插入的文本
#     :param page_w: 页面的宽度（像素）
#     :param page_h: 页面的高度（像素）
#     :param box_w: 插入区域的宽度（像素）
#     :param box_h: 插入区域的高度（像素）
#     :param line: 要插入的行数
#     :return: 建议的字号大小
#     """
#     # 假设每个字符的宽度大约是字号大小的 0.6 倍，高度大约等于字号大小
#     # 先根据宽度计算字号
#     max_chars_per_line = len(text) // line if line > 0 else len(text)
#     fontsize_w = box_w / (max_chars_per_line * 0.6) if max_chars_per_line > 0 else box_w

#     # 再根据高度计算字号
#     fontsize_h = box_h / line if line > 0 else box_h

#     # 取较小的值作为最终的字号，确保文本能完整显示在区域内
#     fontsize = min(fontsize_w, fontsize_h)

#     # 确保字号不小于 1
#     return max(10, fontsize)
def ensure_tesseract_installed():
    import subprocess
    import sys
    import shutil
    
    """
    检查 tesseract 是否已安装。如果未安装，则执行 update.sh 启动终端安装。
    """
    # ✅ 优先用 shutil.which() 检查
    if shutil.which("tesseract"):
        print("✅ 检测到 Tesseract 已安装，无需处理。")
        return  # 已经存在，直接退出函数

    print("🚫 检测到系统未安装 Tesseract，准备启动安装脚本...")

    # 获取当前运行目录（打包后是 MacOS/）
    base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()

    # 脚本路径（与可执行文件同级）
    script_path = os.path.join(base_path, 'install_tesseract.sh')

    # ✅ 先确认脚本是否存在
    if not os.path.exists(script_path):
        print(f"⚠️ 安装脚本不存在: {script_path}")
        return  # 没脚本就退出，避免出错

    # ✅ 给脚本加执行权限（冗余但安全）
    subprocess.run(['chmod', '+x', script_path], check=False)

    # ✅ 启动脚本，在独立会话中运行
    try:
        subprocess.Popen(
            ['bash', script_path],
            cwd=base_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # ✅ 脱离当前 app 控制
        )
    except Exception as e:
        print(f"🚨 启动安装脚本失败: {e}")

def tesseractocr(db,img_path_list,lang,file_id):

    ensure_tesseract_installed()
    ocr_result_list = []
    count = 0 # 用于计数
    for img_path in img_path_list:
        # 判断是否需要终止此线程
        if stop_ocr_process(file_id):
            return []
        start_time = time.time()
        image= Image.open(img_path)
        width,height=image.width,image.height
        data = pytesseract.image_to_data(image,lang=lang,output_type=Output.DICT)

        ocr_result = []
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            if text:
                left = data['left'][i]
                top = data['top'][i]
                width = data['width'][i]
                height = data['height'][i]
                x, y, w, h = left,top,width,height
                d = {"boxes":[x,y,x+w,y+h],"text":text}
                ocr_result.append(d)
        ocr_result_list.append(ocr_result)
        log.info(f"tesseractocr layout cost {time.time() - start_time}s--------img:{img_path}")
        log.info(f"tesseractocr：{(len(img_path_list) + count)/(len(img_path_list)*3)}")
        process_translate.set_ocr_process_item(db,file_id,(len(img_path_list) + count)/(len(img_path_list)*3))
        count = count + 1
    return ocr_result_list

def calculate_fontsize(text, w, h, line):
    # line = 0 
    if line != 0:
        area = w * h
        area_line = area / line
        word_line = len(text) / line
        per_pix = area_line / word_line
        log.info(f"area:{area},area_line:{area_line},word_line:{word_line},per_pix:{per_pix}") 
        fontsize = int(per_pix /72 * 1.0) 
        log.info(f"fontsize:{fontsize}")
    else:
        fontsize = 10
    return 15

def trans_(pdf_path,lang,translated_origin_path,file_id,db):
    global translated_path
    if translated_origin_path:
        translated_path = translated_origin_path
    # 创建translated_files目录
    os.makedirs(translated_path,exist_ok=True)
    img_path_list, page_box_list = pdf_to_image(pdf_path,file_id)
    tesseractocr_result_list = tesseractocr(img_path_list,lang,file_id)
    pdf_document = fitz.open()
    page_num = 0
    for page_box in page_box_list:
        # 判断是否需要终止此线程
        if stop_ocr_process(file_id):
            break
        page = pdf_document.new_page()
        h , w = page_box.shape
        log.info(f"page_box height:{h},width:{w}")
        tesseractocr_result = tesseractocr_result_list[page_num]
        global texts_list
        texts = texts_list[page_num]

        for result in tesseractocr_result: # 按单词排列
            x0,y0,x1,y1 = result['boxes']
            text = result['text']
            cls = page_box[np.clip(int((y0+y1)/2), 0, h-1), np.clip(int((x0+x1)/2), 0, w-1)]
            if cls == 0:
                continue
            if texts[int(cls)] is None:
                continue
            else:
                texts[int(cls)]["text"] += (" " + text)
                texts[int(cls)]['lf'] = 1

        # 插入图片
        global crop_img_list
        for c_img in crop_img_list[page_num]:
            x0,y0,x1,y1 = c_img[0],c_img[1],c_img[2],c_img[3]

            img = cv2.imread(img_path_list[page_num])
            cropped = img[y0:y1, x0:x1]  # 裁剪坐标为[y0:y1, x0:x1]
            crop_path = os.path.join(translated_path,'output','crop')
            os.makedirs(crop_path,exist_ok=True)
            crop_img_path = os.path.join(crop_path,'cropped.png')
            cv2.imwrite(crop_img_path, cropped)
                
            x0,y0,x1,y1 = int(x0/zoom),int(y0/zoom),int(x1/zoom),int(y1/zoom)
            # 图片截取有偏移
            rect = fitz.Rect(x0,y0,x1,y1)
            
            page.insert_image(
                rect,
                filename=crop_img_path,
            )
        # 插入文字
        for txt in texts:
            if txt is not None:
                x0, y0, x1, y1 = txt["xyxy"]
                insert_text = txt["text"].strip()
                fontsize = calculate_fontsize(insert_text, int(x1-x0), int(y1-y0), line=txt['lf'])
                log.info(f"current  insert fontsize：{fontsize}")
                # html_text = f"""
                # <html>
                #     <body style="background-color: transparent;">
                #         <!-- 设置段落文本左对齐，从左上角开始布局 -->
                #         <p style="font-size:{fontsize}pt; line-height:1.2; text-align: left; background-color: transparent; height: 100%;"> {insert_text} </p> 
                #     </body>
                # </html>
                # """ 
                html_text = f"""
                <html>
                    <head>
                        <style>
                            html, body {{
                                margin: 0;
                                padding: 0;
                                width: 100%;
                                height: 100%;
                                box-sizing: border-box;
                            }}
                            p {{
                                margin: 0;
                                padding: 0;
                                width: 100%;
                                height: 100%;
                                box-sizing: border-box;
                                /* 添加自动换行处理 */
                                overflow-wrap: break-word;
                            }}
                        </style>
                    </head>
                    <body style="background-color: transparent;">
                        <p style="font-size:{fontsize}pt; line-height:1.3;text-align:justify; background-color: transparent;height: 100%;"> {insert_text} </p> 
                    </body>
                </html>
                """ 
                # html_text = f"""
                # <html>
                #     <head>
                #         <style>
                #             html, body {{
                #                 margin: 0;
                #                 padding: 0;
                #                 width: 100%;
                #                 height: 100%;
                #                 box-sizing: border-box;
                #             }}
                #             p {{
                #                 margin: 0;
                #                 padding: 0;
                #                 width: 100%;
                #                 height: 100%;
                #                 box-sizing: border-box;
                #                 /* 添加自动换行处理 */
                #                 overflow-wrap: break-word;
                #             }}
                #         </style>
                #     </head>
                #     <body style="background-color: transparent; height:100%">
                #         <p style="
                            
                #             line-height:1.0;
                #             text-align:justify;
                #             background-color: transparent;">
                #             {insert_text}
                #         </p>
                #     </body>
                # </html>
                # """
                if txt['lf'] == 1: # 一行时，适当放大文本填充方框，以获取更大的字体
                    rect = fitz.Rect(int(x0 / zoom - zoom/2 ) , int(y0 / zoom - zoom) , int(x1 / zoom) , int(y1 / zoom + zoom *2))
                else:
                    rect = fitz.Rect(int(x0 / zoom - zoom/2 ) , int(y0 / zoom - zoom*2) , int(x1 / zoom + zoom/2) , int(y1 / zoom + zoom*3) )
                log.info(f"写入区域: {rect},\n文本内容:{insert_text},\n字号大小:{fontsize}\n")

                # 用 insert_htmlbox 替换 insert_textbox
                page.insert_htmlbox(rect, html_text,overlay=True) # overlay将文本放在前景True
                # import random
                # page.draw_rect(rect, color=(random.randint(0,255) / 255, random.randint(0,255) / 255, random.randint(0,255) / 255), width=1)
        
        page_num += 1
        from pkg.server.process import process_translate
        log.info(f"ocr的进度为：{page_num/len(img_path_list)}")
        process_translate.set_ocr_process_item(db,file_id,page_num/len(img_path_list))
    crop_img_list = []
    texts_list = []
    # filename = pdf_path.split("/")[-1].split(".pdf")[0]
    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    os.makedirs(os.path.join(translated_path,'output','ocr_output'),exist_ok=True)
    # translated_files/pdf_translated_files/xxx_ocr.pdf
    ocr_output_path = os.path.join(translated_path,'output','ocr_output',f"{filename}_ocr.pdf")
    pdf_document.save(ocr_output_path)
    pdf_document.close()
    return ocr_output_path

# if __name__ == "__main__":
#     start_time = time.time()
#     # trans("./data/DeepSeek-4.pdf","en")
#     trans_("./data/DeepSeek_ocr_output.pdf","eng")
#     print("--- totally cost %s seconds ---" % (time.time() - start_time))