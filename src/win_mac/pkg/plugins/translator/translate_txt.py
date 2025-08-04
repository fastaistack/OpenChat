import os
import logging
from typing import Optional
from pkg.projectvar import Projectvar
from pkg.plugins.translator.base_translator import TranslationClient,OllamaTranslator,BaseTranslator,OpenAITranslator
from pkg.server.process.process_translate import set_translate_process_item,update_translate_finalpath,get_glossary_word_list_use
from pkg.database.database import SessionLocal,engine
from pkg.database import models
import time
from pkg.plugins.translator.utils import preprocess_terms, postprocess_terms, reverse_word_item,language_map

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

gvar = Projectvar()
models.Base.metadata.create_all(bind=engine)
db = SessionLocal()

def translate_txt(input_file: str, output_file: Optional[str] = None, 
                  translator: Optional[BaseTranslator] = None,
                  base_lang:str = 'Chinese',
                  target_language: str = 'English',
                  fileid:str="") -> str:
    """
    翻译文档的主入口函数
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径（可选）
        translator: 翻译客户端（可选）
        target_language: 目标语言（默认为英语）
    
    Returns:
        str: 输出文件路径
    """
    update_translate_finalpath(db=db,fileid=fileid,translated_path="",status=0,translated_time="")
    if not output_file:
        file_name, file_ext = os.path.splitext(input_file)
        output_file = f"{file_name}_translated{file_ext}"

    config = gvar.get_model_info()
    if config.get('api_key') == 'ollama':
        translator = OllamaTranslator(config)
    else:
        translator = OpenAITranslator(config)
    
    text = []
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            text.append(line)
    print(text)
    total_num = len(text)
    print("total_num:",total_num)
    current_num = -1
    localtime = time.time()
    translation_Client = TranslationClient(translator)
    tran_text = []
    
    # 术语预处理
    # glossary = gvar.get_glossary()
    # if glossary != -1:
    #     glossary_word_reverse = get_glossary_word_list_use(db, glossary, language_map.get(base_lang), language_map.get(target_language))
    #     glossary_word = reverse_word_item(glossary_word_reverse,language_map.get(base_lang),language_map.get(target_language))
    #     # 预处理所有文本
    #     processed_text = []
    #     direct_translate_flags = []
    #     direct_translate_contents = []
    #     for item in text:
    #         if item == '\n' or item == '':
    #             processed_text.append(item)
    #             direct_translate_flags.append(False)
    #             direct_translate_contents.append(None)
    #         else:
    #             processed_item, term_mappings, is_direct_translation, direct_translation_content = preprocess_terms(item, glossary_word)
    #             processed_text.append(processed_item)
    #             direct_translate_flags.append(is_direct_translation)
    #             direct_translate_contents.append(direct_translation_content)
    #     text = processed_text
    
    for idx, item in enumerate(text):
        current_num += 1
        if item == '\n':
            tran_text.append('\n')
            continue
        elif item == '':
            continue
        isneedstop = gvar.get_needstop()
        if fileid in isneedstop:
            break
        # 直接翻译
        # if glossary != -1 and direct_translate_flags[idx]:
        #     result = direct_translate_contents[idx]
        # else:
        result = translation_Client.translate(item,base_lang, target_language) 
            # 术语后处理
            # if glossary != -1:
            #     result = postprocess_terms(result, term_mappings)
        tran_text.append(result)
        tran_text.append('\n')
        print("current_num:",current_num)
        set_translate_process_item(db,fileid,current_num/total_num)
    isneedstop = gvar.get_needstop()  
    if fileid in isneedstop:
        update_translate_finalpath(db=db,fileid=fileid,translated_path="",status=-1,translated_time='')
        set_translate_process_item(db,fileid,0)
        gvar.delete_needstop(fileid)
        return  
    else: 
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(tran_text)
        
        update_translate_finalpath(db=db,fileid=fileid,translated_path=output_file,status=1,translated_time=time.time()-localtime)
        set_translate_process_item(db,fileid,(current_num+1)/total_num)
        return output_file