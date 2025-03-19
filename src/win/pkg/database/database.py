from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..projectvar import constants as const
from ..projectvar import Projectvar

gvar = Projectvar()
SQLALCHEMY_DATABASE_URL = const.DB_SQLITE_PREFIX + gvar.get_db_filename() + "?charset=utf8mb4"

print("db url = ", SQLALCHEMY_DATABASE_URL)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()