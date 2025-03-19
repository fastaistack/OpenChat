# Environment variables
YUAN_CACHEPATH = "openchat"
YUAN_WEBUI_PATH = "assets/dist"
#  444 与前端部署互斥
# YUAN_WEBUI_DOC_PATH = "assets/yuan-doc"
#  444 与前端部署互斥
# 以下代码为空
#  444 end

# Log variables
YUAN_LOG_NAME = "openchat.log"
YUAN_LOG_ROTATION = "1 day"
YUAN_LOG_RETENTION = "1 day"

YUAN_SERVER_PORT = 5050
API_SERVER_PORT = 5051

# Database variables
DB_SQLITE_PREFIX = "sqlite:///"
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

# OpenChat version
OPENCHAT_VERSION = "v1.0"

