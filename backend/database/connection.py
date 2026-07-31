from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

from ..config import DATABASE_URL, DATABASE_DIR

# 确保数据目录存在
os.makedirs(DATABASE_DIR, exist_ok=True)

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite多线程支持
    echo=False
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 模型基类
Base = declarative_base()

def get_db():
    """获取数据库会话（依赖注入用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库（创建所有表）"""
    Base.metadata.create_all(bind=engine)
    _migrate_add_session_expiry()


def _migrate_add_session_expiry():
    """
    轻量迁移：给已存在的 user_sessions 表补上 expires_at 列。

    背景：项目没有引入 Alembic 之类的迁移工具，create_all() 只会创建
    不存在的表，不会给已存在的表加新列。早期开发库里可能已经有
    user_sessions 表（没有过期时间字段），加上"令牌过期"逻辑后如果不补
    这一列，SQLAlchemy 插入/查询 expires_at 时会报错。

    做法：尝试 ALTER TABLE 加列，如果列已存在（重复迁移 / 全新库）则
    忽略这个报错即可，不影响启动。
    """
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE user_sessions ADD COLUMN expires_at DATETIME"))
            conn.commit()
    except Exception:
        # 列已存在（正常情况）或数据库方言不支持该写法，静默跳过
        pass
