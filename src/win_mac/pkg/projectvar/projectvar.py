import threading


class Projectvar(object):
    __instance_lock = threading.Lock()

    def __new__(cls, *args, **kw):
        if not hasattr(Projectvar, "_instance"):
            with Projectvar.__instance_lock:
                if not hasattr(Projectvar, "_instance"):
                    Projectvar._instance = object.__new__(cls)
                    Projectvar._db_filename = ""
                    Projectvar._home_path = ""
                    Projectvar._cache_path = ""
                    Projectvar._plugins = []
                    Projectvar._stop_id_ = []
                    Projectvar._model = None
                    Projectvar._tokenizer = None
                    Projectvar._model_info= {} # {"url":url, "api_key":api_key,"model_selected":precise_select}
                    Projectvar.glossary= -1
                    Projectvar._translator_model_info = {} # {"url":url, "api_key":api_key,"model_selected":precise_select}
                    Projectvar._needstop = []  #结束翻译线程
                    Projectvar._update_progress = ''
                    Projectvar._complated_page_count = -1
                    Projectvar._model_setting = ''
        return Projectvar._instance
    def set_db_filename(self, name):
        self._db_filename = name
        return name
    
    def get_db_filename(self):
        return self._db_filename

    def set_home_path(self, path):
        self._home_path = path
        return path
    
    def get_home_path(self):
        return self._home_path
    
    def set_cache_path(self, path):
        self._cache_path = path
        return path
    
    def get_cache_path(self):
        return self._cache_path
    
    def get_plugins(self):
        return self._plugins
    
    def set_plugins(self, plugins):
        self._plugins = plugins

    def get_stop_id(self):
        return self._stop_id_

    def set_stop_id(self, id):
        self._stop_id_.append(id)

    def delete_stop_id(self, id):
        for item in self._stop_id_:
            if self._stop_id_ == id:
                self._stop_id_.remove(id)
        return True

    def set_model(self, model):
        self._model = model

    def get_model(self):
        return self._model

    def set_tokenizer(self, tokenizer):
        self._tokenizer = tokenizer

    def get_tokenizer(self):
        return self._tokenizer
    
    def set_model_info(self, _model_info):
        self._model_info = _model_info

    def get_model_info(self):
        return self._model_info
    
    def set_glossary(self, glossary_id):
        self.glossary = glossary_id

    def get_glossary(self):
        return self.glossary
    
    def get_trans_model_info(self):
        return self._translator_model_info
    
    def set_trans_model_info(self, _translator_model_info):
        self._translator_model_info = _translator_model_info

    def set_needstop(self, needstop):
        self._needstop.append(needstop)

    def get_needstop(self):
        return self._needstop
    
    def delete_needstop(self, needstop):
        for item in self._needstop:
            if item == needstop:
                self._needstop.remove(needstop)
        return True
    
    def set_update_progress(self, progress):
        self._update_progress = progress

    def get_update_progress(self):
        return self._update_progress
    
    def set_complated_page_count(self, page_count):
        self._complated_page_count = page_count

    def get_complated_page_count(self):
        return self._complated_page_count
    
    def set_model_setting(self, model_setting):
        self._model_setting = model_setting

    def get_model_setting(self):
        return self._model_setting