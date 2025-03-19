from enum import Enum


class ModelStatus(Enum):
    NOT_DOWNLOAD = (0, '未下载')
    DOWNLOAD_WATING = (1, '等待下载')
    DOWNLOADING = (2, "下载中")
    DOWNLOAD_SUCCESS = (3, "下载成功")
    DOWNLOADED_FAILED = (4, "下载失败")
    DOWNLOAD_PAUSED = (5, "下载暂停")
    NOT_LOAD = (10, "未加载")
    LOADING = (11, "加载中")
    LOAD_SUCCESS = (12, "加载成功")
    LOAD_FAILED = (13, "加载失败")
    WAITING_LOAD = (14, "等待加载")

    @property
    def status(self):
        return self.value[0]

    @property
    def desc(self):
        return self.value[1]


class SettingType(Enum):
    BASE = "BASE"
    WEB_SEARCH = "WEB_SEARCH"
    SENSITIVE = "SENSITIVE"


class ModelType(Enum):
    INFERENCE = 1
    PLUGIN = 2
    EMBEDDING = 3


class ChatItemStatus(Enum):
    WAIT_TO_PROCESS = (0, "待处理")
    SUCCESS = (1, "成功")
    ERROR = (2, "错误")

    @property
    def status(self):
        return self.value[0]

    @property
    def desc(self):
        return self.value[1]


class ChatItemRole(Enum):
    USER = "user"
    SYSTEM = "system"

    @property
    def role(self):
        return self.value

class FileAnalysisStatus(Enum):
    FAILED = -1
    PENDING = 0
    PROCESSING = 1
    DONE = 2