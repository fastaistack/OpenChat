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
from pkg.projectvar import constants as consts

# try:
#     from paddleocr import PaddleOCR
#     HAS_PADDLEOCR = True
# except ImportError:
#     HAS_PADDLEOCR = False

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
            if box['remove'] and texts_box[box['change']]:
                x0,y0,x1,y1 = texts_box[box['change']]['xyxy']
                page_box[y0:y1, x0:x1] = box['change'] # 将需要替换的位置，替换为需要替换的数值
                texts_box[i] = None
    return texts_box

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
            # if np.any(box[y0:y1, x0:x1] > 1):
            #     print(f"{x0,y0, x1,y1},该区域有值，说明覆盖，应该废弃")
            #     continue
            draw.rectangle([(x0, y0), (x1, y1)], outline='green')
            draw.text((x0, y0, i+2), f"{x0, y0 , i+2}", fill="blue")
            draw.text((x1-8, y1-8, i+2), f"{x1, y1 , i+2}", fill="blue")
            box[y0:y1, x0:x1] = i + 2
            global max_cls
            if max_cls <= i + 2:
                max_cls = i + 2
            global texts
            t_list[i + 2] ={"xyxy":[x0,y0,x1,y1],"text":"","lf": 0,"remove":False,"change":0}
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


def calculate_fontsize(text, w, h, line):
    # line = 0 
    if line != 0:
        area = w * h
        area_line = area / line
        word_line = len(text) / line
        per_pix = area_line / word_line
        log.info(f"area:{area},area_line:{area_line},word_line:{word_line},per_pix:{per_pix}") 
        fontsize = int(per_pix /72 * 1.3) 
        log.info(f"fontsize:{fontsize}")
    else:
        fontsize = 10
    return 10

def tesseractocr(db,img_path_list,lang,file_id):
    ocr_result_list = []
    count = 0 # 用于计数
    for img_path in img_path_list:
        # 判断是否需要终止此线程
        if stop_ocr_process(file_id):
            return []
        start_time = time.time()
        image= Image.open(img_path)
        width,height=image.width,image.height
        if consts.SYSTEM == consts.WINDOWS:
            tessdata_dir_config = '--tessdata-dir ./_internal/Tesseract_OCR/tessdata'
            log.info(f"tessdata_dir_config:{tessdata_dir_config}")
            data = pytesseract.image_to_data(image,lang=lang,output_type=Output.DICT,config=tessdata_dir_config)
        else:
            log.info("MAC pytesseract")
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
        log.info(f"tesseractocr layout cost {time.time() - start_time}s--img:{img_path}")
        log.info(f"tesseractocr：{(len(img_path_list) + count)/(len(img_path_list)*3)}")
        process_translate.set_ocr_process_item(db,file_id,(len(img_path_list) + count)/(len(img_path_list)*3))
        count = count + 1
    return ocr_result_list

def trans_(pdf_path,lang,translated_origin_path,file_id,db):
    global translated_path
    if translated_origin_path:
        translated_path = translated_origin_path
    # 创建translated_files目录
    os.makedirs(translated_path,exist_ok=True)
    img_path_list, page_box_list = pdf_to_image(db,pdf_path,file_id)
    tesseractocr_result_list = tesseractocr(db,img_path_list,lang,file_id)
    pdf_document = fitz.open()
    page_num = 0
    for page_box in page_box_list:
        # 判断是否需要终止此线程
        if stop_ocr_process(file_id):
            return ''
        page = pdf_document.new_page()
        h , w = page_box.shape
        log.info(f"page_box height:{h},width:{w}")
        tesseractocr_result = tesseractocr_result_list[page_num]
        global texts_list
        texts = texts_list[page_num]
        texts = do_rectangles_overlap(texts,page_box)
        
        l_x1 = 10000
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
                if l_x1 > x0: # 统计行数，
                    texts[int(cls)]['lf'] = texts[int(cls)]['lf'] + 1
                    l_x1 = x1

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
                if lang not in ['eng' ,'fra']:
                    # insert_text = txt["text"].strip()
                    insert_text = txt["text"].replace(" ", "")
                else:
                    insert_text = txt["text"].strip()
                insert_text ='  '  + insert_text
                fontsize = calculate_fontsize(insert_text, int(x1-x0), int(y1-y0), line=txt['lf'])
                log.info(f"current  insert fontsize：{fontsize}")
                # insert_text = ''
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
                if txt['lf'] == 1: # 一行时，适当放大文本填充方框，以获取更大的字体
                    # rect = fitz.Rect(int(x0 / zoom - zoom/2 ) , int(y0 / zoom - zoom) , int(x1 / zoom) , int(y1 / zoom + zoom *2))
                    rect = fitz.Rect(int(x0 / zoom) , int(y0 / zoom) , int(x1 / zoom ) , int(y1 / zoom) )
                else:
                    # rect = fitz.Rect(int(x0 / zoom - zoom/2 ) , int(y0 / zoom - zoom*2) , int(x1 / zoom + zoom/2) , int(y1 / zoom + zoom*2) )
                    rect = fitz.Rect(int(x0 / zoom) , int(y0 / zoom) , int(x1 / zoom ) , int(y1 / zoom) )
                log.info(f"写入区域: {rect},\n文本内容:{insert_text},\n字号大小:{fontsize}\n")

                # 用 insert_htmlbox 替换 insert_textbox
                page.insert_htmlbox(rect, html_text,overlay=True) # overlay将文本放在前景True
                # page.insert_textbox(rect, insert_text, fontsize = fontsize, fontname="china-ss")
                # import random
                # page.draw_rect(rect, color=(random.randint(0,255) / 255, random.randint(0,255) / 255, random.randint(0,255) / 255), width=1)
        
        page_num += 1

        log.info(f"合并的进度为：{(len(img_path_list)*2+page_num)/(len(img_path_list)*3)}")
        process_translate.set_ocr_process_item(db,file_id,(len(img_path_list)*2+page_num)/(len(img_path_list)*3))
    if stop_ocr_process(file_id): # 此处需要退出
        return ''
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

# def paddleocr(db,img_path_list,lang,file_id):
#     ocr_result_list = []
#     if HAS_PADDLEOCR:
#         ocr = PaddleOCR(use_angle_cls=True, lang=lang)
#     else:
#         return ocr_result_list
#     count = 0 # 用于计数
#     for img_path in img_path_list:
#         start_time = time.time()
#         result = ocr.ocr(img_path, cls=True)
#         ocr_result = []
#         for line in result[0]:
#             d = {"boxes":line[0],"txts":line[1][0]}
#             ocr_result.append(d)
#         ocr_result_list.append(ocr_result)
#         log.info(f"paddleocr layout cost {time.time() - start_time}s--img:{img_path}")
#         log.info(f"paddleocr{(len(img_path_list) + count)/(len(img_path_list)*3)}")
#         process_translate.set_ocr_process_item(db,file_id,(len(img_path_list) + count)/(len(img_path_list)*3))
#         count = count + 1
#     return ocr_result_list

# def trans(pdf_path,lang,translated_origin_path,file_id,db):
#     """
#     paddleOCR
#     """
#     global translated_path
#     if translated_origin_path:
#         translated_path = translated_origin_path
#     # 创建translated_files目录
#     os.makedirs(translated_path,exist_ok=True)
    
#     img_path_list, page_box_list = pdf_to_image(db,pdf_path,file_id)
#     paddleocr_result_list = paddleocr(db,img_path_list,lang,file_id)
#     pdf_document = fitz.open()
#     page_num = 0
#     for page_box in page_box_list:
#         # 判断是否需要终止此线程
#         if stop_ocr_process(file_id):
#             return ''
#         page = pdf_document.new_page()
#         h , w = page_box.shape
#         print(f"page_box height:{h},width:{w}")
#         paddleocr_result = paddleocr_result_list[page_num]
#         global texts_list
#         texts = texts_list[page_num]

#         texts = do_rectangles_overlap(texts,page_box)
#         l_x1 = 10000
#         for result in paddleocr_result:
#             box = result['boxes'] # box的坐标是放大zoom倍的
#             text = result['txts']
#             x0,y0,x1,y1=box[0][0],box[0][1],box[2][0],box[2][1]
#             cls = page_box[np.clip(int((y0+y1)/2), 0, h-1), np.clip(int((x0+x1)/2), 0, w-1)]
#             # cls = page_box[np.clip(int(y0+zoom), 0, h-1), np.clip(int(x0+zoom), 0, w-1)]
#             if cls == 0:
#                 # print(f"({x0},{y0}) 废弃")
#                 continue
#             if texts[int(cls)] is None:
#                 continue
#             else:
#                 # 判别是否需要换行
#                 if abs(y0 - texts[int(cls)]["xyxy"][2])<4*zoom: # 识别问题导致两个字符串属于不同的类别，会换行其实不用
#                     texts[int(cls)]["text"] += (" " + text) 
#                     # print("增加空格")
#                 else:
#                     texts[int(cls)]["text"] += ("" + text)
#                     texts[int(cls)]['lf'] =  texts[int(cls)]['lf'] + 1 #换行
#         # 插入图片
#         global crop_img_list
#         for c_img in crop_img_list[page_num]:
#             x0,y0,x1,y1 = c_img[0],c_img[1],c_img[2],c_img[3]

#             img = cv2.imread(img_path_list[page_num])
#             cropped = img[y0:y1, x0:x1]  # 裁剪坐标为[y0:y1, x0:x1]
#             crop_path = os.path.join(translated_path,'output','crop')
#             os.makedirs(crop_path,exist_ok=True)
#             crop_img_path = os.path.join(crop_path,'cropped.png')
#             crop_img_path_ = os.path.join(crop_path,'cropped_'+ str(c_img) + '.png')
#             cv2.imwrite(crop_img_path, cropped)
#             cv2.imwrite(crop_img_path_, cropped)
                
#             x0,y0,x1,y1 = int(x0/zoom),int(y0/zoom),int(x1/zoom),int(y1/zoom)
#             # 图片截取有偏移
#             rect = fitz.Rect(x0,y0,x1,y1)
            
#             page.insert_image(
#                 rect,
#                 filename=crop_img_path,
#             )
#         # 插入文字
#         for txt in texts:
#             if txt is not None:
#                 x0, y0, x1, y1 = txt["xyxy"]
#                 if lang not in ['en' ,'french']:
#                     # insert_text = txt["text"].strip()
#                     insert_text = txt["text"].replace(" ", "")
#                 else:
#                     insert_text = txt["text"].strip()
#                 insert_text = insert_text
#                 fontsize = calculate_fontsize(insert_text, int(x1-x0), int(y1-y0), line=txt['lf'])
#                 log.info(f"current  insert fontsize：{fontsize}")
                
#                 html_text = f"""
#                 <html>
#                     <body style="background-color: transparent;">
#                         <p style="font-size:{fontsize}pt; line-height:1.3;text-align:justify; background-color: transparent;height: 100%;"> {insert_text} </p> 
#                     </body>
#                 </html>
#                 """ 
#                 html_text = f"""
#                 <html>
#                     <head>
#                         <style>
#                             html, body {{
#                                 margin: 0;
#                                 padding: 0;
#                                 width: 100%;
#                                 height: 100%;
#                                 box-sizing: border-box;
#                             }}
#                             p {{
#                                 margin: 0;
#                                 padding: 0;
#                                 width: 100%;
#                                 height: 100%;
#                                 box-sizing: border-box;
#                                 /* 添加自动换行处理 */
#                                 overflow-wrap: break-word;
#                             }}
#                         </style>
#                     </head>
#                     <body style="background-color: transparent;">
#                         <p style="font-size:{fontsize}pt; line-height:1.3;text-align:justify; background-color: transparent;height: 100%;"> {insert_text} </p> 
#                     </body>
#                 </html>
#                 """ 
#                 if txt['lf'] == 1: # 一行时，适当放大文本填充方框，以获取更大的字体
#                     # rect = fitz.Rect(int(x0 / zoom - zoom/2 ) , int(y0 / zoom - zoom*2) , int(x1 / zoom) , int(y1 / zoom + zoom *2))
#                     rect = fitz.Rect(int(x0 / zoom) , int(y0 / zoom) , int(x1 / zoom ) , int(y1 / zoom) )
#                 else:
#                     # rect = fitz.Rect(int(x0 / zoom - zoom/2 ) , int(y0 / zoom - zoom/2) , int(x1 / zoom + zoom/2) , int(y1 / zoom + zoom/2) )
#                     rect = fitz.Rect(int(x0 / zoom) , int(y0 / zoom) , int(x1 / zoom ) , int(y1 / zoom) )
#                 print(f"写入区域: {rect}, 文本内容:\n{insert_text}\n")

#                 # 用 insert_htmlbox 替换 insert_textbox
#                 page.insert_htmlbox(rect, html_text,overlay=True)
#                 # page.draw_rect(rect, color=(0, 0, 0), width=0.5)
#         page_num += 1
#         log.info(f"合并的进度为：{(len(img_path_list)*2+page_num)/(len(img_path_list)*3)}")
#         process_translate.set_ocr_process_item(db,file_id,(len(img_path_list)*2+page_num)/(len(img_path_list)*3))
#     if stop_ocr_process(file_id): # 此处需要退出
#         return ''
#     crop_img_list = []
#     texts_list = []
#     # filename = pdf_path.split("/")[-1].split(".pdf")[0]
#     filename = os.path.splitext(os.path.basename(pdf_path))[0]
#     os.makedirs(os.path.join(translated_path,'output','ocr_output'),exist_ok=True)
#     # translated_files/pdf_translated_files/xxx_ocr.pdf
#     ocr_output_path = os.path.join(translated_path,'output','ocr_output',f"{filename}_ocr.pdf")
#     pdf_document.save(ocr_output_path)
#     pdf_document.close()
#     return ocr_output_path

# if __name__ == "__main__":
#     start_time = time.time()
#     # trans("./data/DeepSeek-4.pdf","en")
#     trans_("./data/DeepSeek_ocr_output.pdf","eng")
#     print("--- totally cost %s seconds ---" % (time.time() - start_time))