# 系统版本常量
WINDOWS = 'Windows'
MACOS = 'macOS'

# 获取系统版本
import sys
if sys.platform.startswith('win'):
    SYSTEM = WINDOWS
    OPENCHAT_CACHEPATH = ".openchat"
elif sys.platform.startswith('darwin'):
    SYSTEM = MACOS
    OPENCHAT_CACHEPATH = "openchat"

# Environment variables
OPENCHAT_WEBUI_PATH = "assets/dist"


# Log variables
OPENCHAT_LOG_NAME = "openchat.log"
OPENCHAT_LOG_ROTATION = "1 day"
OPENCHAT_LOG_RETENTION = "1 day"

OPENCHAT_SERVER_PORT = 5050
API_SERVER_PORT = 5051

# Database variables
DB_SQLITE_PREFIX = "sqlite:///"
DB_FILENAME = "openchat.db"
DB_DB = "openchat"
DB_FILENAME = "openchat.db"
DB_DB = "openchat"

# Http Header Key
HTTP_HEADER_USER_ID = "user-id"
HTTP_HEADER_USER_NAME = "user-name"
HTTP_HEADER_ROLE_ID = "role-id"
HTTP_HEADER_ROLE_NAME = "role-name"
HTTP_HEADER_AUTHORIZATION = "authorization"
# 客户端接受的语言类型 非header中原生的 accept-language
HTTP_HEADER_ACCEPT_LANGUAGE = "accept-language"

import json
def read_config(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)  # 解析 JSON 文件为 Python 字典
    except FileNotFoundError:
        print(f"错误：配置文件 {file_path} 不存在")
        return None
    except json.JSONDecodeError as e:
        print(f"错误：JSON 格式错误 - {e}")
        return None
    except Exception as e:
        print(f"错误：读取文件失败 - {e}")
        return None

# OpenChat version
if SYSTEM == WINDOWS:
    OPENCHAT_VERSION = read_config('./config.json')['version']
else:
    OPENCHAT_VERSION = 'v1.0.3'

# Openchat Update
UPDATE_SERVER_URL = 'https://xx.xx.xx.xx'
if SYSTEM == WINDOWS:
    DOWNLOAD_DIR = './download'
else:
    import os
    global_path=os.path.join(os.path.expanduser('~'),'openchat')
    DOWNLOAD_DIR = os.path.join(global_path,'download')

