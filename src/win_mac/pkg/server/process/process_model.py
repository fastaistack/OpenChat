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
from pkg.is_embedding_model_utils import is_embedding_model
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
                    if is_embedding_model(model.model):
                        log.info(f"✅ 模型 {model.model} 是嵌入模型")
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
                        if not is_embedding_model(model.model):
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
                    log.error("没启动ollama/没安装ollama/没配置ollama")
                    return False, status.OLLAMA_LOAD_ERROR
                for model in model_list.models:
                    if not is_embedding_model(model.model):
                        precision_list.append(model.model)
                if not precision_list : # chat为空
                    return False,status.OLLAMA_CHAT_MODLE_ERROR
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
                model_name = model.model
                if is_embedding_model(model_name):
                    model_type = "embedding"
                else:
                    model_type = "chat"

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
        {"model_key":"openrouter","name":"deepseek/deepseek-chat","model_type":"chat",},
        {"model_key":"openrouter","name":"mistralai/mistral-7b-instruct:free","model_type":"chat",},
        {"model_key":"openrouter","name":"qwen/qwen3-235b-a22b:free","model_type":"chat",},
        {"model_key":"volcengine","name":"deepseek-r1-250120","model_type":"chat",},
        {"model_key":"volcengine","name":"deepseek-v3-250324","model_type":"chat",},
        {"model_key":"volcengine","name":"doubao-1-5-pro-32k-250115","model_type":"chat",},
        {"model_key":"volcengine","name":"doubao-1-5-pro-256k-250115","model_type":"chat",},
        {"model_key":"volcengine","name":"doubao-embedding-large-text-250515","model_type":"embedding",},
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
        {"model_key":"kimi","name":"kimi-latest","model_type":"chat",},
        {"model_key":"kimi","name":"kimi-k2-0711-preview","model_type":"chat",},
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
        {"model_key":"stepfun","name":"step-2-mini","model_type":"chat",},
        {"model_key":"stepfun","name":"step-1-32k","model_type":"chat",},
        {"model_key":"stepfun","name":"step-2-16k","model_type":"chat",},
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

from pkg.database.schemas import PluginBaseMo
from pkg.server.process.plugin_process import create_plugin

def insert_plugin_by_copy(base_key: str, new_key: str):
    from pkg.database import models
    from pkg.database.database import SessionLocal

    with SessionLocal() as db:
        base_plugin = db.query(models.PluginMo).filter(models.PluginMo.plugin_key == base_key).first()
        if not base_plugin:
            raise Exception(f"插件 {base_key} 不存在，无法复制")
        
        # 构造新插件对象
        plugin_obj = PluginBaseMo(
            plugin_logo=base_plugin.plugin_logo,
            plugin_key=new_key,
            plugin_name=base_plugin.plugin_name,
            plugin_name_en=new_key,
            plugin_name_cn=new_key,
            plugin_path=base_plugin.plugin_path,
            plugin_order=base_plugin.plugin_order,
            plugin_type=base_plugin.plugin_type,
            plugin_status=False,
            plugin_param="[]",  # 插入时会自动生成
            description=f"{new_key} 模型",
            description_en=f"{new_key} model",
            description_cn=f"{new_key}模型"
        )

        return create_plugin(plugin_obj, user_id=base_plugin.user_id)


def add_deployment_from_base(new_deployment: dict):
    """
    以 deepseek_local 模型为基础，添加新的部署模型，并返回完整的新模型（含数据库自动生成的 id）
    """
    base_key = "deepseek_local"

    with SessionLocal() as db:
        base_model = db.query(models.Model).filter(models.Model.key == base_key).first()
        if not base_model:
            raise Exception("未找到基础模型：deepseek_local")

        # ✅ 自动生成编号名（仅当传入为“自定义部署”时）
        raw_name = new_deployment.get("name", "")
        if raw_name.strip() == "自定义部署":
            prefix = "自定义部署_"
            existing_names = db.query(models.Model.name).filter(models.Model.name.like(f"{prefix}%")).all()
            used_numbers = set()
            for name_tuple in existing_names:
                name = name_tuple[0]
                if name.startswith(prefix):
                    try:
                        number = int(name[len(prefix):])
                        used_numbers.add(number)
                    except ValueError:
                        continue
            # 寻找最小未使用编号
            i = 1
            while i in used_numbers:
                i += 1
            auto_name = f"{prefix}{str(i).zfill(2)}"
        else:
            auto_name = raw_name or "未命名部署"

        # 先用临时 key，占位；稍后根据 id 生成正式 key
        temp_key = "temp_key_placeholder"

        new_model = models.Model(
            name=auto_name,
            key=temp_key,
            user=base_model.user,
            author=base_model.author,
            local_path=base_model.local_path,
            modelscope_path=base_model.modelscope_path,
            web_path=base_model.web_path,
            files_size=base_model.files_size,
            task_type=base_model.task_type,
            opensource_license=base_model.opensource_license,
            framework=base_model.framework,
            labels=base_model.labels,
            hardware_requirement=base_model.hardware_requirement,
            description=base_model.description,
            release_time=base_model.release_time,
            base_info=base_model.base_info,
            status=base_model.status,
            type=base_model.type,
            plugin=base_model.plugin,
            pic=base_model.pic,
            precision_list=base_model.precision_list,
            precision_selected=base_model.precision_selected,
            api_key='',
            url='https://xxx.xxx.xxx.xx:xxxxx'
        )

        db.add(new_model)
        db.flush()  # 刷新后可获取 ID，但事务未提交
        db.refresh(new_model)

        # ✅ 使用数据库自动生成的 ID 构造唯一 key
        new_model.key = f"deepseek_local_{new_model.id}"
        db.commit()

        # ✅ 插入 ModelList 表中的两个默认模型
        for name in ["deepseek-r1", "deepseek-v3"]:
            model_dict = {
                "model_key": new_model.key,
                "name": name,
                "model_type": "chat"
            }
            model_base = schemas.ModelBase(**model_dict)
            create_model(model=model_base)

        # ✅ 插入 Plugin 表
        insert_plugin_by_copy(base_key="deepseek_local", new_key=new_model.key)

        return new_model

def delete_deployment_by_key(key: str):
    """
    删除指定 key 的部署模型，包括：
    - Model 主表
    - ModelList 子模型
    - Plugin 插件信息
    """
    from pkg.database.database import SessionLocal
    from pkg.database import models

    db = SessionLocal()

    try:
        # 1. 删除 Model 主表记录
        model = db.query(models.Model).filter(models.Model.key == key).first()
        if model:
            db.delete(model)

        # 2. 删除 ModelList 中所有 model_key 关联的模型
        model_list = db.query(models.ModelList).filter(models.ModelList.model_key == key).all()
        for m in model_list:
            db.delete(m)

        # 3. 删除 PluginMo 中 plugin_key = key 的插件
        plugin = db.query(models.PluginMo).filter(models.PluginMo.plugin_key == key).first()
        if plugin:
            db.delete(plugin)

        db.commit()

    except Exception as e:
        db.rollback()
        raise e

    finally:
        db.close()
