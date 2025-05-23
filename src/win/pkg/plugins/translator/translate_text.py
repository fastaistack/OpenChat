import logging
import re
from pkg.plugins.translator.base_translator import TranslationClient,OllamaTranslator,OpenAITranslator
from pkg.projectvar import Projectvar

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

gvar = Projectvar()

Language_map = {
    'zh':'Chinese',
    'en':'English',
    'ja':'Japanese',
    'ko':'Korean',
    'fr':'French',
    'de':'German',
}

def translate_text(target_text:str, base_lang:str, target_language:str = 'English') -> str:
    """
    翻译文本的主入口函数，保留原始段落格式和特殊内容

    Args:
        target_text: 要翻译的文本
        base_lang: 原始语言
        target_language: 目标语言（默认为英语）

    Returns:
        str: 翻译后的文本，保留原始段落格式和特殊内容
    """
    if not target_text or len(target_text.strip()) <= 1:
        return target_text
    
    try:
        # 设置翻译配置
        config = gvar.get_model_info()
        if config.get('api_key') == 'ollama':
            translator = OllamaTranslator(config)
        else:
            translator = OpenAITranslator(config)
        
        translation_Client = TranslationClient(translator)
        
        # 按段落分割文本
        paragraphs = target_text.split('\n')
        translated_paragraphs = []
        
        # 逐段翻译
        for paragraph in paragraphs:
            try:
                if not paragraph.strip():
                    # 保留空行
                    translated_paragraphs.append(paragraph)
                    continue
                
                # 预处理段落，保护特殊内容
                processed_paragraph, placeholders = preprocess_text(paragraph)
                
                # 翻译处理后的段落
                translated_paragraph = translation_Client.translate(processed_paragraph, base_lang, target_language)
                
                # 后处理段落，恢复特殊内容
                final_paragraph = postprocess_text(translated_paragraph, placeholders)
                
                translated_paragraphs.append(final_paragraph)
            except Exception as e:
                logger.error(f"处理段落时出错: {str(e)}")
                # 出错时保留原段落
                translated_paragraphs.append(paragraph)
        
        # 使用换行符连接翻译后的段落，保留原始段落结构
        result = '\n'.join(translated_paragraphs)
        return result
    except Exception as e:
        logger.error(f"翻译过程出错: {str(e)}")
        # 出错时返回原文本
        return target_text

# 以下是可选的额外优化函数

def preprocess_text(text):
    """文本预处理，保留特殊格式"""
    # 安全的哈希映射
    placeholders = {}
    placeholder_counter = 0
    
    def create_placeholder(prefix, content):
        nonlocal placeholder_counter
        placeholder = f"__{prefix}_{placeholder_counter}__"
        placeholders[placeholder] = content
        placeholder_counter += 1
        return placeholder
    
    # 保护换行符
    text = text.replace('\n', '__NEWLINE__')
    
    # 保护URL
    url_pattern = r'(https?://[^\s]+)'
    def url_replacer(match):
        return create_placeholder("URL", match.group(0))
    text = re.sub(url_pattern, url_replacer, text)
    
    # 保护Email
    email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    def email_replacer(match):
        return create_placeholder("EMAIL", match.group(0))
    text = re.sub(email_pattern, email_replacer, text)
    
    # 保护代码片段（使用``或```包围的内容）
    code_pattern_inline = r'`([^`]+)`'
    def code_inline_replacer(match):
        return create_placeholder("CODE_INLINE", match.group(0))
    text = re.sub(code_pattern_inline, code_inline_replacer, text)
    
    code_pattern_block = r'```[\s\S]*?```'
    def code_block_replacer(match):
        return create_placeholder("CODE_BLOCK", match.group(0))
    text = re.sub(code_pattern_block, code_block_replacer, text)
    
    # 保护Markdown列表（有序和无序）
    list_pattern = r'^(\s*[-*+]\s+|\s*\d+\.\s+)(.+)$'
    def list_replacer(match):
        return f"{match.group(1)}{create_placeholder('LIST_CONTENT', match.group(2))}"
    text = re.sub(list_pattern, list_replacer, text, flags=re.MULTILINE)
    
    # 保护Markdown标题
    heading_pattern = r'^(#{1,6}\s+)(.+)$'
    def heading_replacer(match):
        return f"{match.group(1)}{create_placeholder('HEADING_CONTENT', match.group(2))}"
    text = re.sub(heading_pattern, heading_replacer, text, flags=re.MULTILINE)
    
    # 保护Markdown加粗和斜体
    bold_pattern = r'\*\*(.+?)\*\*'
    def bold_replacer(match):
        return create_placeholder("BOLD", match.group(0))
    text = re.sub(bold_pattern, bold_replacer, text)
    
    italic_pattern = r'\*(.+?)\*'
    def italic_replacer(match):
        return create_placeholder("ITALIC", match.group(0))
    text = re.sub(italic_pattern, italic_replacer, text)
    
    # 保护数字和特殊标识符
    numbers_pattern = r'(\b\d+(\.\d+)?\b)'
    def number_replacer(match):
        return create_placeholder("NUM", match.group(0))
    text = re.sub(numbers_pattern, number_replacer, text)
    
    # 保护文件路径
    path_pattern = r'([a-zA-Z]:\\[^<>:"/\\|?*\n]+|/[^<>:"/\\|?*\n]+)'
    def path_replacer(match):
        return create_placeholder("PATH", match.group(0))
    text = re.sub(path_pattern, path_replacer, text)
    
    return text, placeholders

def postprocess_text(text, placeholders):
    """后处理文本，恢复特殊格式"""
    # 按照占位符长度降序排序，确保更长的占位符先被替换
    # 这避免了较短占位符被较长占位符部分匹配的问题
    for placeholder, original in sorted(placeholders.items(), key=lambda x: len(x[0]), reverse=True):
        text = text.replace(placeholder, original)
    
    # 恢复换行符（最后处理换行符以避免格式问题）
    text = text.replace('__NEWLINE__', '\n')
    
    return text

