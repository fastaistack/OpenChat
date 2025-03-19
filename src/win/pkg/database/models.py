from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime, BigInteger,Text,Float
from datetime import datetime

from sqlalchemy.orm import relationship

from .database import Base


class ChatSession(Base):
    __tablename__ = "chat_session"

    id = Column(String, primary_key=True)
    session_name = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    create_time = Column(DateTime, default=datetime.now(), nullable=False)
    update_time = Column(DateTime, default=datetime.now(), nullable=False)


class ChatItem(Base):
    __tablename__ = "chat_item"
    __table_args__ ={"mysql_charset":"utf8mb4", "mysql_collate":"utf8mb4_unicode_ci"}

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    session_id = Column(String, nullable=False)
    question_id = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    think_text = Column(Text, nullable=False)
    response = Column(String, nullable=True)
    refs = Column(String, nullable=True)
    recommend_question = Column(String, nullable=True)
    like_type = Column(Integer, nullable=False, default=0)
    role = Column(String, nullable=False, default="")
    status = Column(Integer, nullable=False, default=0)
    model_id = Column(Integer, nullable=False, default=0)
    ext_info = Column(String, nullable=True)
    create_time = Column(DateTime, default=datetime.now(), nullable=False)
    update_time = Column(DateTime, default=datetime.now(), nullable=False)


class PluginMo(Base):
    __tablename__ = "plugins_mo"

    plugin_id = Column(Integer, primary_key=True, autoincrement="auto")
    plugin_logo = Column(String, nullable=True)
    plugin_key = Column(String, nullable=True)
    plugin_name = Column(String, nullable=True)
    plugin_name_en = Column(String, nullable=True)
    plugin_name_cn = Column(String, nullable=True)
    plugin_path = Column(String, nullable=False)
    plugin_type = Column(String, default="normal", nullable=False)  #normal: 可选插件  model: 模型插件
    plugin_order = Column(Integer, default=0, nullable=False)
    plugin_param = Column(String, nullable=True)
    plugin_status = Column(Boolean, default=False, nullable=False)
    description = Column(String, nullable=True)
    description_en = Column(String, nullable=True)
    description_cn = Column(String, nullable=True)

    user_id = Column(String, nullable=False)
    create_time = Column(DateTime, onupdate=datetime.now, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, onupdate=datetime.now, default=datetime.now, comment='更新时间')



class SessionPlugins(Base):
    __tablename__ = 'session_plugins'

    session_id = Column(String, nullable=False)
    plugin_id = Column(Integer, nullable=False)
    session_status = Column(Boolean, default=False, nullable=True)  # 默认0，不激活（禁用），1：激活
    plugin_param = Column(String, nullable=True)

    id = Column(Integer, primary_key=True, autoincrement=True)
    create_time = Column(DateTime, default=datetime.now(), nullable=True)
    update_time = Column(DateTime, default=datetime.now(), nullable=True)



class UserPluginParam(Base):
    __tablename__ = "user_plugin_param"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    session_id = Column(String, nullable=False)
    param_key = Column(String, nullable=False)
    param_value = Column(String, nullable=False)


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement="auto")
    user_id = Column(String, nullable=False)
    config_key = Column(String, nullable=False)
    config_value = Column(String, nullable=False)


class Model(Base):
    __tablename__ = "model"

    id                   = Column(Integer,    primary_key=True, autoincrement=True)
    name                 = Column(String,     nullable=False)
    key                  = Column(String,     nullable=False)
    author               = Column(String,     nullable=False)
    user                 = Column(String,     nullable=True)
    local_path           = Column(String,     nullable=True)  # 本地下载路径
    modelscope_path      = Column(String,     nullable=True)  # 魔搭社区路径
    web_path             = Column(String,     nullable=True)  # web访问路径
    files_size           = Column(BigInteger, nullable=True)  # 模型文件大小
    task_type            = Column(String,     nullable=True)  # 模型任务类型
    opensource_license   = Column(String,     nullable=True)  # 开源协议
    framework            = Column(String,     nullable=True)  # 开源协议
    labels               = Column(String,     nullable=True)  # 标签
    hardware_requirement = Column(String,     nullable=True)  # 硬件要求
    description          = Column(String,     nullable=True)
    release_time         = Column(String,     nullable=True)
    base_info            = Column(String,     nullable=True)
    status               = Column(Integer,    nullable=False)
    type                 = Column(Integer,    nullable=False)
    pic                  = Column(String,     nullable=True)  # 图标的base64编码
    plugin               = Column(String,     nullable=True)
    precision_list       = Column(String,     nullable=True)  #模型精度列表, [int8, int16]
    precision_selected   = Column(String,     nullable=True)  # 模型精度选择int8
    api_key              = Column(String,     nullable=True) # 模型的api_key
    url                  = Column(String,     nullable=True) # 模型的url

class TUsers(Base):
    __tablename__ = 'users'

    user_id = Column(String(32), primary_key=True, index=True)
    user_name = Column(String(32), nullable=False)
    password = Column(String(64))  # hashed
    salt = Column(String(32))
    mobile = Column(String(32))
    email = Column(String(32))
    creator = Column(String(32), comment='创建人')
    create_time = Column(DateTime, onupdate=datetime.now, default=datetime.now, comment='创建时间')
    editor = Column(String(32), comment='编辑人')
    edite_time = Column(DateTime, onupdate=datetime.now, default=datetime.now, comment='编辑时间')
    state = Column(Integer, default=0, comment='用户状态:0=正常,1=禁用')


class TUserRoles(Base):
    __tablename__ = 'user_roles'

    id = Column(String(32), primary_key=True, index=True)
    user_id = Column(String(32))
    role_id = Column(String(32))


class TRoles(Base):
    __tablename__ = 'roles'

    role_id = Column(String(32), primary_key=True, index=True)
    role_name = Column(String(64))  # root admin owner group
    description = Column(String(64))  # 描述，如：root 管理员 拥有者 组
    parent_id = Column(String(32))  # 父角色的id


class TUseInfo(Base):
    __tablename__ = "use_info"

    id          = Column(Integer,       primary_key=True,       autoincrement="auto")
    user_id     = Column(String(32),    nullable=False)
    login_time  = Column(String,        nullable=False)
    logout_time = Column(String,        nullable=False)
    use_time    = Column(String,        nullable=False)
    version     = Column(String,        nullable=False)
    is_send     = Column(Boolean,       default=False)


class TPerms(Base):
    __tablename__ = 'perms'

    perm_id = Column(String(32), primary_key=True, index=True)
    parent_id = Column(String(32))  # 父权限的id
    perm_name = Column(String(64))  # 创建用户
    perm_uri = Column(String(128))  # URL规则，如：account:create


class TRolePerms(Base):
    __tablename__ = 'role_perms'

    id = Column(String(32), primary_key=True, index=True)
    role_id = Column(String(32))
    perm_id = Column(String(32))


class Knowledge(Base):
    __tablename__ = "knowledge"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 0表示临时知识库
    description = Column(String, nullable=False)
    config = Column(String, nullable=False)
    user = Column(String, nullable=False)
    createtime = Column(String, nullable=False)


class KnowledgeFile(Base):
    __tablename__ = "file"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    knowledgeid = Column(String, ForeignKey("knowledge.id"))
    size = Column(String, nullable=False)
    bytetotal = Column(Integer, nullable=False)
    createtime = Column(String, nullable=False)
    status = Column(Integer, nullable=False)
    process = Column(Float, nullable=False)
    knowledge = relationship(Knowledge) 

class OptLog(Base):
    __tablename__ = "optlog"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    status = Column(Integer, nullable=False)#0 为迁移 1 迁移中，2 迁移成功，3 迁移失败
    reason = Column(String, nullable=False)
    inprocess = Column(String, nullable=False)
    createtime = Column(String,nullable=False)

class ModelDownloadChunk(Base):
    __tablename__ = "model_download_chunk"

    id               = Column(String, primary_key=True)
    modelscope_path  = Column(String,  nullable=False)
    revision         = Column(String,  nullable=False)
    file_path        = Column(String,  nullable=False)
    file_size        = Column(Integer, nullable=False)
    size             = Column(Integer, nullable=False)
    index            = Column(Integer, nullable=False)
    start_pos        = Column(Integer, nullable=False)
    end_pos          = Column(Integer, nullable=False)
    status           = Column(Integer, nullable=False)
    md5              = Column(String,  nullable=True)
    tmp_file         = Column(String,  nullable=True)

class ModelMoveProgress(Base):
    __tablename__ = "model_move_progress"

    id               = Column(String,  primary_key=True)
    model_id         = Column(Integer,  nullable=False)
    model_name       = Column(String,  nullable=False)
    modelscope_path  = Column(String,  nullable=False)
    revision         = Column(String,  nullable=True)
    origin_file      = Column(String,  nullable=False)
    destion_file     = Column(String,  nullable=False)
    md5              = Column(String,  nullable=True)
    status           = Column(Integer, nullable=False)
    message          = Column(String,  nullable=True)
    time_stamp       = Column(Integer,  nullable=False)