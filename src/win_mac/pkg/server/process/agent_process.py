from sqlalchemy.orm import Session
from ...database.database import SessionLocal, engine
from ...database import models,schemas
from ...database.models import Assistants, Agent
from ...database.schemas import AgentBase
from ...logger import Log
from typing import Union, List, Dict
from sqlalchemy import and_, text
import importlib
import json
from pydantic import BaseModel
import uuid
from datetime import datetime
import os
from pathlib import Path

# 预设的头像路径列表
DEFAULT_AVATAR_PATHS = [
    "/icons/icon/ai-technology (1).png",
    "/icons/icon/ai-technology (2).png",
    "/icons/icon/ai-technology (3).png",
    "/icons/icon/ai-technology (4).png",
    "/icons/icon/ai-technology (5).png"
]

# 默认头像
DEFAULT_AVATAR = DEFAULT_AVATAR_PATHS[0]

# 预设的分类选项
AGENT_CATEGORIES = [
    "development",  # 开发
    "marketing",    # 营销
    "education",    # 教育
    "culture",      # 文化
    "tools",        # 工具
    "writing",      # 写作
    "job",       # 职业
    "entertainment", # 娱乐
    "mental_health", # 心理健康
    "normal"       # 普通
]

# 默认分类
DEFAULT_CATEGORY = "normal"

log = Log()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_welcome_message(agent_name: str) -> str:
    # 生成智能体开场白
    welcome_message = f"您好，我是{agent_name}。请随时向我提问。"
    return welcome_message

# def generate_welcome_message(agent_name: str, category: str = DEFAULT_CATEGORY) -> str:
#     # 根据智能体名称和分类生成欢迎语
#     # 基础欢迎语模板
#     welcome_templates = {
#         "development": f"您好！我是{agent_name}，一名开发助手。我可以帮助您解决编程问题、代码审查和技术选型。请告诉我您需要什么帮助？",
#         "marketing": f"您好！我是{agent_name}，专注于市场营销的助手。我可以协助您制定营销计划、分析市场趋势和优化转化。有什么我可以帮您的？",
#         "education": f"您好！我是{agent_name}，您的学习顾问。我可以帮助您理解复杂概念、制定学习计划和提高学习效率。有什么我可以为您讲解的？",
#         "culture": f"您好！我是{agent_name}，文化领域的助手。我对历史、艺术和文学有深入了解，可以为您提供相关知识和见解。",
#         "tools": f"您好！我是{agent_name}，您的工具助手。我可以帮助您解决各种实用问题，提供操作指导和建议。",
#         "writing": f"您好！我是{agent_name}，写作助手。我可以帮助您构思创意、润色文章和改进表达。您需要什么样的写作帮助？",
#         "job": f"您好！我是{agent_name}。我可以为您提供专业领域的帮助。",
#         "entertainment": f"您好！我是{agent_name}，娱乐领域的助手。我可以陪您做一些小游戏。",
#         "normal": f"您好！我是{agent_name}。我可以回答您的问题，提供信息和建议。请随时向我提问。"
#     }
    
#     # 获取对应分类的欢迎语，如果没有则使用通用欢迎语
#     return welcome_templates.get(category, welcome_templates["normal"])

def generate_recommended_questions(agent_name: str) -> List[str]:
    # 基于智能体描述生成相关问题
    recommended_questions = [
        f"{agent_name}能做什么？",
        f"你有哪些功能？",
        f"如何更有效地使用你的服务？"
    ]
    return recommended_questions

# def generate_recommended_questions(agent_name: str, category: str = DEFAULT_CATEGORY) -> List[str]:
#     # 根据智能体名称和分类生成推荐问题
#     # 基于分类的推荐问题模板
#     question_templates = {
#         "development": [
#             "如何优化代码性能？",
#             "有哪些常用的设计模式？",
#             f"{agent_name}能帮我解决什么类型的编程问题？"
#         ],
#         "marketing": [
#             "如何提高内容的转化率？",
#             "有哪些有效的社交媒体营销策略？",
#             "怎样分析营销数据以做出决策？"
#         ],
#         "product": [
#             "如何确定产品的优先级？",
#             "有哪些有效的用户调研方法？",
#             "如何规划产品路线图？"
#         ],
#         "education": [
#             "如何提高学习效率？",
#             "有什么好的记忆方法？",
#             "怎样制定有效的学习计划？"
#         ],
#         "culture": [
#             "能推荐一些经典文学作品吗？",
#             "中国传统文化有哪些特点？",
#             "如何欣赏不同类型的艺术？"
#         ],
#         "tools": [
#             "如何提高工作效率？",
#             "有哪些实用的生活小技巧？",
#             "推荐一些日常实用的工具和应用？"
#         ],
#         "writing": [
#             "如何克服写作障碍？",
#             "有哪些提升写作风格的技巧？",
#             "如何写出引人入胜的开头？"
#         ],
#         "job": [
#            "如何准备面试？",
#            "有哪些职业发展建议？",
#            "如何提升职场软技能？"
#         ],
#         "entertainment": [
#             "能推荐一些好看的电影吗？",
#             "有哪些有趣的游戏推荐？",
#             "最近有什么值得关注的娱乐新闻？"
#         ],
#         "normal": [
#             f"{agent_name}能做什么？",
#             "你有哪些功能？",
#             "如何更有效地使用你的服务？"
#         ]
#     }
    
#     # 获取对应分类的推荐问题，如果没有则使用通用问题
#     return question_templates.get(category, question_templates["normal"])
     
def create_agent(agent: AgentBase, user_id: str):
    # 创建agent
    with SessionLocal() as db:
        try:
            agent_data = agent.dict()
            agent_data['id'] = str(uuid.uuid4()).replace("-", "")
            agent_data['user_id'] = user_id  # 添加user_id
            agent_data['create_time'] = datetime.now()
            agent_data['update_time'] = datetime.now()
            
            # 设置默认分类（如果未提供）
            if not agent_data.get('category'):
                agent_data['category'] = json.dumps([DEFAULT_CATEGORY])
            elif isinstance(agent_data['category'], list):
                # 验证分类是否在预设列表中
                agent_data['category'] = json.dumps([cat for cat in agent_data['category'] if cat in AGENT_CATEGORIES])
                if not json.loads(agent_data['category']):  # 如果没有有效分类
                    agent_data['category'] = json.dumps([DEFAULT_CATEGORY])
            else:
                agent_data['category'] = json.dumps([DEFAULT_CATEGORY])
                
            # 设置默认头像（如果未提供）
            if not agent_data.get('avatar'):
                agent_data['avatar'] = DEFAULT_AVATAR
                
            # 设置描述默认值
            agent_data['description'] = agent_data.get('description', '')
            agent_data['plugin_param'] = agent_data.get('plugin_param')
            
            # 只在欢迎语为空时生成
            if not agent_data.get('welcome_message'):
                # agent_data['welcome_message'] = generate_welcome_message(agent.name, agent_data['category'])
                agent_data['welcome_message'] = generate_welcome_message(agent.name)
            
            # 只在推荐问题为空时生成
            if not agent_data.get('recommended_questions'):
                agent_data['recommended_questions'] = generate_recommended_questions(agent.name)
            
            log.info(f"Creating agent with data: name={agent.name}, category={agent_data['category']}")
            
            # 将recommended_questions列表转换为JSON字符串
            if 'recommended_questions' in agent_data and isinstance(agent_data['recommended_questions'], list):
                agent_data['recommended_questions'] = json.dumps(agent_data['recommended_questions'])
            
            new_agent = Agent(**agent_data)
            db.add(new_agent)
            db.commit()
            db.refresh(new_agent)
            
            # 在返回前将recommended_questions从JSON字符串转换回列表
            if new_agent.recommended_questions:
                try:
                    new_agent.recommended_questions = json.loads(new_agent.recommended_questions)
                except json.JSONDecodeError:
                    new_agent.recommended_questions = []
            
            # 在返回前将category从JSON字符串转换回列表
            if new_agent.category:
                try:
                    new_agent.category = json.loads(new_agent.category)
                except json.JSONDecodeError:
                    new_agent.category = [DEFAULT_CATEGORY]
            
            return new_agent
        except Exception as e:
            log.error(f"create_agent error: {e}")
            db.rollback()
            raise e

def update_agent(agent_id: str, update_val: dict, user_id: str):
    # 修改agent
    with SessionLocal() as db:
        try:
            # 验证agent是否存在
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                log.error(f"Agent not found with id: {agent_id}")
                return None
            
            # 获取当前agent的信息以便参考
            current_name = agent.name
            current_category = json.loads(agent.category or '["normal"]')
            
            # 只允许更新特定字段
            allowed_fields = {'name', 'prompt', 'avatar', 'description', 'category', 
                            'welcome_message', 'recommended_questions', 'plugin_param', 'is_favorite'}
            filtered_update = {k: v for k, v in update_val.items() if k in allowed_fields}
            
            if not filtered_update:
                log.error("No valid fields to update")
                return None
            
            # 验证分类是否在预设列表中
            if 'category' in filtered_update:
                if isinstance(filtered_update['category'], list):
                    valid_categories = [cat for cat in filtered_update['category'] if cat in AGENT_CATEGORIES]
                    filtered_update['category'] = json.dumps(valid_categories if valid_categories else [DEFAULT_CATEGORY])
                else:
                    filtered_update['category'] = json.dumps([DEFAULT_CATEGORY])
            
            # 更新名称或分类时，只在欢迎语和推荐问题为空时才重新生成
            name_changed = 'name' in filtered_update and filtered_update['name'] != current_name
            category_changed = 'category' in filtered_update and filtered_update['category'] != current_category
            
            if (name_changed or category_changed):
                new_name = filtered_update.get('name', current_name)
                new_category = filtered_update.get('category', current_category)
                
                # 只在欢迎语为空时生成
                if not agent.welcome_message and 'welcome_message' not in filtered_update:
                    filtered_update['welcome_message'] = generate_welcome_message(new_name, new_category)
                
                # 只在推荐问题为空时生成
                if not agent.recommended_questions and 'recommended_questions' not in filtered_update:
                    filtered_update['recommended_questions'] = generate_recommended_questions(new_name)
                
                log.info(f"Regenerating welcome message and questions for agent_id={agent_id}, name={new_name}, category={new_category}")
            
            # recommended_questions从列表转化为JSON
            if 'recommended_questions' in filtered_update:
                if isinstance(filtered_update['recommended_questions'], list):
                    filtered_update['recommended_questions'] = json.dumps(filtered_update['recommended_questions'])
                elif isinstance(filtered_update['recommended_questions'], str):
                    try:
                        # 如果已经是JSON字符串，验证其有效性
                        json.loads(filtered_update['recommended_questions'])
                    except json.JSONDecodeError:
                        filtered_update['recommended_questions'] = json.dumps([])
                
            # 更新时间
            filtered_update['update_time'] = datetime.now()
            
            db.query(Agent).filter(Agent.id == agent_id).update(filtered_update)
            db.commit()
            
            # 重新转换recommended_questions为列表
            updated_agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if updated_agent and updated_agent.recommended_questions:
                try:
                    updated_agent.recommended_questions = json.loads(updated_agent.recommended_questions)
                except json.JSONDecodeError:
                    updated_agent.recommended_questions = []
            
            # 重新转换category为列表
            if updated_agent and updated_agent.category:
                try:
                    updated_agent.category = json.loads(updated_agent.category)
                except json.JSONDecodeError:
                    updated_agent.category = [DEFAULT_CATEGORY]
            
            return updated_agent
        except Exception as e:
            log.error(f"update_agent error: {e}")
            db.rollback()
            return None
    
def delete_agent(agent_id: str, user_id: str):
    # 删除agent
    with SessionLocal() as db:
        try:
            db.query(Agent).filter(Agent.id == agent_id).delete()
            db.commit()
            return True
        except Exception as e:
            log.error(f"delete_agent error: {e}")
            db.rollback()
            return False

def get_agent_list(user_id: str = None):
    # 获取agent列表
    with SessionLocal() as db:
        try:
            query = db.query(Agent)
            if user_id:
                query = query.filter(Agent.user_id == user_id)
            agents = query.all()
            # 将JSON字符串转换为列表
            for agent in agents:
                # 处理推荐问题
                if agent.recommended_questions:
                    try:
                        agent.recommended_questions = json.loads(agent.recommended_questions)
                    except json.JSONDecodeError:
                        agent.recommended_questions = []
                # 处理分类
                if agent.category:
                    try:
                        agent.category = json.loads(agent.category)
                    except json.JSONDecodeError:
                        agent.category = [DEFAULT_CATEGORY]
            return agents
        except Exception as e:
            log.error(f"get_agent_list error: {e}")
            return None

def get_agent(agent_id: str):
    # 获取agent
    with SessionLocal() as db:
        try:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                # 处理推荐问题
                if agent.recommended_questions:
                    try:
                        agent.recommended_questions = json.loads(agent.recommended_questions)
                    except json.JSONDecodeError:
                        agent.recommended_questions = []
                # 处理分类
                if agent.category:
                    try:
                        agent.category = json.loads(agent.category)
                    except json.JSONDecodeError:
                        agent.category = [DEFAULT_CATEGORY]
            return agent
        except Exception as e:
            log.error(f"get_agent error: {e}")
            return None

# def load_agent_info(session_id: str):
#     # session获取agent信息
#     with SessionLocal() as db:
#         try:
#             # 联合查询Assistants和Agent表
#             result = db.query(Agent, Assistants)\
#                 .join(Assistants, Agent.id == Assistants.agent_id)\
#                 .filter(Assistants.session_id == session_id)\
#                 .first()
#             if result:
#                 agent, assistant = result
#                 # 处理recommended_questions
#                 if agent.recommended_questions:
#                     try:
#                         agent.recommended_questions = json.loads(agent.recommended_questions)
#                     except json.JSONDecodeError:
#                         agent.recommended_questions = []
#                 # 处理recommended_questions
#                 if assistant.recommended_questions:
#                     try:
#                         assistant.recommended_questions = json.loads(assistant.recommended_questions)
#                     except json.JSONDecodeError:
#                         assistant.recommended_questions = []
#                 return {
#                     **agent.__dict__,
#                     'session_info': assistant.__dict__
#                 }
#             return None
#         except Exception as e:
#             log.error(f"load_agent_info error: {e}")
#             return None
        
def set_assistant(agent_id: str, session_id: str):
    # 设置session的agent,生成assistant
    with SessionLocal() as db:
        try:
            # 设置数据库操作超时
            db.execute(text("PRAGMA busy_timeout = 5000"))  # 5秒超时
            
            log.info(f"开始设置助手: agent_id={agent_id}, session_id={session_id}")
            
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                log.error(f"Agent not found with id: {agent_id}")
                return None

            log.info(f"Found agent: {agent.__dict__}")

            # 确保必需字段都有值
            name = agent.name
            if not name:
                log.error(f"Agent name is required but not found for agent_id: {agent_id}")
                return None

            prompt = agent.prompt
            if not prompt:
                log.error(f"Agent prompt is required but not found for agent_id: {agent_id}")
                return None

            welcome_message = agent.welcome_message or ""
            recommended_questions = agent.recommended_questions or "[]"
            
            # 如果recommended_questions是字符串，尝试解析为JSON
            if isinstance(recommended_questions, str):
                try:
                    recommended_questions = json.loads(recommended_questions)
                except json.JSONDecodeError as e:
                    log.warning(f"Failed to parse recommended_questions JSON: {e}")
                    recommended_questions = []

            # 处理分类
            category = agent.category or json.dumps([DEFAULT_CATEGORY])
            if isinstance(category, str):
                try:
                    json.loads(category)  # 验证是否为有效的JSON
                except json.JSONDecodeError as e:
                    log.warning(f"Failed to parse category JSON: {e}")
                    category = json.dumps([DEFAULT_CATEGORY])

            log.info(f"Creating assistant with data: session_id={session_id}, agent_id={agent_id}, name={name}")

            # 创建新的assistant记录
            new_assistant = Assistants(
                agent_id=agent_id,
                session_id=session_id,
                name=name,
                prompt=prompt,
                avatar=agent.avatar or DEFAULT_AVATAR,
                description=agent.description or "",
                category=category,
                kb=agent.kb or "",
                welcome_message=welcome_message,
                recommended_questions=json.dumps(recommended_questions),  # 转换为JSON字符串
                creator_id=agent.creator_id or "system",  # 使用"system"作为默认值
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            
            try:
                db.add(new_assistant)
                db.commit()
                db.refresh(new_assistant)
                log.info(f"Successfully created assistant: {new_assistant.__dict__}")
            except Exception as e:
                log.error(f"Database operation failed: {str(e)}")
                db.rollback()
                return None
            
            # 在返回前将JSON字符串转换回列表
            if new_assistant.recommended_questions:
                try:
                    new_assistant.recommended_questions = json.loads(new_assistant.recommended_questions)
                except json.JSONDecodeError as e:
                    log.warning(f"Failed to parse recommended_questions on return: {e}")
                    new_assistant.recommended_questions = []
            
            # 在返回前将category从JSON字符串转换回列表
            if new_assistant.category:
                try:
                    new_assistant.category = json.loads(new_assistant.category)
                except json.JSONDecodeError as e:
                    log.warning(f"Failed to parse category on return: {e}")
                    new_assistant.category = [DEFAULT_CATEGORY]
            
            return new_assistant
        except Exception as e:
            log.error(f"set_assistant error: {str(e)}")
            log.error(f"Error details: {e.__class__.__name__}")
            db.rollback()
            return None
        
def get_assistant(session_id: str):
    # 获取session的assistant
    with SessionLocal() as db:
        try:
            assistant = db.query(Assistants).filter(Assistants.session_id == session_id).first()
            if assistant:
                # 处理推荐问题
                if assistant.recommended_questions:
                    try:
                        assistant.recommended_questions = json.loads(assistant.recommended_questions)
                    except json.JSONDecodeError:
                        assistant.recommended_questions = []
                # 处理分类
                if assistant.category:
                    try:
                        assistant.category = json.loads(assistant.category)
                    except json.JSONDecodeError:
                        assistant.category = [DEFAULT_CATEGORY]
            return assistant
        except Exception as e:
            log.error(f"get_assistant error: {e}")
            return None

def update_assistant(session_id: str, update_val: dict):
    # 更新session的assistant
    with SessionLocal() as db:
        try:
            assistant = db.query(Assistants).filter(Assistants.session_id == session_id).first()
            if not assistant:
                log.error(f"Assistant not found with session_id: {session_id}")
                return None
            
            # 只允许更新特定字段
            allowed_fields = {'name', 'prompt', 'avatar', 'description', 'category', 
                            'welcome_message', 'recommended_questions', 'plugin_param', 'kb'}
            filtered_update = {k: v for k, v in update_val.items() if k in allowed_fields}
            
            if not filtered_update:
                log.error("No valid fields to update")
                return None
            
            # 处理分类
            if 'category' in filtered_update:
                if isinstance(filtered_update['category'], list):
                    valid_categories = [cat for cat in filtered_update['category'] if cat in AGENT_CATEGORIES]
                    filtered_update['category'] = json.dumps(valid_categories if valid_categories else [DEFAULT_CATEGORY])
                elif isinstance(filtered_update['category'], str):
                    try:
                        # 如果已经是JSON字符串，验证其有效性
                        categories = json.loads(filtered_update['category'])
                        if not isinstance(categories, list):
                            filtered_update['category'] = json.dumps([DEFAULT_CATEGORY])
                    except json.JSONDecodeError:
                        filtered_update['category'] = json.dumps([DEFAULT_CATEGORY])
                else:
                    filtered_update['category'] = json.dumps([DEFAULT_CATEGORY])
            
            # recommended_questions从列表转化为JSON
            if 'recommended_questions' in filtered_update:
                if isinstance(filtered_update['recommended_questions'], list):
                    filtered_update['recommended_questions'] = json.dumps(filtered_update['recommended_questions'])
                elif isinstance(filtered_update['recommended_questions'], str):
                    try:
                        # 如果已经是JSON字符串，验证其有效性
                        json.loads(filtered_update['recommended_questions'])
                    except json.JSONDecodeError:
                        filtered_update['recommended_questions'] = json.dumps([])
                
            # 更新时间
            filtered_update['update_time'] = datetime.now()
            
            db.query(Assistants).filter(Assistants.session_id == session_id).update(filtered_update)
            db.commit()
            
            # 重新获取并转换JSON字符串为列表
            updated_assistant = db.query(Assistants).filter(Assistants.session_id == session_id).first()
            if updated_assistant:
                if updated_assistant.recommended_questions:
                    try:
                        updated_assistant.recommended_questions = json.loads(updated_assistant.recommended_questions)
                    except json.JSONDecodeError:
                        updated_assistant.recommended_questions = []
                
                if updated_assistant.category:
                    try:
                        updated_assistant.category = json.loads(updated_assistant.category)
                    except json.JSONDecodeError:
                        updated_assistant.category = [DEFAULT_CATEGORY]
            
            return updated_assistant
        except Exception as e:
            log.error(f"updated_assistant error: {e}")
            db.rollback()
            return None
    

def is_agent_session(session_id: str) -> bool:
    # 判断会话是否已设置助手
    with SessionLocal() as db:
        try:
            # 查询Assistants表中是否存在该会话的记录
            assistant = db.query(Assistants).filter(Assistants.session_id == session_id).first()
            return assistant is not None
        except Exception as e:
            log.error(f"is_agent_session error: {e}")
            return False

def delete_assistant_by_session(session_id: str):
    # 删除会话助手
    with SessionLocal() as db:
        try:
            # 删除Assistants表中与session_id匹配的记录
            db.query(Assistants).filter(Assistants.session_id == session_id).delete()
            db.commit()
        except Exception as e:
            log.error(f"clean_assistant_by_session error: {e}")
            db.rollback()
            return False
        
def get_assistant_list():
    # 获取所有助手
    with SessionLocal() as db:
        try:
            assistants = db.query(Assistants).all()
            for assistant in assistants:
                # 处理推荐问题
                if assistant.recommended_questions:
                    try:
                        assistant.recommended_questions = json.loads(assistant.recommended_questions)
                    except json.JSONDecodeError:
                        assistant.recommended_questions = []
                # 处理分类
                if assistant.category:
                    try:
                        assistant.category = json.loads(assistant.category)
                    except json.JSONDecodeError:
                        assistant.category = [DEFAULT_CATEGORY]
            return assistants   
        except Exception as e:
            log.error(f"get_assistant_list error: {e}")
            return []

# --------------------other tool---------------------------------------

def agents_init(user_id: str):
    # 初始化默认智能体
    with SessionLocal() as db:
        try:
            default_agents = load_default_agents(user_id)
            for agent in default_agents:
                existing_agent = db.query(Agent).filter(
                    Agent.user_id == user_id, Agent.creator_id == "system", Agent.name == agent['name']
                ).first()
                # 如果智能体不存在，则创建智能体
                if not existing_agent:
                    try:
                        agent_base = AgentBase(**agent)
                        db_create_agent = create_agent(agent=agent_base, user_id=user_id)
                        if db_create_agent:
                            log.info(f"Agent {db_create_agent.name} create SUCCESSFUL.")
                    except Exception as e:
                        log.error(f"Error creating agent {agent['name']}: {str(e)}")
                else:
                    log.info(f"Agent {existing_agent.name} already exists, skipping initialization")
        except Exception as e:
            log.error(f"Error in agents_init for user {user_id}: {str(e)}")

def load_default_agents(user_id: str) -> list:
    # 加载预置智能体
    config_path = Path(__file__).parent.parent / "config" / "default_agents.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            agents = config.get('agents', [])
            # 为每个智能体添加user_id
            for agent in agents:
                agent['user_id'] = user_id
            return agents
    except Exception as e:
        print(f"Error loading default agents: {e}")
        return []

