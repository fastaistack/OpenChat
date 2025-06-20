from .biz_enum import ModelStatus, ModelType
from ...logger import Log
from typing import List
from sqlalchemy import or_,and_
import importlib
from pkg.projectvar.projectvar import Projectvar
import threading
from pkg.projectvar import Projectvar
from ollama import Client
import json
from ...database.models import ModelList
from ...database import models,schemas
from ...database.database import SessionLocal
from ...projectvar.statuscode import StatusCodeEnum as status

gvar = Projectvar()
log = Log()
gavr = Projectvar()


ollama_support_embedding_model_list = ['nomic-embed-text',
                                    'mxbai-embed-large',
                                    'snowflake-arctic-embed',
                                    'snowflake-arctic-embed2',
                                    'granite-embedding',
                                    'all-minilm',
                                    'bge-large',
                                    'jeffh/intfloat-multilingual-e5-large-instruct',
                                    'shaw/dmeta-embedding-zh',]


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

def insert_model_list(model_key: str, name: str, model_type: str):
    from pkg.database import models
    from pkg.database.database import SessionLocal
    with SessionLocal() as db:
        new_model = models.ModelList(
            model_key=model_key,
            name=name,
            model_type=model_type
        )
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        return new_model  # 可返回刚插入的数据

def delete_model_by_id(model_id: int):
    from pkg.database import models
    from pkg.database.database import SessionLocal
    with SessionLocal() as db:
        model = db.query(models.ModelList).filter(models.ModelList.id == model_id).first()
        if model:
            db.delete(model)
            db.commit()
            return True
        else:
            return False

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

def get_download_multiple_embedding_model_list():
    from pkg.database import models
    from pkg.database.database import SessionLocal
    result = []
    id = 1

    with SessionLocal() as db:
        # ✅ 1. 获取 Ollama 模型（单独 try）
        try:
            model_info = db.query(models.Model).filter(models.Model.key == 'ollama').first()
            if model_info:
                from ollama import Client
                ollama = Client(host=model_info.url)
                model_list = ollama.list()
                for model in model_list.models:
                    if model.model.split(':')[0] in ollama_support_embedding_model_list:
                        result.append({
                            "id": id,
                            "name": model.model,
                            "local_path": model.model,
                            "key": 'ollama',
                            "cn_name": 'ollama'
                        })
                        id += 1
        except Exception as ex:
            import traceback
            print("❌ Ollama 加载失败：", traceback.format_exc())
            log.warning(f"Ollama 未连接或加载失败: {str(ex)}")

        # ✅ 2. 继续加载数据库中其他 embedding 模型
        try:
            query = db.query(
                models.ModelList,
                models.Model.name.label("model_name")
            ).join(
                models.Model, models.ModelList.model_key == models.Model.key
            ).filter(
                models.ModelList.model_type == 'embedding',
                models.Model.api_key != '',
                models.ModelList.model_key != 'ollama',
            )

            for row, model_name in query.all():
                result.append({
                    "id": id,
                    "name": row.name,
                    "local_path": row.name,
                    "key": row.model_key,
                    "cn_name": model_name
                })
                id += 1
        except Exception as ex:
            import traceback
            print("❌ 数据库模型加载失败：", traceback.format_exc())
            log.error(f"get_embedding_model_list database error: {str(ex)}")

    return result

        
def get_show_model_list():
    try:
        from pkg.database import models
        from pkg.database.database import SessionLocal
        result = []
        id = 1
        with SessionLocal() as db:
            query = db.query(models.ModelList)
            for row in query.all():
                result.append({
                    "id": id,
                    "name": row.name,
                    "type": row.model_type,
                    "provider":row.model_key
                })
                id += 1
            
            return result
    except Exception as ex:
        log.error(f"get_model_list error,{str(ex)}")
        return []

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
            models_list = []
            platform = db.query(models.Model).filter(models.Model.status == ModelStatus.LOAD_SUCCESS.status).all()
            if platform:
                if platform[0].key == 'ollama': # 按照ollama client来处理，不走数据库
                    ollama = Client(host=platform[0].url)
                    ollama_model_list = ollama.list()
                    for model in ollama_model_list.models:
                        if model.model.split(':')[0] not in ollama_support_embedding_model_list:
                            models_list.append(model.model)
                else:
                    model_item = db.query(models.ModelList).filter(models.ModelList.model_key == platform[0].key).all()
                    for model in model_item:
                        if model.model_type!="embedding":
                            models_list.append(model.name)
            return platform, models_list
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
            if model_info.key == 'ollama':
                ollama = Client(host=url)
                try:
                    model_list = ollama.list()
                except:
                    log.error("没启动ollama/没安装ollama")
                    return False, status.OLLAMA_LOAD_ERROR
                for model in model_list.models:
                    if model.model.split(':')[0] not in ollama_support_embedding_model_list:
                        precision_list.append(model.model)
                if precision_selected in precision_list: # 解决ollama URL切换时selected与模型列表不一致问题
                    # db.query(models.Model).filter(models.Model.id == model_id).update({"precision_list": json.dumps(precision_list)})
                    pass
                    
                else: # 切换url
                    precision_selected = precision_list[0]
                    # db.query(models.Model).filter(models.Model.id == model_id).update({"precision_list": json.dumps(precision_list),"precision_selected":json.dumps(precision_selected)})
            log.info(f"load_model :{precision_list}")
                        
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
                return True,''
            t = threading.Thread(target=load_model_by_model_info, args=(model_info.id, model_info.plugin, url,api_key, precision_selected))
            t.start()
            return True,''
    except Exception as ex:
        import traceback
        print(traceback.format_exc())
        log.error(f"load model error, {str(ex)}")
        return False,status.OPENCHAT_MODEL_LOAD_FAILED_ERROR

def update_url_and_api_key(model_id:int,url:str,api_key:str):
    try:
        from pkg.database import models
        from pkg.database.database import SessionLocal
        with SessionLocal() as db:
            model_info = db.query(models.Model).filter(models.Model.id == model_id).first()
            if model_id == 2 and api_key == '': # 保证保存的ollama的apikey为空时，有固定的apikey赋值
                api_key ='ollama'
            db.query(models.Model).filter(models.Model.id == model_id).update({"api_key": api_key, "url": url})
            # if url == '':
            #     db.query(models.Model).filter(models.Model.id == model_id).update({"api_key": api_key})
            # if api_key != '' and url != '':
            #     db.query(models.Model).filter(models.Model.id == model_id).update({"api_key": api_key, "url": url})
            # if api_key == '':
            #     db.query(models.Model).filter(models.Model.id == model_id).update({"url": url})
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

#创建model
def create_model(model:schemas.ModelBase):
    with SessionLocal() as db:
        try:
            db_query = db.query(models.ModelList).filter(and_(models.ModelList.model_key == model.model_key, models.ModelList.name == model.name)).first()
            if db_query:
                log.info(f"create_model model_name: {model.name} is already exist.")
                return None
            db_model = models.ModelList(**model.dict())
            db.add(db_model)
            db.commit()
            db.refresh(db_model)
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            log.error(f"create_model Exception:{str(e)}")
    return db_model

def create_ollama_model():
    ollama_model_list = []
    with SessionLocal() as db:
        try:
            db_query = db.query(models.Model).filter(models.Model.key == 'ollama').first()
            url = db_query.url
            ollama = Client(host = url)
            model_list = ollama.list()
            for model in model_list.models:
                model_name = model.model.split(':')[0]
                if model_name not in ollama_support_embedding_model_list: # chat模型
                    if "embed" in model_name: # embed模型
                        model_type = "embedding"
                    else:
                        model_type = "chat"
                else: # embedding模型
                    model_type = "embedding"
                ollama_model_list.append(
                    {
                        "model_key":"ollama",
                        "name":model.model,
                        "model_type":model_type,
                    }
                )
        except Exception as e:
            log.error(f"create_ollama_model:{str(e)}")
        return ollama_model_list

# 根据key值获取model_list
def get_model_list_by_key(key:str):
    model_list = []
    with SessionLocal() as db:
        try:
            db_query = db.query(models.ModelList).filter(models.ModelList.model_key == key).all()
            
            for model in db_query:
                model_list.append(model.name)
        except Exception as e:
            log.error(f"get_model_list_by_key:{str(e)}")
        finally:
            return model_list
        
def models_init():
    models_list =[
        {"model_key":"deepseek_local","name":"deepseek-r1","model_type":"chat",},
        {"model_key":"deepseek_local","name":"deepseek-v3","model_type":"chat",},
        {"model_key":"tencent","name":"deepseek-r1","model_type":"chat",},
        {"model_key":"tencent","name":"deepseek-v3","model_type":"chat",},
        {"model_key":"baidu","name":"deepseek-r1","model_type":"chat",},
        {"model_key":"baidu","name":"deepseek-v3","model_type":"chat",},
        {"model_key":"baidu","name":"qwen3-32b","model_type":"chat",},
        {"model_key":"deepseek_office","name":"deepseek-chat","model_type":"chat",},
        {"model_key":"deepseek_office","name":"deepseek-reasoner","model_type":"chat",},
        {"model_key":"openai","name":"gpt-3.5-turbo","model_type":"chat",},
        {"model_key":"openai","name":"gpt-4","model_type":"chat",},
        {"model_key":"kimi","name":"moonshot-v1-8k","model_type":"chat",},
        {"model_key":"kimi","name":"moonshot-v1-32k","model_type":"chat",},
        {"model_key":"zhipu","name":"glm-4-plus","model_type":"chat",},
        {"model_key":"zhipu","name":"glm-4-air","model_type":"chat",},
        {"model_key":"hunyuan","name":"hunyuan-lite","model_type":"chat",},
        {"model_key":"hunyuan","name":"hunyuan-pro","model_type":"chat",},
        {"model_key":"hunyuan","name":"hunyuan-embedding","model_type":"embedding",},
        {"model_key":"infini","name":"qwen3-32b","model_type":"chat",},
        {"model_key":"infini","name":"deepseek-r1","model_type":"chat",},
        {"model_key":"infini","name":"qwen2.5-32b-instruct","model_type":"chat",},
        {"model_key":"infini","name":"bge-m3","model_type":"embedding",},
        {"model_key":"siliconflow","name":"deepseek-ai/DeepSeek-R1-Distill-Qwen-7B","model_type":"chat",},
        {"model_key":"siliconflow","name":"Qwen/Qwen3-8B","model_type":"chat",},
        {"model_key":"siliconflow","name":"Qwen/Qwen3-32B","model_type":"chat",},
        {"model_key":"siliconflow","name":"Qwen/Qwen2.5-7B-Instruct","model_type":"chat",},
        {"model_key":"siliconflow","name":"BAAI/bge-large-zh-v1.5","model_type":"embedding",},
        {"model_key":"siliconflow","name":"netease-youdao/bce-embedding-base_v1","model_type":"embedding",},
        {"model_key":"siliconflow","name":"BAAI/bge-m3","model_type":"embedding",},
        {"model_key":"aliyun","name":"qwen3-8b","model_type":"chat",},
        {"model_key":"aliyun","name":"qwen3-32b","model_type":"chat",},
        {"model_key":"aliyun","name":"qwen-plus","model_type":"chat",},
        {"model_key":"aliyun","name":"qwen-max","model_type":"chat",},
        {"model_key":"aliyun","name":"text-embedding-v3","model_type":"embedding",},
        {"model_key":"Jina","name":"jina-clip-v2","model_type":"embedding",},
        {"model_key":"Jina","name":"jina-embeddings-v2-base-zh","model_type":"embedding",},
        {"model_key":"Jina","name":"jina-embeddings-v3","model_type":"embedding",},
        {"model_key":"stepfun","name":"step-1-flash","model_type":"chat",},
        {"model_key":"stepfun","name":"step-1-32k","model_type":"chat",},
        {"model_key":"baichuan","name":"Baichuan2-Turbo","model_type":"chat",},
        {"model_key":"baichuan","name":"Baichuan4-Air","model_type":"chat",},
        {"model_key":"baichuan","name":"Baichuan-Text-Embedding","model_type":"embedding",},
    ]
    # ollama 模型列表更新
    ollama_model_list = create_ollama_model()
    models_list.extend(ollama_model_list)
    # 根据模型默认列表初始化
    for model in models_list:
        model_base = schemas.ModelBase(**model)
        db_create_model = create_model(model=model_base)
        if db_create_model:
            log.info(f"model {db_create_model.name} create SUCCESSFUL")
        