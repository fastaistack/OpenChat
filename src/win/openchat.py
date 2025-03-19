from pkg.projectvar import *

import os
import json
gvar = Projectvar()


def init_acount():
    from pkg.server.router.account_api import alchemytool

    alchemytool.init_database()

    # 初始化权限
    # 判断文件是否存在
    config_path = "assets/config/config.json"
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            alchemytool.init_permissions(data)

def init_plugins():
    from pkg.database import models
    from pkg.database.database import SessionLocal
    db = SessionLocal()
    from pkg.server.process.plugin_process import plugins_init
    plugins_init()
    plugins = db.query(models.Plugin).all()
    gvar.set_plugins(plugins=plugins)

def init_vector_config():
    from pkg.database import models
    from pkg.database.database import SessionLocal
    from sqlalchemy import and_
    from pkg.server.process import process_setting
    from pkg.server.router.knowledge import VECTOR_VERSION
    db = SessionLocal()
    if VECTOR_VERSION == "chromadb":
        knowledgequeried = db.query(models.Setting).filter(and_(models.Setting.config_key == VECTOR_VERSION)).all()
        # 查询不到，新增chromadb
        if len(knowledgequeried) == 0:
            global_path = process_setting.get_system_default_path().config_value
            file_local_path = os.path.join(global_path, VECTOR_VERSION)
            chromadb = {"global_param":{"chromadb_persist_path":file_local_path,"embed_model":"thomas/text2vec-base-chinese"},"storage_param":{"chunk_size":300,"overlap_size":20,"distance_strategy":"cosine"},"query_param":{"search_type":"similarity","k":3,"score_threshold":0.5,"fetch_k":20,"lambda_mult":0.5,"prompt_template":"请根据检索到的背景信息，回答以下问题："}}
            knowledge_config = models.Setting(user_id="admin", config_key=VECTOR_VERSION, config_value=json.dumps(chromadb))
            db.add(knowledge_config)
            db.commit()
            db.refresh(knowledge_config)
    else:
        knowledge_milvus = db.query(models.Setting).filter(and_(models.Setting.config_key == VECTOR_VERSION)).all()
        if len(knowledge_milvus) == 0:
            milvus = {"global_param":{"milvus_db_host":"127.0.0.1","milvus_db_port":"19530","milvus_db_user":"","milvus_db_password":"","embed_model":"thomas/text2vec-base-chinese"},"storage_param":{"chunk_size":1000,"overlap_size":120,"index_params":{},"distance_strategy":"l2","metric_type":"COSINE","index_type":"FLAT"},
                      "query_param":{"search_type":"similarity","k":4,"score_threshold":0.5,"fetch_k":20,"lambda_mult":0.5,"prompt_template":"请根据检索到的背景信息，回答以下问题："}}
            mknowledge_config = models.Setting(user_id="admin", config_key="milvus", config_value=json.dumps(milvus))
            db.add(mknowledge_config)
            db.commit()
            db.refresh(mknowledge_config)

    knowledgefilechat_config = db.query(models.Setting).filter(and_(models.Setting.config_key == "document_chat")).all()
    # 查询不到，新增配置
    if len(knowledgefilechat_config) == 0:
        embedding_config = {"embed_model":"thomas/text2vec-base-chinesee","embed_param":{"dimension":512}}
        knowledge_config = models.Setting(user_id="admin", config_key="document_chat", config_value=json.dumps(embedding_config))
        db.add(knowledge_config)
        db.commit()
        db.refresh(knowledge_config)
    # process_setting.get_system_default_path().config_value
    # from pkg.server.router import knowledge
    # knowledge.mv_knowledge_file(process_setting.get_system_default_path().config_value,os.path.join(process_setting.get_system_default_path().config_value,'tmp_test'))
    # knowledge.get_move_knowledge_process()
    # knowledge.get_move_knowledge_volume()

def init():
    gvar.set_home_path(os.getcwd())
    # check cache dir, if not exist, create it
    user_basepath = os.path.expanduser("~")
    cache_path = os.path.join(user_basepath, YUAN_CACHEPATH)
    # print("cache_path", cache_path)
    os.makedirs(cache_path, exist_ok=True)
    gvar.set_cache_path(cache_path)
    
    # check db file, if not exist, create it 
    db_filename = os.path.join(cache_path, DB_FILENAME)
    gvar.set_db_filename(db_filename)
    if not os.path.exists(db_filename):
        from pkg.database import crud
        crud.init_database()
        from pkg.database.data_init import init_models
        init_models()

    from pkg.server.process import process_model
    
    process_model.init_models_status()
    # 初始化登录账户
    init_acount()
    # 初始化插件
    # init_plugins()
    # 初始化向量库配置
    init_vector_config()
    # from pkg.server.router.knowledge import get_knowledge_by_id
    # params = get_knowledge_by_id("590c97cff54f11eeb85cbce92ffb436e")
    # print(params)
    # 更新文件状态
    from pkg.server.router import knowledge
    knowledge.change_file_status()
    
def main():
    #0. Init environment
    init()
    from pkg.server import run as server_run
    from pkg.app import run as app_run
    #1. Create server
    server_run()
    #2. Create main app
    app_run()

if __name__ == "__main__":
    main()