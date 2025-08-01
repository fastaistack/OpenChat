import sqlite3
import os
from pkg.logger import Log
from pkg.projectvar import constants as consts

log = Log()

migrate_table_map = {
    'chat':'chat_item_table_migrate,chat_session_table_migrate',
    'agent':'agent_table_migrate,assistants_table_migrate',
    'knowledge':'file_table_migrate,knowledge_table_migrate,optlog_table_migrate',
    'translate':'glossary_item_table_migrate,glossary_page_table_migrate,translated_item_table_migrate,translated_text_item_table_migrate',
    'models':'model_table_migrate,model_list_table_migrate',
    'parameters':'perms_table_migrate,plugins_model_table_migrate,role_perms_table_migrate,roles_table_migrate,session_plugins_table_migrate,settings_table_migrate,use_info_table_migrate,user_plugin_param_table_migrate,user_roles_table_migrate,users_table_migrate'
}

default_value = {
    'BOOLEAN':0,
    'FLOAT':0.0,
    'VARCHAR':'',
    'TEXT':'',
    'DATATIME':'',
    'INTEGER':0,
    'REAL':0,
    'BIGINT':0,
    'TINYINT':0
}

def doing_migrate(keyword:str):
    items = migrate_table_map.get(keyword)
    need_migrate_items = items.split(',')
    if not need_migrate_items:
        return
    
        user_home_path = os.path.expanduser('~')
    # db_path = os.path.join(user_home_path,const.OPENCHAT_CACHEPATH)
    if consts.SYSTEM == consts.WINDOWS:
        db_path = os.path.join(user_home_path,'.openchat')
    else:
        db_path = os.path.join(user_home_path,'openchat')
    # log.info(db_path)
    # 连接到新旧数据库
    conn_new = sqlite3.connect(os.path.join(db_path,'openchat.db'))
    conn_old = sqlite3.connect(os.path.join(db_path,'openchat_old.db'))

    cursor_old = conn_old.cursor()
    cursor_new = conn_new.cursor()

    for item in need_migrate_items:
        eval(item+'(conn_new, cursor_old, cursor_new)')
        
    return "success"



def table_migrate(item, conn_new, cursor_old, cursor_new):
    """
    model表迁移
    """
    # item = 'model'
    cursor_old.execute(f"PRAGMA table_info({item})")
    columns_info_old = cursor_old.fetchall() # 表格信息（列名1、数据类型2、是否为空3、是否主键）
    if not columns_info_old: # 属于新表新增加的表,新增加的表会在源代码的data_init中走完流程
        # log.info(f"旧表不存在:{item}表")
        log.info(f"旧表不存在:{item}表")
        return
    old_columns = [
        col[1] for col in columns_info_old
        if not (col[5] > 0 and col[2].upper() == 'INTEGER') # 排除自增主键 自增主键类型（INTEGER PRIMARY KEY会自增）
    ]
    
    ####### 1.新旧结构对比，获取有效迁移列
    cursor_new.execute(f"PRAGMA table_info({item})")
    columns_info_new = cursor_new.fetchall() # 表格属性
    # 获取新表结构
    new_columns = [
        col[1] for col in columns_info_new
        if not (col[5] > 0 and col[2].upper() == 'INTEGER')
    ]
    # 获取有效的迁入列即相同的列
    valid_columns = [col for col in new_columns if col in old_columns]
    
    ####### 2.根据有效迁移列，获取旧表有效内容
    cursor_old.execute(f"SELECT {','.join(valid_columns)} FROM {item};")
    rows = cursor_old.fetchall()
    
    ####### 3.获取新表增加的列
    added_columns = [col for col in new_columns if col not in old_columns]
    if added_columns:
        log.info(f"表 {item} 新增的列: {added_columns}")
        for added_column in added_columns:
            valid_columns.append(added_column)
        # 更新rows
        for col_info in columns_info_new:
            # 新增列赋初值
            if col_info[1] in added_columns: 
                log.info(f"列名: {col_info[1]}, 数据类型: {col_info[2]}, 是否允许为空: {col_info[3]}, 是否为主键: {col_info[5]}")
                for i,row in enumerate(rows):
                    temp_list = list(row)
                    ####### 4.赋默认值/初值
                    temp_list.append(default_value[col_info[2]])
                    rows[i] = tuple(temp_list)
    ####### 5.组织SQL插入语句
    placeholders =  ','.join(["?"]*len(valid_columns))
    insert_sql = f"INSERT INTO {item} ({','.join(valid_columns)}) VALUES ({placeholders})"
    ####### 6.执行插入
    conn_new.execute("BEGIN TRANSACTION")
    for row in rows:
        try:
            cursor_new.execute(insert_sql,row)
        except Exception as e:
            log.error(f"执行 {insert_sql} 插入失败，error:{e}")
            continue
            
    log.info(f"迁移{item}表完成：{len(rows)}条数据")
    conn_new.commit()

def agent_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("Agent",conn_new, cursor_old, cursor_new)
    
def assistants_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("assistants",conn_new, cursor_old, cursor_new)
    
def chat_item_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("chat_item",conn_new, cursor_old, cursor_new)
    
def chat_session_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("chat_session",conn_new, cursor_old, cursor_new)
    
def file_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("file",conn_new, cursor_old, cursor_new)
    
def glossary_item_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("glossary_item",conn_new, cursor_old, cursor_new)
    
def glossary_page_table_migrate( conn_new, cursor_old, cursor_new):
    table_migrate("glossary_page",conn_new, cursor_old, cursor_new)
    
def knowledge_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("knowledge",conn_new, cursor_old, cursor_new)
    
def model_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("model",conn_new, cursor_old, cursor_new)

def model_list_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("model_list",conn_new, cursor_old, cursor_new)
    
def optlog_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("optlog",conn_new, cursor_old, cursor_new)
    
def perms_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("perms",conn_new, cursor_old, cursor_new)
    
def plugins_mo_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("plugins_mo",conn_new, cursor_old, cursor_new)
    
def role_perms_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("role_perms",conn_new, cursor_old, cursor_new)
    
def roles_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("roles",conn_new, cursor_old, cursor_new)

def session_pluginst_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("session_plugins",conn_new, cursor_old, cursor_new)
    
def settings_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("settings",conn_new, cursor_old, cursor_new)
    
def translated_item_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("translated_item",conn_new, cursor_old, cursor_new)
    
def translated_text_item_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("translated_text_item",conn_new, cursor_old, cursor_new)
    
def use_info_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("use_info",conn_new, cursor_old, cursor_new)
    
def user_plugin_param_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("user_plugin_param",conn_new, cursor_old, cursor_new)
    
def user_roles_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("user_roles",conn_new, cursor_old, cursor_new)
    
def users_table_migrate(conn_new, cursor_old, cursor_new):
    table_migrate("users",conn_new, cursor_old, cursor_new)
    

# 迁移
def migrate():
    user_home_path = os.path.expanduser('~')
    # db_path = os.path.join(user_home_path,const.OPENCHAT_CACHEPATH)
    if consts.SYSTEM == consts.WINDOWS:
        db_path = os.path.join(user_home_path,'.openchat')
    else:
        db_path = os.path.join(user_home_path,'openchat')
    # log.info(db_path)
    # 连接到新旧数据库
    conn_new = sqlite3.connect(os.path.join(db_path,'openchat.db'))
    conn_old = sqlite3.connect(os.path.join(db_path,'openchat_old.db'))

    cursor_old = conn_old.cursor()
    cursor_new = conn_new.cursor()
        
    try:
        
        agent_table_migrate(conn_new, cursor_old, cursor_new) # 李
        assistants_table_migrate(conn_new, cursor_old, cursor_new)
        chat_item_table_migrate(conn_new, cursor_old, cursor_new)
        chat_session_table_migrate(conn_new, cursor_old, cursor_new)
        file_table_migrate(conn_new, cursor_old, cursor_new)
        glossary_item_table_migrate(conn_new, cursor_old, cursor_new)
        glossary_page_table_migrate(conn_new, cursor_old, cursor_new)
        knowledge_table_migrate(conn_new, cursor_old, cursor_new)
        model_table_migrate(conn_new, cursor_old, cursor_new) # 韩
        model_list_table_migrate(conn_new, cursor_old, cursor_new)
        optlog_table_migrate(conn_new, cursor_old, cursor_new)
        perms_table_migrate(conn_new, cursor_old, cursor_new)
        plugins_mo_table_migrate(conn_new, cursor_old, cursor_new)
        role_perms_table_migrate(conn_new, cursor_old, cursor_new)
        roles_table_migrate(conn_new, cursor_old, cursor_new)
        session_pluginst_table_migrate(conn_new, cursor_old, cursor_new)
        settings_table_migrate(conn_new, cursor_old, cursor_new) # 贺
        translated_item_table_migrate(conn_new, cursor_old, cursor_new)
        translated_text_item_table_migrate(conn_new, cursor_old, cursor_new)
        use_info_table_migrate(conn_new, cursor_old, cursor_new)
        user_plugin_param_table_migrate(conn_new, cursor_old, cursor_new)
        user_roles_table_migrate(conn_new, cursor_old, cursor_new)
        users_table_migrate(conn_new, cursor_old, cursor_new)
                
        conn_old.close()
        return True
            
    except sqlite3.Error as e:
        import traceback
        log.info(traceback.format_exc())
        log.info(f"插入数据表失败：{str(e)}")
        conn_new.rollback()
        conn_new.close()
        conn_old.close()
        return False

# def clean():
#     for item in table:
#         cursor_new.execute(f"DELETE FROM {item}")  # 清空所有记录
#         conn_new.commit()
#         log.info("成功清空表数据")

# migrate()