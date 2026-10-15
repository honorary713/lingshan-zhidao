"""
SQLAlchemy 数据库引擎和会话管理
"""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import DATABASE_URL

# 锁定当前database.py所在的backend文件夹
BASE_DIR = Path(__file__).parent
# 强制数据库生成在backend目录
DB_FILE_PATH = BASE_DIR / "scenic_admin.db"
DATABASE_URL_FIX = f"sqlite:///{DB_FILE_PATH}"

# SQLite 引擎
engine = create_engine(
    DATABASE_URL_FIX,
    connect_args={"check_same_thread": False},
    echo=False
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from models import admin
    from models import conversation
    from models import faq
    from models import scenic
    from models import visitor
    Base.metadata.create_all(bind=engine)
    print(f"[文件生成校验] 数据库路径：{DB_FILE_PATH}")