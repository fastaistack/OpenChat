from .database import SessionLocal, engine
from . import models
from ..logger import Log


log = Log()

def init_database():
    models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()