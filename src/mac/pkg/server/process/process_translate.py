from sqlalchemy.orm import Session
from pkg.database import models

## 翻译逻辑
def create_translate_text_item(db:Session,origin_text:str,transed_text:str,base_lang:str,target_lang:str,create_time:str):
    db_translate_text_item = models.Translate_text_item(
        origin_text = origin_text,
        transed_text = transed_text,
        base_lang = base_lang,
        target_lang = target_lang,
        create_time = create_time
    )
    db.add(db_translate_text_item)
    db.commit()
    db.refresh(db_translate_text_item)

def get_translate_text_item_list(db:Session):
    translate_text_item_list = db.query(models.Translate_text_item).all()
    return translate_text_item_list

def delete_translate_text_item(db:Session,id:int):
    db_translate_text_item = db.query(models.Translate_text_item).filter(models.Translate_text_item.id==id).first()
    if db_translate_text_item:
        db.delete(db_translate_text_item)
        db.commit()
        return True
    else:
        return False


def create_translate_item(db:Session,fileid:str,file_name:str,base_lang:str,target_lang:str,source_file_path:str,upload_time:str,status:int,process:float,image_base64:str):
    db_translate_item = models.Translate_item(
        fileid = fileid,
        file_name = file_name,
        base_lang = base_lang,
        target_lang = target_lang,
        source_file_path = source_file_path,
        upload_time = upload_time,
        status = status,
        process = process,
        pic = image_base64
    )
    db.add(db_translate_item)
    db.commit()
    db.refresh(db_translate_item)
    return True

def update_translate_item_img(db:Session,fileid:str,image_base64:str):
    db_translate_item = db.query(models.Translate_item).filter(models.Translate_item.fileid==fileid).first()
    if db_translate_item:
        db_translate_item.pic = image_base64
    db.add(db_translate_item)
    db.commit()
    db.refresh(db_translate_item)
    return True

def update_translate_item(db:Session,fileid:str,status:int,porcess:float,base_lang:str,target_lang:str,translated_path:str = '',translated_time:str=''):
    db_translate_item = db.query(models.Translate_item).filter(models.Translate_item.fileid==fileid).first()
    if db_translate_item:
        if translated_path != '':
            db_translate_item.translated_file_path = translated_path
        db_translate_item.status = status
        db_translate_item.process = porcess
        db_translate_item.base_lang = base_lang
        db_translate_item.target_lang = target_lang
        db_translate_item.translated_time = translated_time
    db.commit()
    db.refresh(db_translate_item)
    return True

def get_translate_item_process(db:Session,fileid:str):
    db_translate_item = db.query(models.Translate_item).filter(models.Translate_item.fileid==fileid).first()
    if db_translate_item:
        return db_translate_item.process
    else:
        return 0

def update_translate_finalpath(db:Session,fileid:str,translated_path:str,status:int,translated_time:str):
    db_translate_item = db.query(models.Translate_item).filter(models.Translate_item.fileid==fileid).first()
    if db_translate_item:
        db_translate_item.translated_file_path = translated_path
        db_translate_item.status = status
        db_translate_item.translated_time = translated_time
    db.commit()
    db.refresh(db_translate_item)
    return True



def get_translate_item_list(db:Session):
    translate_item_list = db.query(models.Translate_item).all()
    return translate_item_list

def get_translateitem_progress(db:Session,fileid:str):
    db_translate_item = db.query(models.Translate_item).filter(models.Translate_item.fileid==fileid).first()
    return db_translate_item

import threading
lock = threading.Lock()
def set_translate_process_item(db:Session,fileid:str,process:float):
    # 在翻译pdf中多线程会对数据库频繁地写入，多线程写入会出现重复提交事务的错误
    # 因此对db资源进行加锁，保证不会重复提交
    lock.acquire()
    db_translate_item = db.query(models.Translate_item).filter(models.Translate_item.fileid==fileid).first()
    if db_translate_item:
        db_translate_item.process = process
    db.commit()
    db.refresh(db_translate_item)
    lock.release()
    return True

# 更新ocr状态
def set_ocr_status(db:Session,file_id:str,ocr_status:bool):
    '''
    ocr_status: True or False
    '''
    db_translate_item = db.query(models.Translate_item).filter(models.Translate_item.fileid==file_id).first()
    if db_translate_item:
        db_translate_item.ocr_status = ocr_status 
    db.commit()
    db.refresh(db_translate_item)
    return True

# 更新ocr进度
def set_ocr_process_item(db:Session,file_id:str,process:float):
    db_translate_item = db.query(models.Translate_item).filter(models.Translate_item.fileid==file_id).first()
    if db_translate_item:
        db_translate_item.ocr_process = process
    db.commit()
    db.refresh(db_translate_item)
    return True

def set_translate_status_item(db:Session,fileid:str,status:int):
    db_translate_item = db.query(models.Translate_item).filter(models.Translate_item.fileid==fileid).first()
    if db_translate_item:
        db_translate_item.status = status
    db.commit()
    db.refresh(db_translate_item)
    return True

def get_translate_status_item(db:Session,fileid:str):
    db_translate_item = db.query(models.Translate_item).filter(models.Translate_item.fileid==fileid).first()
    return db_translate_item

def get_translate_item(db:Session,fileid:str):
    db_translate_item = db.query(models.Translate_item).filter(models.Translate_item.fileid==fileid).first()
    return db_translate_item

def delete_translate_item(db:Session,fileid:str):
    db_translate_item = db.query(models.Translate_item).filter(models.Translate_item.fileid==fileid).first()
    if db_translate_item:
        db.delete(db_translate_item)
        db.commit()
        return True
    else:
        return False

## 术语表逻辑
def create_glossary_item(db:Session,total_num_words:int,name:str,field:str):
    db_glossary_item = models.Glossary_item(
        name = name,
        field = field,
        total_num_words = total_num_words
    )
    db.add(db_glossary_item)
    db.commit()
    db.refresh(db_glossary_item)
    return True

def set_glossary_item(db:Session,id:int,total_num_words:int):
    db_glossary_item = db.query(models.Glossary_item).filter(models.Glossary_item.id==id).first()
    if db_glossary_item:
        db_glossary_item.total_num_words = total_num_words
        db.add(db_glossary_item)
        db.commit()
        db.refresh(db_glossary_item)
        return True
    else:
        return False

    
def get_glossary_item_list(db:Session):
    glossary_item_list = db.query(models.Glossary_item).all()
    return glossary_item_list
 
def delete_glossary_item(db:Session,id:int):
    db_glossary_item = db.query(models.Glossary_item).filter(models.Glossary_item.id==id).first()
    db_glossary_word = db.query(models.Glossary_page).filter(models.Glossary_page.glossary_id==id).all()
    for item in db_glossary_word:
        db.delete(item)
        db.commit()
    if db_glossary_item:
        db.delete(db_glossary_item)
        db.commit()
        return True
    else:
        return False
    
def create_glossary_word(db:Session,base_lang:str,base_language:str,target_lang:str,target_language:str,glossary_id:int):
    db_glossary_word = models.Glossary_page(
        base_lang=base_lang,
        base_language=base_language,
        target_lang=target_lang,
        target_language=target_language,
        glossary_id=glossary_id
    )
    db.add(db_glossary_word)
    db.commit()
    db.refresh(db_glossary_word)
    return True

def get_glossary_word_list(db: Session,glossary_id: int):
    db_glossary_word_list = db.query(models.Glossary_page).filter(models.Glossary_page.glossary_id == glossary_id).all()
    return db_glossary_word_list

def get_glossary_word_list_use(db:Session,glossary_id: int,base_lang:str,target_lang:str):
    db_glossary_list = db.query(models.Glossary_page).filter(models.Glossary_page.glossary_id == glossary_id).filter(models.Glossary_page.base_lang == base_lang).filter(models.Glossary_page.target_lang == target_lang).all()
    db_glossary_list_resverse = db.query(models.Glossary_page).filter(models.Glossary_page.glossary_id == glossary_id).filter(models.Glossary_page.base_lang == target_lang).filter(models.Glossary_page.target_lang == base_lang).all()
    for item in db_glossary_list_resverse:
        db_glossary_list.append(item)
    return db_glossary_list
def set_glossary_word(db: Session, base_lang: str, base_language: str, target_lang: str, target_language: str, id:int):
    db_glossary_word = db.query(models.Glossary_page).filter(models.Glossary_page.id == id).first()
    db_glossary_word.base_lang = base_lang
    db_glossary_word.base_language = base_language
    db_glossary_word.target_lang = target_lang
    db_glossary_word.target_language = target_language
    db.commit()
    db.refresh(db_glossary_word)
    return True

def get_glossary_word(db: Session, base_language: str):
    db_glossary_word = db.query(models.Glossary_page).filter(models.Glossary_page.base_language == base_language).all()
    return db_glossary_word

def delete_glossary_word(db: Session, id:int):
    db_glossary_word = db.query(models.Glossary_page).filter(models.Glossary_page.id == id).first()
    db.delete(db_glossary_word)
    db.commit()
    return True

