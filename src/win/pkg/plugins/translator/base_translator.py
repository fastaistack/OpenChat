from openai import OpenAI
import os
import re
import ollama
from pkg.plugins.translator.utils import get_translation_messages,has_title_number, postprocess_terms, term_mappings,preprocess_terms, reverse_word_item,language_map
from ...logger import Log
from pkg.projectvar import Projectvar
from pkg.database.database import SessionLocal
from pkg.server.process.process_translate import get_glossary_word_list_use
gvar = Projectvar()
db = SessionLocal()
log = Log()


class BaseTranslator:
    name = "base"
    envs = {}
    lang_map = {}
    
    def __init__(self, lang_in, lang_out, model):
        lang_in = self.lang_map.get(lang_in.lower(), lang_in)
        lang_out = self.lang_map.get(lang_out.lower(), lang_out)
        self.lang_in = lang_in
        self.lang_out = lang_out
        self.model = model
    
    def translate(self, text):
        pass
    
    def prompt(self, text):
        
        pdf_prompt = f"""
            You are a professional, authentic machine translation engine.
            Only Output the translated text, do not include any other text.
            \n\n
            Translate the following markdown source text to {self.lang_out}.
            Keep the formula notation {{v*}} unchanged.
            Output translation directly without any additional text.
            \n\n
            Source Text: {text}
            \n\n
            Translated Text:
        """
        doc_prompt = f"""
            将输入的内容翻译成{self.lang_out}，并确保符合{self.lang_out}语言习惯。
            如果文本包含URL或数字，则直接返回URL或数字。
            你可以调整语气和风格，并考虑到某些词语的文化内涵和地区差异。
            仅输出翻译结果，不输出任何注释或解释。
            翻译的文本为：{text}"
        """

        return [
            {
                "role": "user",
                "content":pdf_prompt, 
            }
        ]
        
    """基础翻译器类"""
    def translate_text(self, text: str,base_lang:str, target_language: str) -> str:
        """翻译文本
        
        Args:
            text: 要翻译的文本
            target_language: 目标语言
            
        Returns:
            翻译后的文本
        """
        raise NotImplementedError
    
class OllamaTranslator(BaseTranslator):
    def __init__(self, config: dict):
        """初始化OpenAI翻译器
        
        Args:
            config: OpenAI配置
        """
        self.client = ollama.Client(
            host=config.get('url')
        )
        self.model = config.get('model_selected')

    def translate_text(self, text:str,base_lang:str,target_lang:str):
        if has_title_number(text):
            title = text[0:2]
            main_text = text[2:]
        else:
            main_text = text
        glossary = gvar.get_glossary()
        if glossary != -1:
            glossary_word_reverse = get_glossary_word_list_use(db, glossary, language_map.get(base_lang), language_map.get(target_lang))
            glossary_word = reverse_word_item(glossary_word_reverse,language_map.get(base_lang),language_map.get(target_lang))
            main_text = preprocess_terms(main_text,glossary_word)
        data = get_translation_messages(text=main_text,base_lang=base_lang,target_language=target_lang)
        # 检查是否为直接翻译
        if data and data[0]["content"] == "__DIRECT_TRANSLATION__":
            return (title if has_title_number(text) else "") + data[1]["content"]
        try:
            response = self.client.chat(
                model=self.model,
                messages=data,
                options = {
                    "temperature": 0.3,
                    "top_p": 1,
                    "repeat_penalty": 1,
                },
                stream=False
            )
            final_text = ""
            if has_title_number(text):
                final_text = title + re.sub(r"^<think>.+?</think>","",response["message"]["content"], count=1, flags=re.DOTALL).strip()
            else:
                final_text = re.sub(r"^<think>.+?</think>","",response["message"]["content"], count=1, flags=re.DOTALL).strip()
            if glossary != -1:
                return postprocess_terms(final_text,term_mappings)
            else:
                return final_text
        except Exception as e:
            log.error(f"Ollama translation error: {str(e)}")
            raise
    
class OpenAITranslator(BaseTranslator):
    """OpenAI翻译器"""
    def __init__(self, config: dict):
        """初始化OpenAI翻译器
        
        Args:
            config: OpenAI配置
        """
        self.client = OpenAI(
            api_key=config.get('api_key'),
            base_url=config.get('url')
        )
        self.model = config.get('model_selected')

    def translate_text(self, text: str,base_lang:str, target_language: str) -> str:
        """使用OpenAI API翻译文本"""
        if has_title_number(text):
            title = text[0:2]
            main_text = text[2:]
        else:
            main_text = text
        glossary = gvar.get_glossary()
        if glossary != -1:
            glossary_word_reverse = get_glossary_word_list_use(db, glossary, language_map.get(base_lang), language_map.get(target_language))
            glossary_word = reverse_word_item(glossary_word_reverse,language_map.get(base_lang),language_map.get(target_language))
            main_text,term_mappings, is_direct_translation, direct_translation_content = preprocess_terms(main_text,glossary_word)
            if is_direct_translation:
                return (title if has_title_number(text) else "") + direct_translation_content
        messages = get_translation_messages(main_text,base_lang=base_lang,target_language = target_language)
        # 检查是否为直接翻译
        if messages and messages[0]["content"] == "__DIRECT_TRANSLATION__":
            return (title if has_title_number(text) else "") + messages[1]["content"]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1500,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            translated_text = re.sub(r"^<think>.+?</think>","",response.choices[0].message.content.strip(), count=1, flags=re.DOTALL).strip()
            if glossary != -1:
                translated_text = postprocess_terms(translated_text, term_mappings)
            if has_title_number(text):
                return title + translated_text
            else:
                return translated_text
        except Exception as e:
            log.error(f"OpenAI translation error: {str(e)}")
            raise

class OllamaPDFTranslator(BaseTranslator):
    name = "ollama"
    # envs = {
    #     "OLLAMA_HOST": "http://127.0.0.1:11434",
    #     # "OLLAMA_MODEL": "gemma2",
    #     "OLLAMA_MODEL": "deepseek-r1:1.5b",
    # }

    def __init__(self, lang_in:str, lang_out:str,model:str,base_url:str,api_key:str=None):
        # if not model:
        #     model = os.getenv("OLLAMA_MODEL", self.envs["OLLAMA_MODEL"])
        super().__init__(lang_in, lang_out, model)
        self.options = {
            "temperature": 0,# 随机采样可能会打断公式标记
            "num_predict": 2000,
            }  
        self.client = ollama.Client(host=base_url)

    def translate(self, text):
        try:
            response = self.client.chat(
                model=self.model,
                options=self.options,
                messages=self.prompt(text.replace('','l')),
            )
            
            content = self._remove_cot_content(response.message.content or "")
            return content.strip()
        except Exception as e:
            log.error(e)
            raise e
    
    @staticmethod
    def _remove_cot_content(content: str) -> str:
        """Remove text content with the thought chain from the chat response

        :param content: Non-streaming text content
        :return: Text without a thought chain
        """
        return re.sub(r"^<think>.+?</think>", "", content, count=1, flags=re.DOTALL)


class OpenAIPDFTranslator(BaseTranslator):
    name = "openai"
    envs = {
        "OPENAI_BASE_URL": "https://api.openai.com/v1",
        "OPENAI_API_KEY": None,
        "OPENAI_MODEL": "gpt-4o-mini",
    }

    def __init__(self, lang_in, lang_out, model,service = None, base_url=None, api_key=None,):
        if not model:
            model = os.getenv("OPENAI_MODEL", self.envs["OPENAI_MODEL"])
        # if not base_url:
        #     base_url = os.getenv("OPENAI_BASE_URL", self.envs["OPENAI_BASE_URL"])
        super().__init__(lang_in, lang_out, model)
        self.options = {"temperature": 0}  # 随机采样可能会打断公式标记
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def translate(self, text) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                **self.options,
                messages=self.prompt(text),
                max_tokens=4096,
            )
            content = self._remove_cot_content(response.choices[0].message.content.strip() or "")
            return content
            return response.choices[0].message.content.strip()
        except Exception as e:
            log.error(f"OpenAIPDFTranslator,error:{str(e)}")
            raise e
    
    @staticmethod
    def _remove_cot_content(content: str) -> str:
        """Remove text content with the thought chain from the chat response

        :param content: Non-streaming text content
        :return: Text without a thought chain
        """
        # print("调用_remove_cot_content")
        return re.sub(r"^<think>.+?</think>", "", content, count=1, flags=re.DOTALL)



class TranslationClient:
    """翻译客户端基类"""
    def __init__(self, translator: BaseTranslator, max_retries: int = 3):
        self.translator = translator
        self.max_retries = max_retries

    def translate(self, text: str,base_lang:str, target_language: str = 'English') -> str:
        """翻译方法"""
        for attempt in range(self.max_retries):
            try:
                return self.translator.translate_text(text,base_lang, target_language)
            except Exception as e:
                log.error(f"Translation attempt {attempt + 1} failed: {str(e)}")
                if attempt + 1 == self.max_retries:
                    return "Translation failed"