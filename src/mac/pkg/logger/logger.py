from loguru import logger

from ..projectvar import Projectvar
from ..projectvar import constants as const
import threading

gvar = Projectvar()

class Log(object):
    __instance_lock = threading.Lock()

    def __new__(cls, *args, **kw):
        if not hasattr(Log, "_instance"):
            with Log.__instance_lock:
                if not hasattr(Log, "_instance"):
                    Log._instance = object.__new__(cls)
                    Log._logger = logger
                    Log._logger.add(gvar.get_cache_path() + "/" + const.YUAN_LOG_NAME, rotation=const.YUAN_LOG_ROTATION, retention=const.YUAN_LOG_RETENTION, compression="zip")
                    
        return Log._instance._logger