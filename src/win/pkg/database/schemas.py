from typing import Optional
from fastapi import UploadFile

from pydantic import BaseModel, Field, root_validator
from datetime import datetime


class PluginBaseMo(BaseModel):
    
    plugin_logo: str			= Field(default="logo_index", example="plugin_logo_index")						# string （“sdfasdfasdf‘） 		支持编辑
    plugin_key: str             = Field(default="", example="plugin_key")
    plugin_name: str            = Field(default="", example="plugin_name")
    plugin_name_en: str			= Field(..., example="plugin_name_en")  # 插件名
    plugin_name_cn: str			= Field(..., example="plugin_name_cn")  # 插件名
    plugin_path: str			= Field(..., example="pkg/plugins")	# 插件路径
    plugin_order: int			= Field(..., example="plugin_name_cn")	# 插件执行顺序	,前处理：5 4 3 2 1 中处理：0 后处理：-1 -2 -3 -4 -5 
    plugin_type: str			= Field(..., example="plugin_name_cn")	# 插件类型			default：默认插件，normal：可选插件
    plugin_status: bool  		= Field(default=False, example="False") # defualt False：未启用   True ：启用
    plugin_param: str			= Field(default="[]", example="['plugin_param': param1]") # 默认参数  自己获取插库
    description: str            = Field(default="", example="plugin_name")
    description_en: str 		= Field(default="", example="description_en")   # 描述信息  						支持中英文   支持编辑
    description_cn: str 		= Field(default="", example="description_cn")   # 描述信息  						支持中英文   支持编辑
    
    #  支持orm
    class Config:
        from_attributes = True

class  PluginInDB(PluginBaseMo):
    plugin_id: int				= Field(..., example="2")	# 插件id
    user_id: str 		        = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0") # 创建人id  通过header获取
    create_time: datetime       = Field(example="2024-03-25 15:33:00")
    update_time: datetime       = Field(example="2024-03-25 15:33:00")


class SessionPluginBase(BaseModel):
    session_id: str 			= Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")	# session id
    plugin_id: int				= Field(..., example="1")	# 插件id
    plugin_param: str			= Field(example="[{'plugin_param': param1}]")# 插件参数
    session_status: bool	    = Field(default=False, example="False")	# session 对应该插件是否启用   False：未启用  True：启用

    #  支持orm
    class Config:
        from_attributes = True
	
class SessionPluginInDB(SessionPluginBase):
    id: int 					= Field(..., example="1")			# session id
    create_time: datetime       = Field(example="2024-03-25 15:33:00")
    update_time: datetime       = Field(example="2024-03-25 15:33:00")
 



class PluginBase(BaseModel):
    name: str
    path: str
    plugin_order: int
    plugin_type: str
    status: bool = False  # defualt value "False"


class PluginCreate(PluginBase):
    create_time: datetime = datetime.now()


class PluginUpdate(PluginBase):
    update_time: datetime = datetime.now()


class Plugin(PluginBase):
    id: int
    role: str = "user"
    description: str = None


class UserPluginBase(BaseModel):
    user_id: str
    plugin_status: bool
    plugin_name: str
    plugin_id: int
    plugin_type: str
    plugin_order: int


class UserPlugin(UserPluginBase):
    id: int
    role: str = "user"
    create_time: datetime = datetime.now()
    update_time: datetime = datetime.now()


class UserPluginSettingBase(BaseModel):
    user_id: str
    plugin_id: int


class UserPluginSettingArg(UserPluginSettingBase):
    arg_name: str
    arg_value: str


class UserPluginSetting(UserPluginSettingArg):
    arg_datatype: str
    arg_precision: int
    arg_max: float
    arg_min: float
    arg_maxlen: int


class BaseSettingInfo(BaseModel):
    top_k: int
    top_p: float
    temperature: float
    multi_dialog_turns: int
    response_length: int


class WebSearchSettingInfo(BaseModel):
    web_search_switch: bool
    serper_key: str
    embedding_model_path: str
    retrieve_topk: int
    template: str


class SensitiveSettingInfo(BaseModel):
    style_filter_list: list
    local_words: object
    baidu_api: object
    local_model: object


class SettingLocalWordsInfo(BaseModel):
    interval_tokens: int


class SettingBaiduApiInfo(BaseModel):
    interval_tokens: int
    api_key: str
    secret_key: str


class SettingLocalModelInfo(BaseModel):
    interval_tokens: int = 20
    filter_model_list: Optional[list] = None
    model_id: Optional[int] = None


class SensitiveSettingUpdateInfo(BaseModel):
    plugin_id: int
    local_words: Optional[SettingLocalWordsInfo] = None
    baidu_api: Optional[SettingBaiduApiInfo] = None
    local_model: Optional[SettingLocalModelInfo] = None
    style_filter_list: list


class SensitiveSettingPluginParamInfo(BaseModel):
    local_words: dict
    baidu_api: dict
    local_model: dict
    style_filter_list: list


class ChatMessageInfo(BaseModel):
    message: str
    session_id: str
    dialogs_history: Optional[list] = None  # 格式如[{"question"："xxx", "answer":"yyy"}, {"question"："hhh", "answer":"zzz"}]，用户最新问题不要加到list中
    user_id: Optional[str] = None
    reference_info: Optional[dict] = None  # {file:[{file_id:"", file_name:""}], knowledge_id:"", knowledge_name:"", "web_search_type":""}


class ReChatMessageInfo(BaseModel):
    question_id: str


class ChatMessageItemRefsInfo(BaseModel):
    url: str
    text: str
    title: str

    def to_dict(self):
        return {"url": self.url}


class ChatMessageItemRecommendQuestionInfo(BaseModel):
    question: str

    def to_dict(self):
        return {"question": self.question}


class UserPluginWebSearchParamInfo(BaseModel):
    web_api_key: Optional[str] = None
    embedding_model_id: Optional[int] = None
    retrieve_topk: int
    template: str
    style_search: str


class UserPluginWebSearchParamUpdateInfo(BaseModel):
    web_api_key: Optional[str] = None
    embedding_model_id: Optional[int] = None
    retrieve_topk: int
    template: str
    style_search: str
    plugin_id: int


class ChatMessageItemInfo(BaseModel):
    message: str
    refs: list[ChatMessageItemRefsInfo]
    recommend_question: list[ChatMessageItemRecommendQuestionInfo]
    time: int
    browser_flag: bool

    def to_dict(self):
        return {"message": self.message, "finish_flag": self.finish_flag, "id": self.id,
                "refs": self.convert_to_dict(self.refs),
                "recommend_question": self.convert_to_dict(self.recommend_question),
                "time": self.time, "browser_flag": self.browser_flag}


class ChatMessageResponseInfo(ChatMessageItemInfo):
    finish_flag: bool
    id: str

    def to_dict(self):
        return {"message": self.message, "finish_flag": self.finish_flag, "id": self.id,
                "refs": self.refs, "recommend_question": self.recommend_question,
                "time": self.time, "browser_flag": self.browser_flag}


class ChatSessionInfo(BaseModel):
    id: str
    session_name: str
    user_id: str
    create_time: int
    update_time: int


class ChatItemInfo(BaseModel):
    id: str
    session_id: str
    text: str
    think_text: str
    response: Optional[str] = None
    refs: list[dict]
    recommend_question: list[dict]
    like_type: int
    role: str
    question_id: str
    create_time: int
    model_id: int
    model_pic: Optional[str] = None
    model_name: Optional[str] = None
    reference_info: Optional[dict] = None


# 会话信息-带时间
class ChatSessionTimeInfo(BaseModel):
    time_label: str
    time_desc: str
    session_list: list[dict]


class KnowledgeBase(BaseModel):
    name: str
    description: str
    files: list[UploadFile]


class KnowledgeCreate(KnowledgeBase):
    pass


class Knowledge(KnowledgeBase):
    id: int


class KnowledgeQuery(BaseModel):
    name: str
    page: int
    pagesize: int


# token
class TokenBase(BaseModel):
    access_token: str
    refresh_token: str = Field(default="")
    token_type: str = Field(default="bearer", example="bearer")
    user_name: Optional[str] = Field(default="", exclude=True)


# user
class UserBase(BaseModel):
    user_name: str = Field(..., example="tom")
    password: str = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")
    salt: str = Field(..., example="salt")
    mobile: str = Field(default="", example="18788889999")
    email: str = Field(default="", example="test@test.com")

    class Config:
        # orm_mode = True
        from_attributes = True


class UserInDB(UserBase):
    user_id: str = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")
    creator: str = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")
    create_time: datetime = Field(example="2024-03-25 15:33:00")
    editor: str = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")
    edite_time: datetime = Field(example="2024-03-25 15:33:00")
    state: int = Field(default=0)


class UserInDBPlus(UserInDB):
    user_role_id: str = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")
    role_id: str = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")
    role_name: str = Field(..., example="root")  # root admin owner group
    description: str = Field(..., example="超级管理员用户")  # 描述，如：创建用户


# user role
class UserRoleBase(BaseModel):
    user_id: str = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")
    role_id: str = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")

    class Config:
        # orm_mode = True
        from_attributes = True


class UserRoleInDB(UserRoleBase):
    id: str = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")


class UserRoleInDBPlus(UserRoleInDB):
    user_name: str = Field(..., example="tom")
    state: int = Field(..., example=0)
    role_name: str = Field(..., example="root")  # root admin owner group
    description: str = Field(..., example="超级管理员用户")  # 描述，如：创建用户


# role
class RoleBase(BaseModel):
    role_name: str = Field(..., example="root")  # root admin owner group
    description: str = Field(..., example="超级管理员用户")  # 描述，如：创建用户
    parent_id: str = Field(default="", example="79e43f601fec4a3ea3232f306c07dfe0")  # 父角色的id

    class Config:
        # orm_mode = True
        from_attributes = True


class RoleInDB(RoleBase):
    role_id: str = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")


# role perm
class RolePermBase(BaseModel):
    role_id: str = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")
    perm_id: str = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")

    class Config:
        # orm_mode = True
        from_attributes = True


class RolePermInDB(RolePermBase):
    id: str = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")


class RolePermInDBPlus(RolePermInDB):
    role_name: str = Field(..., example="root")  # root admin owner group
    description: str = Field(..., example="超级管理员用户")  # 描述，如：创建用户
    perm_name: str = Field(..., example="创建用户")  # 权限名，如：创建用户
    perm_uri: str = Field(..., example="/account/create")  # /account/create


# perm
class PermBase(BaseModel):
    perm_name: str = Field(..., example="创建用户")  # 权限名，如：创建用户
    perm_uri: str = Field(..., example="/account/create")  # /account/create
    parent_id: str = Field(default="", example="79e43f601fec4a3ea3232f306c07dfe0")  # 父角色的id


class PermInDB(PermBase):
    perm_id: str = Field(..., example="79e43f601fec4a3ea3232f306c07dfe0")

    class Config:
        # orm_mode = True
        from_attributes = True


class RoleInDBDict(RoleInDB):
    perms: list[PermInDB] = Field(default=[])


class PageParamBase(BaseModel):
    page: int = Field(..., ge=1)
    pagesize: int = Field(...)  # 当pagesize==-1的时候， page_end为正无穷大，实际效果为全表查询

    page_start: int = Field(exclude=True, default=0)
    page_end: int = Field(exclude=True, default=0)


    @root_validator(skip_on_failure=True)
    def check_passwords_match(cls, values):
        page_idx, page_size = values.get('page'), values.get('pagesize')
        page_start = (page_idx - 1) * page_size
        page_end = page_idx * page_size
        values['page_start'] = page_start
        values['page_end'] = page_end
        return values


# 返回list
class OutputListPlus(PageParamBase):
    data: list = Field(default=[])
    total: int = Field(default=0)


class KnowledgeUpdateBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str]
    user: Optional[list[str]] = None
    knowledge_setting: Optional[str]


class KnowledgeBase(BaseModel):
    id: str
    name: str
    description: str
    createtime: str
    user: list[str]
    config: dict
    type: str


class KnowledgeCreate(KnowledgeBase):
    pass


class KnowledgeFileBase(BaseModel):
    id : str
    name : str
    knowledgeid : str
    size : str
    bytetotal : int
    createtime : str
    status: int
    process: int
class KnowledgeJoinFile(BaseModel):
    id: str
    name: str
    description: str
    createtime: str
    user: list[str]
    config: dict
    type: str
    count: int
    volume: str
class KnowledgeQuery(BaseModel):
    data: list[KnowledgeJoinFile]
    page: int
    pagesize: int
    total: int


class KnowledgeFileQuery(BaseModel):
    data: list[KnowledgeFileBase]
    page: int
    pagesize: int
    total: int


class KnowledgeGlobalConfigUpdateBase(BaseModel):
    chromadb_persist_path: str
    embed_model: str

class KnowledgeFileChatConfig(BaseModel):
    sessionid: str
    embed_param: dict
    embed_model: str

class GetKnowledgeSessionConfigPayload(BaseModel):
    plugin_key: str

class UpdateKnowledgeSessionConfigPayload(BaseModel):
    name: Optional[str] = None
    plugin_key: str
    description: Optional[str]
    user: Optional[list[str]] = None
    knowledge_setting: Optional[str]
