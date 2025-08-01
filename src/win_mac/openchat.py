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


import sys, os, nltk, shutil, pytesseract

def get_runtime_path(subpath=""):
    """
    获取资源在打包后运行时的路径，兼容 PyInstaller .app 中 Contents/Resources/，否则 fallback 到 MacOS 目录
    """
    if getattr(sys, 'frozen', False):
        base_mac = os.path.abspath(os.path.dirname(sys.executable))
        resources_path = os.path.abspath(os.path.join(base_mac, "../Resources"))
        candidate = os.path.join(resources_path, subpath)
        if os.path.exists(candidate):
            return candidate
        return os.path.join(base_mac, subpath)
    else:
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), subpath)

def setup_runtime():
    """
    设置运行时依赖路径，兼容 PyInstaller .app 环境。
    """
    if getattr(sys, 'frozen', False):
        print("📦 正在初始化运行时依赖路径...")

        # ✅ 1. 设置 PATH 补充
        homebrew_bin = "/opt/homebrew/bin"
        if homebrew_bin not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{homebrew_bin}:{os.environ.get('PATH', '')}"

        # ✅ 2. 设置 libmagic
        packed_magic = get_runtime_path("libmagic/magic.mgc")
        libmagic_dylib = get_runtime_path("libmagic/libmagic.dylib")

        if os.path.exists(packed_magic):
            os.environ["MAGIC"] = packed_magic
            print(f"✅ 使用打包内置 libmagic 数据库: {packed_magic}")
        else:
            print(f"❌ 未找到 libmagic 数据文件: {packed_magic}，请检查是否正确打包或放置")

        if os.path.exists(libmagic_dylib):
            dyld_dir = os.path.dirname(libmagic_dylib)
            old_dyld = os.environ.get("DYLD_LIBRARY_PATH", "")
            os.environ["DYLD_LIBRARY_PATH"] = f"{dyld_dir}:{old_dyld}"
            print(f"✅ 设置 DYLD_LIBRARY_PATH 为: {os.environ['DYLD_LIBRARY_PATH']}")
        else:
            print(f"❌ 未找到 libmagic 动态库: {libmagic_dylib}，请检查是否正确打包或放置")

        # ✅ 2.5 设置 libexpat 检查路径
        libexpat_path = os.path.abspath(
            os.path.join(sys.executable, "../../Frameworks/libexpat.1.dylib")
        )
        print(f"🧭 检查路径: Frameworks/libexpat.1.dylib → {libexpat_path} (存在: {os.path.exists(libexpat_path)})")

        # ✅ 2.6 检查 pyexpat 链接和路径
        try:
            import pyexpat
            print(f"📦 当前 pyexpat.so 路径: {pyexpat.__file__}")
            import subprocess
            
            result = subprocess.run(
                ["otool", "-L", pyexpat.__file__],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode == 0:
                output = result.stdout
                print("🔍 otool 输出：")
                print(output)

                if "@executable_path/../Frameworks/libexpat.1.dylib" in output:
                    print("✅ pyexpat.so 正确链接至打包内 libexpat")
                else:
                    print("❌ pyexpat.so 未正确链接，仍使用系统 libexpat")
            else:
                print(f"❌ otool 执行失败: {result.stderr}")

        except Exception as e:
            print(f"❌ pyexpat 加载失败或验证失败: {e}")

        # ✅ 3. 检查 tesseract
        if shutil.which("tesseract") is None:
            print("❌ 未检测到 Tesseract OCR，请先运行：brew install tesseract")
            return
        else:
            print("✅ 已安装 tesseract")

        # ✅ 5. 设置 nltk 路径
        nltk_path = get_runtime_path("nltk_data")
        if os.path.exists(nltk_path):
            nltk.data.path.append(nltk_path)
            print(f"✅ 加载 nltk_data: {nltk_path}")
        else:
            print(f"⚠️ 未找到 nltk_data 目录: {nltk_path}")

        # ✅ 6. 设置 huggingface hub 缓存路径（用于加载 onnx 模型）
        hf_model_path = get_runtime_path("resources/models")
        if os.path.exists(hf_model_path):
            os.environ["HUGGINGFACE_HUB_CACHE"] = hf_model_path
            print(f"✅ 设置 HUGGINGFACE_HUB_CACHE = {hf_model_path}")
        else:
            print("⚠️ 未找到打包的 huggingface 模型目录")

        # ✅ 7. 检查 pandoc（从 libmagic 文件夹中查找）
        try:
            local_pandoc = get_runtime_path("libmagic/pandoc")
            if os.path.exists(local_pandoc):
                if os.access(local_pandoc, os.X_OK):
                    os.environ["PYPANDOC_PANDOC"] = local_pandoc
                    os.environ["PATH"] = f"{os.path.dirname(local_pandoc)}:{os.environ.get('PATH', '')}"
                    print(f"✅ 设置 PYPANDOC_PANDOC = {local_pandoc}")
                else:
                    print(f"⚠️ pandoc 存在但不可执行：{local_pandoc}")
            else:
                print(f"❌ 未找到 pandoc：{local_pandoc}")
        except ImportError:
            print("❌ 未安装 pypandoc，请运行：pip install pypandoc")


def init():
    gvar.set_home_path(os.getcwd())
    # check cache dir, if not exist, create it
    user_basepath = os.path.expanduser("~")
    cache_path = os.path.join(user_basepath, OPENCHAT_CACHEPATH)
    # print("cache_path", cache_path)
    os.makedirs(cache_path, exist_ok=True)
    gvar.set_cache_path(cache_path)
    
    # check db file, if not exist, create it 
    db_filename = os.path.join(cache_path, DB_FILENAME)
    gvar.set_db_filename(db_filename)
    if not os.path.exists(db_filename):
        from pkg.database import crud
        crud.init_database()
        # 执行数据迁移
        from pkg.server.router import update_api
        update_api.data_migration_immediately()
        
    from pkg.database.data_init import init_models
    init_models()
        
    if constants.SYSTEM == constants.MACOS:
        setup_runtime()
    
    
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
    from pkg.plugins.translator.utils import checkout_translate_item
    checkout_translate_item()
    
    if constants.SYSTEM == constants.WINDOWS:
        # v1.0.3版本向上升级时仅配置一次
        from pkg.server.process import process_setting
        process_setting.init_file_move()
    
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
    if constants.SYSTEM == constants.MACOS:
        import multiprocessing
        multiprocessing.freeze_support() # 解决mac端无线重启
    main()