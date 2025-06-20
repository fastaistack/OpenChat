import sqlite3
import os
from pkg.logger import Log
from pkg.projectvar import constants as consts

log = Log()

# async def migrate():
def migrate():
    
    table = [
        'model',
        'chat_item', 
        'chat_session', 
        'file', 
        'knowledge', 
        'session_plugins',
        'glossary_item',
        'glossary_page',
        'translated_item',
        'translated_text_item',
        'assistants',
        'Agent',
        'settings',
    ]

    user_home_path = os.path.expanduser('~')
    # db_path = os.path.join(user_home_path,const.OPENCHAT_CACHEPATH)
    if consts.SYSTEM == consts.WINDOWS:
        db_path = os.path.join(user_home_path,'.openchat')
    else:
        db_path = os.path.join(user_home_path,'openchat')
    # print(db_path)
    # 连接到新旧数据库
    conn_new = sqlite3.connect(os.path.join(db_path,'openchat.db'))
    conn_old = sqlite3.connect(os.path.join(db_path,'openchat_old.db'))

    cursor_old = conn_old.cursor()
    cursor_new = conn_new.cursor()
    # 获取旧表结构
        
    try:
        # 获取新的user_id
        cursor_new.execute(f"SELECT user_id FROM users WHERE user_name =='hello';")
        user_id = cursor_new.fetchone()[0]
        
        for item in table:
            # 获取旧表结构
            cursor_old.execute(f"PRAGMA table_info({item})")
            columns_info_old = cursor_old.fetchall()
            # print(f"old:{columns_info_old}")
            if not columns_info_old: # 属于新表新增加的表 不用管
                # print(f"旧表不存在:{item}表")
                log.info(f"旧表不存在:{item}表")
                continue
            old_columns = [
                col[1] for col in columns_info_old
                if not (col[5] > 0 and col[2].upper() == 'INTEGER') # 自增主键类型（INTEGER PRIMARY KEY会自增）
            ]
            
            # 获取新表结构
            cursor_new.execute(f"PRAGMA table_info({item})")
            columns_info_new = cursor_new.fetchall()
            new_columns = [
                col[1] for col in columns_info_new
                if not (col[5] > 0 and col[2].upper() == 'INTEGER')
            ]
            # print(f"new:{columns_info_new}")
            
            # 获取有效的迁入列即相同的列
            valid_columns = [col for col in new_columns if col in old_columns]
            
            # 获取旧表有效内容
            cursor_old.execute(f"SELECT {','.join(valid_columns)} FROM {item};")
            rows = cursor_old.fetchall()
            
            # 获取新表增加的列，并为新增加列赋初值
            added_columns = [col for col in new_columns if col not in old_columns]
            if added_columns:
                # print(f"表 {item} 新增的列: {added_columns}")
                log.info(f"表 {item} 新增的列: {added_columns}")
                for added_column in added_columns:
                    valid_columns.append(added_column)
                    # 更新rows
                for col_info in columns_info_new:
                    if col_info[1] in added_columns: # 新增列赋初值
                        # print(f"列名: {col_info[1]}, 数据类型: {col_info[2]}, 是否允许为空: {col_info[3]}, 是否为主键: {col_info[5]}")
                        log.info(f"列名: {col_info[1]}, 数据类型: {col_info[2]}, 是否允许为空: {col_info[3]}, 是否为主键: {col_info[5]}")
                        for i,row in enumerate(rows):
                            temp_list = list(row)
                            if col_info[2] == 'BOOLEAN':
                                temp_list.append(0)
                            elif col_info[2] == 'FLOAT':
                                temp_list.append(0.0)
                            elif col_info[2] == 'VARCHAR':
                                temp_list.append('')
                            elif col_info[2] == 'TEXT':
                                temp_list.append('')
                            elif col_info[2] == 'DATATIME':
                                temp_list.append('')
                            elif col_info[2] == 'INTEGER':
                                temp_list.append(0)
                            elif col_info[2] == 'REAL':
                                temp_list.append(0.0)
                            elif col_info[2] == 'BIGINT':
                                temp_list.append(0)
                            elif col_info[2] == 'TINYINT':
                                temp_list.append(0)
                            # row = tuple(temp_list)
                            rows[i] = tuple(temp_list)
            placeholders =  ','.join(["?"]*len(valid_columns))
            insert_sql = f"INSERT INTO {item} ({','.join(valid_columns)}) VALUES ({placeholders})"
            # print(insert_sql)
            # print(f"rows:{rows}")
            
            # 向新表中更新部分值key、user_id
            conn_new.execute("BEGIN TRANSACTION")
            for row in rows:
                if item == 'model':
                    # 更新model列表
                    index_api_key = valid_columns.index('api_key')
                    index_key = valid_columns.index('key')
                    temp_list = list(row)
                    if temp_list[index_key] == 'ollama': # ollama 单独处理
                        index_url = valid_columns.index('url')
                        url = '\'' + temp_list[index_url] + '\''
                        key = '\'' + temp_list[index_key] + '\''
                        api_key = '\'' + temp_list[index_api_key] + '\'' if temp_list[index_api_key] else "\'ollama\'"
                        update_sql = f"UPDATE {item} SET api_key = {api_key} , url = {url} WHERE key = {key};"
                        cursor_new.execute(update_sql)
                        continue
                    api_key = '\'' + temp_list[index_api_key] + '\'' if temp_list[index_api_key] else "\'\'"
                    key = '\'' + temp_list[index_key] + '\''
                    if temp_list[index_key] == 'deepseek_local': # deepseek_local单独处理
                        index_url = valid_columns.index('url')
                        url = '\'' + temp_list[index_url] + '\''
                        update_sql = f"UPDATE {item} SET api_key = {api_key} , url = {url} WHERE key = {key};"
                    else:
                        update_sql = f"UPDATE {item} SET api_key = {api_key} WHERE key = {key};"
                    # print(update_sql)
                    cursor_new.execute(update_sql)
                    continue
                if item == 'chat_session' or item == 'chat_item' or item == 'Agent':
                    # print("更新user_id")
                    # 更新user_id
                    if 'user_id' in valid_columns:
                        index = valid_columns.index('user_id')
                        temp_list = list(row)
                        temp_list[index] = user_id
                        row = tuple(temp_list)
                if item == 'Agent':
                    if row[8] == 'system': # 系统精选无需插入，只保留为user的
                        continue
                if item == 'settings':
                    index_config_key = valid_columns.index('config_key')
                    index_config_value = valid_columns.index('config_value')
                    temp_list = list(row)
                    config_key = '\'' + temp_list[index_config_key] + '\''
                    config_value = '\'' + temp_list[index_config_value] + '\''
                    update_sql = f'UPDATE {item} SET config_value = {config_value} where config_key = {config_key};'
                    cursor_new.execute(update_sql)
                    continue
                cursor_new.execute(insert_sql,row)
            # print(f"成功迁移{item}表：{len(rows)}条数据")
            log.info(f"成功迁移{item}表：{len(rows)}条数据")
            conn_new.commit()
        conn_new.close()
        conn_old.close()
        return True
            
    except sqlite3.Error as e:
        import traceback
        print(traceback.format_exc())
        # print(f"插入数据表失败：{str(e)}")
        conn_new.rollback()
        conn_new.close()
        conn_old.close()
        return False

# def clean():
#     for item in table:
#         cursor_new.execute(f"DELETE FROM {item}")  # 清空所有记录
#         conn_new.commit()
#         print("成功清空表数据")

# migrate()