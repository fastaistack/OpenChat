from .biz_enum import ModelStatus, ModelType
from ...logger import Log
from typing import List
from sqlalchemy import or_
import importlib
from pkg.projectvar.projectvar import Projectvar
import threading
from pkg.projectvar import Projectvar
from ollama import Client
import json

gvar = Projectvar()
log = Log()
gavr = Projectvar()


def get_download_model_list():
    try:
        from pkg.database import models
        from pkg.database.database import SessionLocal
        db = SessionLocal()
        models = db.query(models.Model).filter(models.Model.status != ModelStatus.NOT_DOWNLOAD.status,
                                               models.Model.status != ModelStatus.DOWNLOADING.status,
                                               models.Model.status != ModelStatus.DOWNLOADED_FAILED.status,
                                               models.Model.status != ModelStatus.DOWNLOAD_WATING.status,
                                               models.Model.status != ModelStatus.DOWNLOAD_PAUSED.status,
                                               models.Model.type == ModelType.INFERENCE.value
                                               ).all()
        return models
    except Exception as ex:
        log.error(f"get_model_list error,{str(ex)}")
        return []

def get_download_embedding_model_list():
    try:
        from pkg.database import models
        from pkg.database.database import SessionLocal
        with SessionLocal() as db:
            model_list = db.query(models.Model).filter(models.Model.status == ModelStatus.DOWNLOAD_SUCCESS.status,
                                                   models.Model.type == ModelType.EMBEDDING.value,
                                                   ).all()
            result = []
            for model in model_list:
                result.append({
                    "id": model.id,
                    "name": model.name,
                    "local_path": model.modelscope_path, # 直接给modelscope_path，而不是全路径，模型迁移后地址会变
                })
            return result
    except Exception as ex:
        log.error(f"get_embedding_model_list error,{str(ex)}")

def get_download_ollama_embedding_model_list():
    try:
        from pkg.database import models
        from pkg.database.database import SessionLocal
        result = []
        id = 1
        with SessionLocal() as db:
            model_info = db.query(models.Model).filter(models.Model.key == 'ollama').first()
            ollama = Client(host=model_info.url)
            model_list = ollama.list()
            ollama_support_embedding_model_list = ['nomic-embed-text',
                                                'mxbai-embed-large',
                                                'snowflake-arctic-embed',
                                                'snowflake-arctic-embed2',
                                                'granite-embedding',
                                                'all-minilm',
                                                'bge-large',
                                                'jeffh/intfloat-multilingual-e5-large-instruct',
                                                'shaw/dmeta-embedding-zh',
                                                ]
            for model in model_list.models:
                # print(model)
                if model.model.split(':')[0] in ollama_support_embedding_model_list:
                    result.append({
                        "id": id,
                        "name": model.model,
                        "local_path": model.model, # 直接给modelscope_path，而不是全路径，模型迁移后地址会变
                    })
                    id = id + 1
            return result
    except Exception as ex:
        import traceback
        print(traceback.format_exc())
        log.error(f"get_embedding_model_list error,{str(ex)}")

def get_download_model_list_by_type(type: str):
    try:
        from pkg.database import models
        from pkg.database.database import SessionLocal
        with SessionLocal() as db:
            models = db.query(models.Model).filter(models.Model.status == ModelStatus.DOWNLOAD_SUCCESS.status,
                                                   models.Model.type == type).all()
        return models
    except Exception as ex:
        log.error(f"get_embedding_model_list error,{str(ex)}")
        return []


def get_loaded_model_info():
    try:
        from pkg.database import models
        from pkg.database.database import SessionLocal
        with SessionLocal() as db:
            models = db.query(models.Model).filter(models.Model.status == ModelStatus.LOAD_SUCCESS.status).all()
            return models
    except Exception as ex:
        log.error(f"get_model_list error,{str(ex)}")
        return []


def get_model_info_by_status(status_list: []):
    try:
        from pkg.database import models
        from pkg.database.database import SessionLocal
        with SessionLocal() as db:
            models = db.query(models.Model).filter(models.Model.status.in_(status_list)).all()
            return models
    except Exception as ex:
        log.error(f"get_model_list error,{str(ex)}")
        return None


def load_model(model_id: int, precision_selected: str, type: int):
    try:
        from pkg.database import models
        from pkg.database.database import SessionLocal
        with SessionLocal() as db:
            model_info = db.query(models.Model).filter(models.Model.id == model_id).first()
            db.query(models.Model).filter(or_(models.Model.status == ModelStatus.LOAD_SUCCESS.status,
                                              models.Model.status == ModelStatus.LOAD_FAILED.status,
                                              models.Model.status == ModelStatus.LOADING.status)).update(
                {"status": ModelStatus.NOT_LOAD.status, "precision_selected": ""})
            url = model_info.url
            api_key = model_info.api_key
            precision_list= []
            ollama_support_embedding_model_list = ['nomic-embed-text',
                                            'mxbai-embed-large',
                                            'snowflake-arctic-embed',
                                            'snowflake-arctic-embed2',
                                            'granite-embedding',
                                            'all-minilm',
                                            'bge-large',
                                            'jeffh/intfloat-multilingual-e5-large-instruct',
                                            'shaw/dmeta-embedding-zh',
                                            ]
            if model_info.key == 'ollama':
                ollama = Client(host=url)
                model_list = ollama.list()
                for model in model_list.models:
                    if model.model.split(':')[0] not in ollama_support_embedding_model_list:
                        precision_list.append(model.model)
                if precision_selected in precision_list: # 解决ollama URL切换时selected与模型列表不一致问题
                    db.query(models.Model).filter(models.Model.id == model_id).update({"precision_list": json.dumps(precision_list)})
                else:
                    precision_selected = precision_list[0]
                    db.query(models.Model).filter(models.Model.id == model_id).update({"precision_list": json.dumps(precision_list),"precision_selected":json.dumps(precision_selected)})
            print(precision_list)
                        
            if type == 1:
                model_info.status = ModelStatus.LOADING.status
                model_info.precision_selected = precision_selected
            else:
                model_info.status = ModelStatus.NOT_LOAD.status
                # update_result = db.query(models.Model).filter(models.Model.id == model_id).update(
                #     {"status": ModelStatus.NOT_LOAD.status})
            log.info("load_model model_id:" + str(model_id) + ", type:" + str(type))
            db.commit()
            if type != 1:
                return True
            t = threading.Thread(target=load_model_by_model_info, args=(model_info.id, model_info.plugin, url,api_key, precision_selected))
            t.start()
            return True
    except Exception as ex:
        log.error(f"load model error, {str(ex)}")
        return False

def update_url_and_api_key(model_id:int,url:str,api_key:str):
    try:
        from pkg.database import models
        from pkg.database.database import SessionLocal
        with SessionLocal() as db:
            model_info = db.query(models.Model).filter(models.Model.id == model_id).first()
            if url == '':
                db.query(models.Model).filter(models.Model.id == model_id).update({"api_key": api_key})
            if api_key != '' and url != '':
                db.query(models.Model).filter(models.Model.id == model_id).update({"api_key": api_key, "url": url})
            if api_key == '':
                db.query(models.Model).filter(models.Model.id == model_id).update({"url": url})
            db.commit()
            model_info = db.query(models.Model).filter(models.Model.id == model_id).first()
            # print(model_info)
            return model_info
    except Exception as ex:
        log.error(f"load model error, {str(ex)}")
        return False 


def load_model_by_model_info(model_id: int, plugin_path: str, url: str,api_key:str, precise_select: str):
    from pkg.database import models
    from pkg.database.database import SessionLocal
    try:
        if gvar.get_model():
            gvar.set_model(None)
            gvar.set_tokenizer(None)
        load_model_result = importlib.import_module(plugin_path)
        load_flag = load_model_result.load_model('', url, api_key,precise_select)
        # print("load_flag:",load_flag)
        # if not load_flag:
        #     return False
        log.info("加载成功")
        with SessionLocal() as db:
            db.query(models.Model).filter(models.Model.id == model_id).update(
                {"status": ModelStatus.LOAD_SUCCESS.status})
            # print("加载成功",ModelStatus.LOAD_SUCCESS.status)
            db.commit()
        return True
    except Exception as ex:
        log.error(f"load_model_by_model_info error, model_id:{model_id}, err: {str(ex)}")
        with SessionLocal() as db:
            db.query(models.Model).filter(models.Model.id == model_id).update(
                {"status": ModelStatus.LOAD_FAILED.status})
            db.commit()



def list(ids: List[int] = None, statuses: List[int] = None,  names: List[str] = None, page_no: int = None, page_size: int = None):
    results = []
    try:
        from pkg.database import models
        from pkg.database.database import SessionLocal
        with SessionLocal() as db:
            query = db.query(models.Model)
            if ids:
                query = query.filter(models.Model.id.in_(ids))

            if statuses:
                query = query.filter(models.Model.status.in_(statuses))

            if names:
                names_filters = [models.Model.name.ilike('%{}%'.format(name)) for name in names]
                query = query.filter(or_(*names_filters))

            if page_no is not None and page_size is not None:
                query = query.offset((page_no - 1) * page_size).limit(page_size).all()

            models = query.all()

            for model in models:
                model_dict = model.__dict__.copy()
                model_dict.pop('_sa_instance_state', None)
                str_labels = model_dict["labels"].strip('[]')
                items = str_labels.split(',')
                model_dict["labels"] = [item.strip() for item in items]
                results.append(model_dict)
    except Exception as ex:
        log.error("list models error, " + str(ex))
    return results


def init_models_status():
    try:
        from pkg.database import models
        from pkg.database.database import SessionLocal
        with SessionLocal() as db:
            db.query(models.Model).filter(models.Model.status == ModelStatus.LOAD_SUCCESS.status).update({"status": ModelStatus.NOT_LOAD.status})
            db.commit()
        return True
    except Exception as ex:
        log.error(f"init_models_status error, {str(ex)}")

