from enum import Enum


class StatusCodeEnum(Enum):
    """状态码枚举类"""
    OK = (0, '成功')

    ERROR = (-1, '错误')
    UNKNOWN = (-2, '未知错误')
    
    #数据库错误码定义， 范围（1-1000）
    DB_NOTFOUND_ERR = (1, '记录不存在')
    DB_EXIST_ERR = (2, '记录已存在')

    YUAN_MODEL_PARAM_INVALID_ERROR = (3, "参数不合法，请检查")
    YUAN_MODEL_NOT_EXIST_ERROR = (4, "模型不存在，请检查")
    YUAN_MODEL_LOAD_FAILED_ERROR = (5, "模型加载失败，请检查")
    YUAN_BIZ_DATA_UPDATE_FAILED_ERROR = (6, "数据更新失败，请检查")
    KNOWLEDGE_EXIST_ERROR = (7, "知识库已存在，请检查")

    AUTHORIZATION_FIALEDS = (8, "鉴权失败")

    YUAN_BIZ_DATA_CREATE_FAILED_ERROR = (9, "创建失败，请检查")
    AUTHORIZATION_ERROR = (10, "用户名或密码错误")
    YUAN_MODEL_DOWNLOAD_FAILED_ERROR = (11, "模型下载失败，请检查")
    SYSTEM_FILE_PATH_NOT_EXIST = (12, "文件路径不存在，请检查")
    SYSTEM_PORT_ALREADY_IN_USE = (13, "端口被占用，请检查")
    API_SERVER_NOT_START_ERROR = (14, "api server 未开启，请检查")
    SYSTEM_PATH_MOVE_FAIL = (15, "系统路径迁移失败，请检查")
    SYSTEM_PATH_SPACE_NOT_ENOUGH = (16, "系统路径空间不足，请检查")

    @property
    def code(self):
        """获取状态码"""
        return self.value[0]

    @property
    def errmsg(self):
        """获取状态码信息"""
        return self.value[1]

