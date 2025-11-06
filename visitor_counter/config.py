"""
访客计数服务配置文件
"""

import os
from pathlib import Path

# 基础配置
APP_NAME = "访客计数服务"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "基于FastAPI的独立访客计数服务"

# 服务配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8081"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# 数据文件配置
DATA_DIR = Path(__file__).parent
VISITOR_FILE = DATA_DIR / "visitor_count.json"

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# CORS配置
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
    "*"  # 开发环境允许所有来源
]

# API配置
API_PREFIX = "/api"
DOCS_URL = "/docs"
REDOC_URL = "/redoc"
