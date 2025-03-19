from ...logger import Log

from sqlalchemy import or_, and_, func
from sqlalchemy.exc import SQLAlchemyError
from pkg.database import models, schemas
from pkg.database.database import SessionLocal
from ...database.schemas import *
from ...database.models import *

from datetime import datetime, timedelta
import uuid
# hash
from passlib.context import CryptContext
# token
from jose import JWTError, jwt

# 创建密钥变量
# to get a string like this run:
# openssl rand -hex 32
# 生成一个随机的密钥，用于对JWT令牌进行签名
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
# 创建用于设定JWT令牌签名算法的变量
ALGORITHM = "HS256"
# 创建设置令牌过期时间变量（单位：分钟）
#ACCESS_TOKEN_EXPIRE_MINUTES = 30
ACCESS_TOKEN_EXPIRE_MINUTES = 150000

class AlchemyTool(object):
    def __init__(self):
        # print("AlchemyTool init")

        # self._session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
        self._session = SessionLocal()
        self._log = Log()

        # 创建对象，进行哈希和校验密码
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

     ############################### User ###############################
    def test(self, role_name: str = "owner"):
        pass
        # print("AlchemyTool.create")

    def init_database(self):
        role_root = "root"
        role_admin = "admin"
        role_owner = "owner"
        if not self.select_role_by_name(role_root):
            db_location = self.create_role(RoleBase(role_name=role_root, description="超级管理员"))
            # if db_location:
            #     self._log.error("init_database create_role", role_root, db_location.__dict__)
            
            db_root = self.select_role_by_name(role_root)
            if db_root:
                db_location = self.create_role(RoleBase(role_name=role_admin, description="管理员", parent_id=db_root.role_id))
                # print("init_database create_role", role_admin, db_location)
            
            db_admin = self.select_role_by_name(role_admin)
            if db_admin:
                db_location = self.create_role(RoleBase(role_name=role_owner, description="拥有者", parent_id=db_admin.role_id))
                # print("init_database create_role", role_owner, db_location)

        user_name = "hello"
        if not self.select_user_by_name(user_name):
            root_id = "system init"
            user_base = UserBase(**{"user_name":"hello", "password": "hello", "salt": "hello", "mobile": "18777778888"})
            db_location = self.create_user(user_base, root_id, role_root)
            # print("init_database create_user hello", db_location)
            
            user_base = UserBase(**{"user_name":"world", "password": "world", "salt": "hello", "mobile": "18777778888"})
            db_location = self.create_user(user_base, root_id, role_admin)
            # print("init_database create_user world", db_location)

            user_base = UserBase(**{"user_name":"local", "password": "local", "salt": "local", "mobile": "18700000000"})
            db_location = self.create_user(user_base, root_id, role_admin)
            # print("init_database create_user world", db_location)

    def init_permissions(self, data):
        # self._log.error(f"file exist type:{type(data)} data:{data}")
        for item in  data:
            role_name = item["role_name"]
            perm_uri = item["perm_uri"]
            perm_name = item["perm_name"]
            db_perm = self.create_perm(PermBase(perm_uri=perm_uri, perm_name=perm_name))
            db_query = self.select_role_by_name(role_name)
            role_id = None
            if db_query:
                role_id = db_query.role_id
            # print(f"init_permissions exit role_name:{role_name} role_id:{role_id} perm_uri:{perm_uri} perm_name:{perm_name}")

            if db_perm.perm_id and role_id:
                self.create_role_perm(RolePermBase(role_id=role_id, perm_id=db_perm.perm_id))

    # 哈希密码：hash(password)
    def hash_password(self, password: str):
        """
        哈希来自用户的密码
        :param password: 原密码
        :return: 哈希后的密码
        """
        return self._pwd_context.hash(password)
    
    # 校验密码：verify(plain_password, hash_password)
    def verify_password(self, plain_password: str, hash_password: str):
        """
        校验接收的密码是否与存储的哈希值匹配
        :param plain_password: 原密码
        :param hash_password: 哈希后的密码
        :return: 返回值为bool类型，校验成功返回True,反之False
        """
        return self._pwd_context.verify(plain_password, hash_password)

    def generate_access_token(self, user_name: str) -> Optional[str]:
        try:
            # 计算token
            # 计算token过期时间
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            payload = {"sub": user_name, 
                        "exp": expire}
            """
            :param data: 需要进行JWT令牌加密的数据（解密的时候会用到）
            :param expires_delta: 令牌有效期
            :return: token
            """
            # SECRET_KEY：密钥
            # ALGORITHM：JWT令牌签名算法
            encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            return 0, encoded_jwt
        except jwt.JWTClaimsError as err:
            return 1, str(err)
        except jwt.ExpiredSignatureError as err:
            return 2, str(err)
        except JWTError as err:
            return 3, str(err)
        return 9, ""
    
    # 验证 access token
    def check_access_token(self, token: str):
        token = token[7:]
        # print(f"AlchemyTool,check_access_token token:{token}")
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # print(f"AlchemyTool.check_access_token payload:{payload}")
            user_name: str = payload.get("sub")
            if user_name is None:
                self._log.error(f"AlchemyTool.check_access_token user_name Error")
                return 4, "user_name Error"
            token_data = TokenBase(access_token=token, user_name=user_name)
            return 0, token_data
        except jwt.JWTClaimsError as err:
            return 1, str(err)
        except jwt.ExpiredSignatureError as err:
            return 2, str(err)
        except JWTError as err:
            return 3, str(err)
        return 9,""

    def generate_refresh_token(self, user_name: str):
        try:
            payload = {"user_name": user_name,
                        "sub": "refresh"}
            encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
            return 0, encoded_jwt
        except JWTError as err:
            return 3, str(err)
        return 9, ""

    # 验证i refresh token
    def check_refresh_token(self, token: str):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # print(f"AlchemyTool.check_refresh_token payload:{payload}")
            if payload["sub"] != "refresh":
                return 4, "not refresh"
            
            user_name = payload["user_name"]
            access_token = self.generate_access_token(user_name)
            return 0, access_token 
        except jwt.JWTClaimsError as err:
            return 1, str(err)
        except jwt.ExpiredSignatureError as err:
            return 2, str(err)
        except JWTError as err:
            return 3, str(err)
        return 9,""

    ############################### User ###############################
    def create_user(self, user_base: UserBase, creator : str, role_name: str = "owner"):
        # 如果用户已经存在 则禁止创建
        db_query = self.select_user_by_name(user_base.user_name)
        if db_query:
            # print(f"Error.AlchemyTool.create_user user_name:{user_base.user_name} is exist")
            return None

        # 默认使用拥有者角色
        db_role = self.select_role_by_name(role_name)
        if not db_role:
            # print(f"Error.AlchemyTool.create_user role_name:{role_name} is not exist")
            return None

        try:
            user_id = str(uuid.uuid4().hex)
            #create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #print("AlchemyTool.create_user create_time:", create_time)
            #edite_time = create_time
            user_base.password = self.hash_password(user_base.password)

            db_location = TUsers(**user_base.dict(), user_id=user_id, creator=creator, editor=creator)
            self._session.add(db_location)
            self._session.commit()
        except SQLAlchemyError as e:
            # print(f"Error.AlchemyTool.create_user SQLAlchemyError:{str(e)}")
            self._session.rollback()
            db_location = None
        finally:
            #self._session.refresh(db_location)
            pass
                
        if db_location:
            # 为用户添加角色
            self.create_user_role(UserRoleBase(user_id=user_id, role_id=db_role.role_id))
        # 返回 TUsers join TRoles
        return self.select_user_join_role(user_base.user_name)

    def delete_user(self, user_id: str):
        try:
            db_query = self._session.query(TUsers).get(user_id)
            if db_query:
                self._session.delete(db_query)
                self._session.commit()

                # 同时删除 用户角色关系表
                self.delete_user_role_by_user_id(user_id)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.delete_user SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query 

    def select_user_by_name(self, user_name: str):
        try:
            db_query = self._session.query(TUsers).filter(TUsers.user_name==user_name).first()    
            #if db_query:
            #    print("AlchemyTool.select_user_by_name", user_name, db_query.__dict__)
            #else:
            #    print("AlchemyTool.select_user_by_name not exist", user_name, db_query)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.select_user_by_name SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query 

    def select_user_by_id(self, user_id: str):
        try:
            db_query = self._session.query(TUsers).filter(TUsers.user_id==user_id).first()    
            #if db_query:
            #    print("AlchemyTool.select_user_by_id", user_id, db_query.__dict__)
            #else:
            #    print("AlchemyTool.select_user_by_id not exist", user_id, db_query)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.select_user_by_id SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query 

    def select_user_join_role(self, user_name: str):
        try:
            db_query = self._session.query(TUsers, TUserRoles.id, TRoles).join(TUserRoles, TUsers.user_id==TUserRoles.user_id).join(TRoles, TUserRoles.role_id==TRoles.role_id).filter(TUsers.user_name==user_name).first()
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.select_user_join_role SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query

    def select_user_outerjoin_roles(self, page_param: PageParamBase):
        # print("select_role_outjoin_perms", page_param)
        total = 0
        try:
            # db_query = self._session.query(TUsers, TUserRoles.id, TRoles).outerjoin(TUserRoles, TUsers.user_id==TUserRoles.user_id).outerjoin(TRoles, TUserRoles.role_id==TRoles.role_id).all()

            total = self._session.query(TUsers, TUserRoles.id, TRoles).outerjoin(TUserRoles, TUsers.user_id==TUserRoles.user_id).outerjoin(TRoles, TUserRoles.role_id==TRoles.role_id).with_entities(func.count(TUsers.user_id)).scalar()

            db_query = self._session.query(TUsers, TUserRoles.id, TRoles).outerjoin(TUserRoles, TUsers.user_id==TUserRoles.user_id).outerjoin(TRoles, TUserRoles.role_id==TRoles.role_id).slice(page_param.page_start, page_param.page_end)
            # db_query = self._session.query(TUsers, TUserRoles.id, TRoles).outerjoin(TUserRoles, TUsers.user_id==TUserRoles.user_id).outerjoin(TRoles, TUserRoles.role_id==TRoles.role_id).slice((page_param.page-1)*page_param.pagesize, page_param.page*page_param.pagesize)
            # db_query = self._session.query(TUsers, TUserRoles.id, TRoles).outerjoin(TUserRoles, TUsers.user_id==TUserRoles.user_id).outerjoin(TRoles, TUserRoles.role_id==TRoles.role_id).limit(page_param.pagesize).offset((page_param.page-1)*page_param.pagesize)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.select_user_outerjoin_roles SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return total, db_query


    ############################## UserRole ############################
    def create_user_role(self, user_role_base: UserRoleBase):
        # 如果用户或者角色不存在  禁止创建关系
        db_user = self.select_user_by_id(user_role_base.user_id)
        db_role = self.select_role_by_id(user_role_base.role_id)
        if not db_user or not db_role:
            self._log.error(f"Error.AlchemyTool.create_user_role user:{db_user} or role:{db_role} no exit")
            return None

        # 如果关系已经存在 禁止重新创建
        db_query = self._session.query(TUserRoles).filter(and_(TUserRoles.user_id==user_role_base.user_id, TUserRoles.role_id==user_role_base.role_id)).all()
        if db_query:
            self._log.error(f"Error.AlchemyTool.create_user_role user_id:{user_role_base.user_id} role_id:{user_role_base.role_id} exist")
            return None

        try:
            user_role_id = str(uuid.uuid4().hex)
            db_location = TUserRoles(**user_role_base.dict(), id=user_role_id)
            #print("AlchemyTool.create_user_role", db_location.__dict__)
            self._session.add(db_location)
            self._session.commit()
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.create_user_role SQLAlchemyError: [[{str(e)}]]")
            self._session.rollback()
            db_location = None
        finally:
            #self._session.refresh(db_location)
            #print("AlchemyTool.create_user_role")
            pass
        return db_location 

    ## 重置
    #def reset_user_role(self, user_role_base: UserRoleBase):
    #    db_location = None
    #    try:
    #        db_query = self._session.query(TUserRoles).filter(TUserRoles.user_id==user_role_base.user_id).all()    
    #        print(f"AlchemyTool.reset_user_role", db_query)
    #        if db_query:
    #            for db_orm in db_query:
    #                print(f"AlchemyTool.reset_user_role user_id:{user_role_base.user_id} delete old role", db_orm.__dict__)
    #                self._session.delete(db_orm)
    #            self._session.commit()
    #        else:
    #            print(f"AlchemyTool.reset_user_role user_id:{user_role_base.user_id} no role")

    #        # 不可用 get 只能根据id返回
    #        #db_query = self._session.query(TUserRoles).get(user_role_base.user_id)
    #        #print(f"AlchemyTool.reset_user_role", db_query)
    #        #if db_query:
    #        #    self._session.delete(db_query)
    #        #    self._session.commit()

    #        db_location = self.create_user_role(user_role_base)
    #    except SQLAlchemyError as e:
    #        print("AlchemyTool.reset_user_role SQLAlchemyError", str(e))
    #    finally:
    #        pass
    #    return db_location

    def delete_user_role(self, user_role_id: str):
        try:
            # 不可用 get 只能根据id返回
            db_query = self._session.query(TUserRoles).get(user_role_id)
            if db_query:
                self._session.delete(db_query)
                self._session.commit()
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.delete_user_role user_role_id:{user_role_id} SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query 

    def delete_user_role_by_user_id(self, user_id: str):
        try:
            db_query = self._session.query(TUserRoles).get(user_id)
            if db_query:
                self._session.delete(db_query)
                self._session.commit()
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.delete_user_role_by_user_id user_id:{user_id} SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query 

    def delete_user_role_by_role_id(self, role_id: str):
        try:
            db_query = self._session.query(TUserRoles).get(role_id)
            if db_query:
                self._session.delete(db_query)
                self._session.commit()
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.delete_user_role_by_role_id role_id:{role_id} SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query 

    def select_user_roles(self, page_param: PageParamBase):
        total = 0
        try:
            total = self._session.query(TUserRoles, TUsers, TRoles).outerjoin(TUsers, TUserRoles.user_id==TUsers.user_id).outerjoin(TRoles, TUserRoles.role_id==TRoles.role_id).with_entities(func.count(TUserRoles.id)).scalar()

            #db_list = self._session.query(TUserRoles).all()
            # db_query = self._session.query(TUserRoles, TUsers, TRoles).outerjoin(TUsers, TUserRoles.user_id==TUsers.user_id).outerjoin(TRoles, TUserRoles.role_id==TRoles.role_id).all()

            db_query = self._session.query(TUserRoles, TUsers, TRoles).outerjoin(TUsers, TUserRoles.user_id==TUsers.user_id).outerjoin(TRoles, TUserRoles.role_id==TRoles.role_id).slice(page_param.page_start, page_param.page_end)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.select_user_roles SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return total, db_query 

    ############################### Role ###############################
    def create_role(self, role_base: RoleBase):
        # 如果角色已经存在 禁止创建
        db_query = self.select_role_by_name(role_base.role_name)
        if db_query:
            self._log.error(f"Error.AlchemyTool.create_role role_name:{role_base.role_name} is exist")
            return None

        try:
            role_id = str(uuid.uuid4().hex)
            db_location = TRoles(**role_base.dict(), role_id=role_id)
            self._session.add(db_location)
            self._session.commit()
            #print("AlchemyTool.create_role ", db_location.__dict__)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.create_role SQLAlchemyError:{str(e)}")
            self._session.rollback()
            db_location = None
        finally:
            #self._session.refresh(db_location)
            #print("AlchemyTool.create_role")
            pass
        return db_location

    def delete_role(self, role_id: str):
        try:
            db_query = self._session.query(TRoles).get(role_id)
            if db_query:
                self._session.delete(db_query)
                self._session.commit()

                # 同时删除用户角色关系表
                self.delete_user_role_by_role_id(role_id)

                # 同时删除角色权限关系表
                self.delete_role_perm_by_role_id(role_id)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.delete_role SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query 

    def select_roles(self, page_param: PageParamBase):
        total = 0
        try:
            total = self._session.query(TRoles).with_entities(func.count(TRoles.role_id)).scalar()

            # db_query = self._session.query(TRoles).all()
            db_query = self._session.query(TRoles).slice(page_param.page_start, page_param.page_end)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.select_roles SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return total, db_query

    # def select_role_outjoin_perms(self, page_param: PageParamBase):
    #     total = 0
    #     try:
    #         total = self._session.query(TRoles, TRolePerms.id, TPerms).outerjoin(TRolePerms, TRoles.role_id==TRolePerms.role_id).outerjoin(TPerms, TRolePerms.perm_id==TPerms.perm_id).with_entities(func.count(TRoles.role_id)).scalar()

    #         # db_query = self._session.query(TRoles, TRolePerms.id, TPerms).outerjoin(TRolePerms, TRoles.role_id==TRolePerms.role_id).outerjoin(TPerms, TRolePerms.perm_id==TPerms.perm_id).all()
    #         db_query = self._session.query(TRoles, TRolePerms.id, TPerms).outerjoin(TRolePerms, TRoles.role_id==TRolePerms.role_id).outerjoin(TPerms, TRolePerms.perm_id==TPerms.perm_id).slice(page_param.page_start, page_param.page_end)
    #     except SQLAlchemyError as e:
    #         self._log.error(f"Error.AlchemyTool.select_roles SQLAlchemyError:{str(e)}")
    #         db_query = None
    #     finally:
    #         pass
    #     return total, db_query


    def select_role_by_name(self, role_name = "owner"):
        try:
            db_query = self._session.query(TRoles).filter(TRoles.role_name==role_name).first()    
            #if db_query:
            #    print("AlchemyTool.select_role_by_name", role_name, db_query.__dict__)
            #else:
            #    print("AlchemyTool.select_role_by_name not exist", role_name, db_query)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.select_role_by_name SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query

    def select_role_by_id(self, role_id):
        try:
            db_query = self._session.query(TRoles).filter(TRoles.role_id==role_id).first()    
            #if db_query:
            #    print("AlchemyTool.select_role_by_id", role_id, db_query.__dict__)
            #else:
            #    print("AlchemyTool.select_role_by_id not exist", role_id, db_query)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.select_role_by_id SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query

    def select_role_join_perm(self, role_id):
        try:
            db_query = self._session.query(TRoles, TRolePerms.id, TPerms).join(TRolePerms, TRoles.role_id==TRolePerms.role_id).join(TPerms, TRolePerms.perm_id==TPerms.perm_id).filter(TRoles.role_id==role_id).all()
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.select_role_join_perm SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query


    ############################### Perm ###############################
    def create_perm(self, perm_base: PermBase):
        # 如果权限已经存在 禁止创建
        db_query = self.select_perm_by_uri(perm_base.perm_uri)
        if db_query:
            # self._log.error(f"Error.AlchemyTool.create_perm perm_uri:{perm_base.perm_uri} is exist")
            return db_query

        try:
            perm_id = str(uuid.uuid4().hex)
            db_location = TPerms(**perm_base.dict(), perm_id=perm_id)
            self._session.add(db_location)
            self._session.commit()
            #print("AlchemyTool.create_perm ", db_location.__dict__)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.create_perm SQLAlchemyError:{str(e)}")
            self._session.rollback()
            db_location = None
        finally:
            #self._session.refresh(db_location)
            #print("AlchemyTool.create_perm")
            pass
        return db_location

    def update_perm(self, perm_indb: PermInDB):
        try:
            db_query = self._session.query(TPerms).get(perm_indb.perm_id)
            if db_query:
                db_query.perm_name = perm_indb.perm_name
                db_query.perm_uri = perm_indb.perm_uri
                db_query.parent_id = perm_indb.parent_id
                self._session.commit()
            else:
                self._log.error(f"Error.AlchemyTool.update_perm perm_uri:{perm_indb.perm_uri} is not exist")
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.update_perm SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            #self._session.refresh(db_location)
            #print("AlchemyTool.update_perm")
            pass
        return db_query 

    def delete_perm(self, perm_id: str):
        try:
            db_query = self._session.query(TPerms).get(perm_id)
            if db_query:
                self._session.delete(db_query)
                self._session.commit()

                # 同时删除角色权限表
                self.delete_role_perm_by_perm_id(perm_id)
            else:
                self._log.error(f"Error.AlchemyTool.delete_perm perm_id:{perm_id} is no not exist")
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.delete_perm SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query 

    def select_perm_by_uri(self, perm_uri: str):
        try:
            db_query = self._session.query(TPerms).filter(TPerms.perm_uri==perm_uri).first()    
            #if db_query:
            #    print("AlchemyTool.select_perm_by_uri", perm_name, db_query.__dict__)
            #else:
            #    print("AlchemyTool.select_perm_by_uri not exist", perm_name, db_query)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.select_perm_by_uri perm_uri:{perm_uri} SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query

    def select_perm_by_id(self, perm_id: str):
        try:
            db_query = self._session.query(TPerms).filter(TPerms.perm_id==perm_id).first()    
            #if db_query:
            #    print("AlchemyTool.select_perm_by_id", perm_name, db_query.__dict__)
            #else:
            #    print("AlchemyTool.select_perm_by_id not exist", perm_name, db_query)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.select_perm_by_id perm_id:{perm_id} SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query

    def select_perms(self, page_param: PageParamBase):
        total = 0
        try:
            total = self._session.query(TPerms).with_entities(func.count(TPerms.perm_id)).scalar()

            # db_query = self._session.query(TPerms).all()
            db_query = self._session.query(TPerms).slice(page_param.page_start, page_param.page_end)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.select_perms SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return total, db_query

    ############################## RolePerm ############################
    def create_role_perm(self, role_perm_base: RolePermBase):
        # 如果角色或者权限不存在  禁止创建关系
        db_role = self.select_role_by_id(role_perm_base.role_id)
        db_perm = self.select_perm_by_id(role_perm_base.perm_id)
        if not db_role or not db_perm:
            self._log.error(f"Error.AlchemyTool.create_role_perm role:{db_role} or perm:{db_perm} no exit")
            return None

        # 如果关系已经存在 禁止重新创建
        db_query = self._session.query(TRolePerms).filter(and_(TRolePerms.role_id==role_perm_base.role_id, TRolePerms.perm_id==role_perm_base.perm_id)).all()
        if db_query:
            # self._log.error(f"Error.AlchemyTool.create_role_perm role_id:{role_perm_base.role_id} perm_id:{role_perm_base.perm_id} exist")
            return None

        try:
            role_perm_id = str(uuid.uuid4().hex)
            db_location = TRolePerms(**role_perm_base.dict(), id=role_perm_id)
            #print("AlchemyTool.create_role_perm", db_location.__dict__)
            self._session.add(db_location)
            self._session.commit()
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.create_role_perm SQLAlchemyError: [[{str(e)}]]")
            self._session.rollback()
            db_location = None
        finally:
            #self._session.refresh(db_location)
            #print("AlchemyTool.create_role_perm")
            pass
        return db_location 

    def delete_role_perm(self, role_perm_id: str):
        try:
            db_query = self._session.query(TRolePerms).get(role_perm_id)
            if db_query:
                self._session.delete(db_query)
                self._session.commit()
            else:
                self._log.error(f"Error.AlchemyTool.delete_role_perm role_perm_id:{role_perm_id} is not exist")
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.delete_role_perm SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query 

    def delete_role_perm_by_perm_id(self, perm_id: str):
        try:
            db_query = self._session.query(TRolePerms).get(perm_id)
            if db_query:
                self._session.delete(db_query)
                self._session.commit()
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.delete_role_perm_by_perm_id perm_id:{perm_id} SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query 

    def delete_role_perm_by_role_id(self, role_id: str):
        try:
            db_query = self._session.query(TRolePerms).get(role_id)
            if db_query:
                self._session.delete(db_query)
                self._session.commit()
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.delete_role_perm_by_role_id role_id:{role_id} SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return db_query 

    def select_role_perms(self, page_param: PageParamBase):
        total = 0
        try:
            total = self._session.query(TRolePerms, TRoles, TPerms).join(TRoles, TRolePerms.role_id==TRoles.role_id).join(TPerms, TRolePerms.perm_id==TPerms.perm_id).with_entities(func.count(TRolePerms.id)).scalar()

            # db_query = self._session.query(TRolePerms, TRoles, TPerms).join(TRoles, TRolePerms.role_id==TRoles.role_id).join(TPerms, TRolePerms.perm_id==TPerms.perm_id).all()
            db_query = self._session.query(TRolePerms, TRoles, TPerms).join(TRoles, TRolePerms.role_id==TRoles.role_id).join(TPerms, TRolePerms.perm_id==TPerms.perm_id).slice(page_param.page_start, page_param.page_end)
        except SQLAlchemyError as e:
            self._log.error(f"Error.AlchemyTool.select_role_perms SQLAlchemyError:{str(e)}")
            db_query = None
        finally:
            pass
        return total, db_query


    def access_perm(self, role_id: str, role_name: str, path: str):
        # db_query = self.select_user_join_role(user_name)
        #print(f"AlchemyTool.access_perm user_name:{user_name}", db_query[0].__dict__)
        ##print(f"AlchemyTool.access_perm user_name:{user_name}", db_query[1].__dict__)
        #print(f"AlchemyTool.access_perm user_name:{user_name}", db_query[2].__dict__)

        if role_name == "root":
            return True

        if role_name == "admin":
           return True

        # if db_query[2]:
        #     role_id = db_query[2].role_id
        #     db_query_role = self.select_role_join_perm(role_id)

        #     for db_list in db_query_role:
        #         #print(f"AlchemyTool.access_perm role_id:{role_id}", db_list[0].__dict__)
        #         #print(f"AlchemyTool.access_perm role_id:{role_id}", db_list[1].__dict__)
        #         print(f"AlchemyTool.access_perm role_id:{role_id}", db_list[2].__dict__)
        #         if db_list[2].perm_uri == path:
        #             return True
        # return False


        db_query_role = self.select_role_join_perm(role_id)
        for db_list in db_query_role:
            # print(f"AlchemyTool.access_perm role_id:{role_id}", db_list[0].__dict__)
            # print(f"AlchemyTool.access_perm role_id:{role_id}", db_list[1])
            # print(f"AlchemyTool.access_perm role_id:{role_id}", db_list[2].__dict__)
            if db_list[2].perm_uri == path:
                return True
        return False
