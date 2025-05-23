"""
构建翻译提示词
"""

DEFAULT_ROLE_PROMPT = """You are a professional translator, proficient in various languages including English, Chinese, Japanese, Korean, German, French, and Spanish. 
You have expertise in specialized vocabulary across different fields and understand the cultural nuances of each language.
Your translations are accurate, natural, and maintain the original tone and style of the text."""

DEFAULT_USER_PROMPT = """
Please translate the following text into {target_language}, ensuring accurate conveyance of the original meaning while maintaining consistency in style and tone.

# Translation Guidelines
1. Maintain the original meaning and context
2. Use appropriate terminology for the target language
3. Keep the same level of formality
4. Preserve any technical terms or proper nouns
5. Ensure natural flow in the target language
6. Consider cultural context and localization needs
7. If the text contains a URL or number, then directly return the URL or number
{appendix_glossary}

# Language-Specific Notes
- For Chinese: Use Simplified Chinese characters and modern standard Mandarin
- For Japanese: Use appropriate keigo (honorific language) when context requires
- For Korean: Use appropriate honorific forms based on context
- For European languages: Maintain proper gender agreement and formal/informal distinctions

# Output Format
Return only the translated text without any additional content or explanation.

Input Text: {text}
Your Translated Text:
"""

from pkg.database import crud
from sqlalchemy.orm import Session
from pkg.projectvar import Projectvar
from pkg.server.process import process_translate
from pkg.database.database import SessionLocal,engine
from pkg.database import models
import os
import sys
# from docx2pdf import convert
# from pdf2image import convert_from_path
import tempfile
from PIL import Image, ImageDraw, ImageFont
import base64
import re
from sqlalchemy import and_
from Levenshtein import distance

gvar = Projectvar()
language_map = {
    "Chinese": "zh",
    "English": "en",
    "Japanese": "ja",
    "Korean": "ko",
    "French": "fr",
}
models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

# 全局变量，用于存储术语映射关系
term_mappings = {}

# 常见英文词形变化规则
PLURAL_RULES = [
    (r'ies$', 'y'),  # 如: studies -> study
    (r's$', ''),     # 如: books -> book
    (r'es$', ''),    # 如: watches -> watch
]

# 常见动词变化规则
VERB_RULES = [
    (r'ing$', ''),   # 如: studying -> study
    (r'ed$', ''),    # 如: studied -> study
    (r'ies$', 'y'),  # 如: studies -> study
    (r's$', ''),     # 如: studies -> study
]

def checkout_translate_item():
    """检查并更新翻译项的状态"""
    try:
        from sqlalchemy import or_
        # 获取所有状态为0（进行中）的翻译项
        translate_items = db.query(models.Translate_item).filter(or_(models.Translate_item.status == 0,models.Translate_item.status == 2)).all()
        
        for item in translate_items:
            # 更新状态为-1（失败）
            item.status = -1
            item.translated_time = ""
            item.translated_path = ""
        
        # 提交更改
        db.commit()
    except Exception as e:
        print(f"更新翻译项状态时出错: {str(e)}")
        db.rollback()

def normalize_term(term):
    """
    使用规则进行词形还原，并去除术语最后一位的标点符号
    """
    if not term:
        return ""
        
    # 去除最后一位的标点符号
    if term and len(term) > 0 and not term[-1].isalnum() and not term[-1].isspace():
        term = term[:-1]
    
    # 标准化处理
    term = term.lower().strip()
    
    # 应用复数规则
    for pattern, replacement in PLURAL_RULES:
        if re.search(pattern, term):
            return re.sub(pattern, replacement, term)
            
    # 应用动词规则
    for pattern, replacement in VERB_RULES:
        if re.search(pattern, term):
            return re.sub(pattern, replacement, term)
            
    return term

def fuzzy_match(text, term, threshold=0.85):
    """使用编辑距离进行模糊匹配"""
    # 标准化两个字符串
    text = normalize_term(text)
    term = normalize_term(term)
    
    # 计算相似度
    max_len = max(len(text), len(term))
    if max_len == 0:
        return False
    similarity = 1 - distance(text, term) / max_len
    return similarity >= threshold

def preprocess_terms(text, terms_list):
    """
    术语预处理函数，将文本中的术语替换为特殊标记
    如果整段文本（或整句）完全等于某个术语，直接返回目标语言翻译，并标记为直接翻译。
    支持词形变化和模糊匹配。
    
    Args:
        text: 要处理的文本
        terms_list: 术语列表，每个术语是一个对象，包含 base_language 和 target_language
    
    Returns:
        tuple: (处理后的文本, 术语映射关系, 是否直接翻译, 直接翻译内容)
    """
    if not terms_list:
        return text, {}, False, None
        
    text_stripped = text.strip()
    
    # 先检查完全匹配
    for term in terms_list:
        if text_stripped == term.base_language.strip():
            return term.target_language, {}, True, term.target_language
            
        # 检查词形还原后的匹配
        if normalize_term(text_stripped) == normalize_term(term.base_language.strip()):
            return term.target_language, {}, True, term.target_language
            
    # 按术语长度降序排序
    sorted_terms = sorted(terms_list, key=lambda x: len(x.base_language), reverse=True)
    
    # 创建术语映射关系
    global term_mappings
    processed_text = text
    
    # 第一步：精确匹配
    for term_idx, term in enumerate(sorted_terms):
        base_term = term.base_language.strip()
        target_term = term.target_language
        marker = f"__TERM_{term_idx}__"
        
        # 在文本中查找所有匹配项
        start_pos = 0
        while True:
            # 查找下一个匹配项
            match_pos = processed_text.find(base_term, start_pos)
            if match_pos == -1:
                break
                
            # 检查是否为单词边界
            is_word_boundary = True
            if match_pos > 0 and processed_text[match_pos-1].isalnum():
                is_word_boundary = False
            if match_pos + len(base_term) < len(processed_text) and processed_text[match_pos + len(base_term)].isalnum():
                is_word_boundary = False
                
            if is_word_boundary:
                # 替换匹配项
                processed_text = processed_text[:match_pos] + marker + processed_text[match_pos + len(base_term):]
                term_mappings[marker] = target_term
                start_pos = match_pos + len(marker)
            else:
                start_pos = match_pos + 1
    
    # 第二步：模糊匹配
    import re
    words = re.findall(r'\b\w+\b|[^\w\s]', processed_text)
    processed_parts = []
    
    for word in words:
        # 只对单词进行模糊匹配，标点符号直接添加
        if word.isalnum() and not word.startswith("__TERM_"):
            matched = False
            for term_idx, term in enumerate(sorted_terms):
                base_term = term.base_language.strip()
                target_term = term.target_language
                marker = f"__TERM_{term_idx}__"
                
                if fuzzy_match(word, base_term):
                    processed_parts.append(marker)
                    term_mappings[marker] = target_term
                    matched = True
                    break
                    
            if not matched:
                processed_parts.append(word)
        else:
            processed_parts.append(word)
            
    processed_text = ' '.join(processed_parts)
                    
    return processed_text, term_mappings, False, None

def postprocess_terms(text, term_mapping):
    """
    术语后处理函数，将特殊标记替换回对应的目标语言术语
    
    Args:
        text: 翻译后的文本
        term_mapping: 术语映射关系
        
    Returns:
        str: 处理后的文本
    """
    if not term_mapping:
        return text
    
    processed_text = text
    
    # 按标记长度降序排序，确保先替换长标记
    sorted_markers = sorted(term_mapping.keys(), key=len, reverse=True)
    
    for marker in sorted_markers:
        target_term = term_mapping[marker]
        processed_text = processed_text.replace(marker, target_term)
    
    return processed_text
            
def get_translation_messages(text: str, base_lang: str, target_language: str = 'English') -> list:
    """获取翻译消息列表
    
    Args:
        text: 要翻译的文本
        target_language: 目标语言
    
    Returns:
        list: 包含系统提示和用户提示的消息列表
    """
    global db, term_mappings
    glossary = gvar.get_glossary()
    
    # 初始化术语映射关系
    term_mappings = {}
    
    if glossary == -1:
        appendix_glossary = ''
        processed_text = text
    else:
        glossary_word = process_translate.get_glossary_word_list_use(db, glossary, language_map.get(base_lang), language_map.get(target_language))
        
        # 术语预处理
        processed_text, term_mappings, is_direct_translation, direct_translation_content = preprocess_terms(text, glossary_word)
        
        # 减少提示词中的术语说明
        appendix_glossary = '8. Use the provided terminology consistently.'
        
        if is_direct_translation:
            return [
                {"role": "system", "content": "__DIRECT_TRANSLATION__"},
                {"role": "user", "content": direct_translation_content},
            ]
    
    return [
        {"role": "system", "content": DEFAULT_ROLE_PROMPT},
        {"role": "user", "content": DEFAULT_USER_PROMPT.format(
            text=processed_text, target_language=target_language, appendix_glossary=appendix_glossary
        )},
    ]



"""
翻译文档标题判断
"""
def has_title_number(title:str) -> bool:
    if re.match(r'一|二|三|四|五|六|七|八|九|十', title):
        return True
    else:
        return False
    
# def convert_docx_first_page_to_image(docx_path, output_image_path=None):
#     """
#     将Word文档的第一页转换为图片
    
#     Args:
#         docx_path (str): Word文档的路径
#         output_image_path (str, optional): 输出图片的路径。如果不指定，将在同目录下创建同名图片
    
#     Returns:
#         str: 输出图片的路径
#     """
#     try:
#         # 如果没有指定输出路径，使用输入文件名（更改扩展名为.png）
#         if output_image_path is None:
#             output_image_path = os.path.splitext(docx_path)[0] + '.png'
        
#         # 创建临时目录
#         with tempfile.TemporaryDirectory() as temp_dir:
#             # 临时PDF文件路径
#             temp_pdf = os.path.join(temp_dir, 'temp.pdf')
            
#             print("正在将Word文档转换为PDF...")
#             # 转换docx到pdf
#             # convert(docx_path, temp_pdf)
            
#             print("正在将PDF转换为图片...")
#             # 将PDF的第一页转换为图片
#             # poppler_path =get_poppler_path()
#             # images = convert_from_path(temp_pdf, first_page=1, last_page=1, poppler_path=poppler_path)
            
#             # 保存第一页为图片
#             images[0].save(output_image_path, 'PNG')
            
#             print(f"转换完成！图片已保存至: {output_image_path}")
#             return output_image_path
            
#     except Exception as e:
#         print(f"转换过程中出现错误: {str(e)}")
#         raise

def txt_to_image(txt_path, output_image_path=None, font_size=20, bg_color=(255, 255, 255), text_color=(0, 0, 0)):
    """
    将txt文件转换为图片
    
    Args:
        txt_path (str): txt文件的路径
        output_image_path (str, optional): 输出图片的路径。如果不指定，将在同目录下创建同名图片
        font_size (int, optional): 字体大小，默认20
        bg_color (tuple, optional): 背景颜色，默认白色
        text_color (tuple, optional): 文字颜色，默认黑色
    
    Returns:
        str: 输出图片的路径
    """
    try:
        # 如果没有指定输出路径，使用输入文件名（更改扩展名为.png）
        if output_image_path is None:
            output_image_path = os.path.splitext(txt_path)[0] + '.png'
        
        # 读取txt文件
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 创建字体对象
        try:
            font = ImageFont.truetype("simhei.ttf", font_size)  # Windows默认中文字体
        except:
            font = ImageFont.load_default()  # 如果找不到字体，使用默认字体
        
        # 计算文本大小
        dummy_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        text_lines = text.split('\n')
        max_width = 0
        total_height = 0
        
        for line in text_lines:
            bbox = dummy_draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            max_width = max(max_width, line_width)
            total_height += line_height
        
        # 添加边距
        padding = 20
        image_width = max_width + padding * 2
        image_height = total_height + padding * 2
        
        # 创建图片
        image = Image.new('RGB', (image_width, image_height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # 绘制文本
        y = padding
        for line in text_lines:
            draw.text((padding, y), line, font=font, fill=text_color)
            bbox = draw.textbbox((padding, y), line, font=font)
            y += bbox[3] - bbox[1]
        
        # 保存图片
        image.save(output_image_path)
        print(f"转换完成！图片已保存至: {output_image_path}")
        return output_image_path
        
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")
        raise

# def pdf_first_page_to_image(pdf_path, output_image_path=None, dpi=200):
#     """
#     将PDF的第一页转换为图片
    
#     Args:
#         pdf_path (str): PDF文件的路径
#         output_image_path (str, optional): 输出图片的路径。如果不指定，将在同目录下创建同名图片
#         dpi (int, optional): 图片分辨率，默认200
    
#     Returns:
#         str: 输出图片的路径
#     """
#     try:
#         # 检查文件是否存在
#         if not os.path.exists(pdf_path):
#             raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
            
#         # 如果没有指定输出路径，使用输入文件名（更改扩展名为.png）
#         if output_image_path is None:
#             output_image_path = os.path.splitext(pdf_path)[0] + '.png'
            
#         # 检查文件扩展名
#         if not pdf_path.lower().endswith('.pdf'):
#             raise ValueError("输入文件必须是PDF格式")
            
#         print("正在将PDF转换为图片...")
        
#         # 设置poppler路径（如果需要）
#         poppler_path = get_poppler_path()
#         if not os.path.exists(os.path.join(poppler_path, "pdftoppm")):
#             poppler_path = None  # 系统 PATH 或 fallback（如打包的 internal 路径）

#         # 转换PDF的第一页为图片
#         images = convert_from_path(
#             pdf_path,
#             dpi=dpi,
#             first_page=1,
#             last_page=1,
#             poppler_path=poppler_path
#         )
        
#         # 保存第一页为图片
#         images[0].save(output_image_path, 'PNG')
        
#         print(f"转换完成！图片已保存至: {output_image_path}")
#         return output_image_path
        
#     except Exception as e:
#         print(f"转换过程中出现错误: {str(e)}")
#         raise

def image_to_base64(image_path):
    """
    将图片转换为base64格式
    
    Args:
        image_path (str): 图片文件的路径
    
    Returns:
        str: base64编码的字符串
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
            
        # 检查文件扩展名
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError("不支持的文件格式，支持的格式有: " + ", ".join(valid_extensions))
            
        print("正在将图片转换为base64...")
        
        # 读取图片文件
        with open(image_path, 'rb') as image_file:
            # 读取文件内容
            image_data = image_file.read()
            
            # 转换为base64
            base64_data = base64.b64encode(image_data)
            
            # 转换为字符串
            base64_string = base64_data.decode('utf-8')
            
            print("转换完成！")
            return base64_string
            
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")
        raise

def reverse_word_item(word_item:list, base_lang:str, target_lang:str) -> list:
    """
    反转术语列表中的语言顺序
    
    Args:
        word_item: 术语列表
        base_lang: 期望的源语言代码
        target_lang: 期望的目标语言代码
        
    Returns:
        list: 处理后的术语列表
    """
    for item in word_item:
        # 如果当前项的语言代码与期望的相同，保持不变
        if item.base_lang == base_lang and item.target_lang == target_lang:
            continue
            
        # 交换语言代码
        item.base_lang, item.target_lang = item.target_lang, item.base_lang
        
        # 交换术语内容
        item.base_language, item.target_language = item.target_language, item.base_language
        
    return word_item


