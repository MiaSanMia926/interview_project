import os
from dotenv import load_dotenv

load_dotenv()

# 数据库配置
DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATABASE_URL = f"sqlite:///{DATABASE_DIR}/interview.db"

# MiMo配置（供Agent模块使用）—— 必须在 .env 里配置，不再提供硬编码默认值
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", os.getenv("MIMO_API_KEY"))
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", os.getenv("MIMO_API_BASE", "https://api.mimo.xiaomi.com/v1"))
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", os.getenv("MIMO_MODEL", "mimo-v2.5-pro"))

if not DEEPSEEK_API_KEY:
    import warnings
    warnings.warn(
        "未找到 DEEPSEEK_API_KEY / MIMO_API_KEY，AI 功能将不可用。"
        "请在项目根目录复制 .env.example 为 .env 并配置 API Key。",
        RuntimeWarning,
        stacklevel=2,
    )

# 兼容旧代码
MIMO_API_KEY = DEEPSEEK_API_KEY
MIMO_API_BASE = DEEPSEEK_BASE_URL
MIMO_MODEL = DEEPSEEK_MODEL

# 应用配置
APP_NAME = "面试突破助手"
APP_VERSION = "1.0.0"
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# 数据库配置（dev/prod 可不同）
if APP_ENV == "production":
    DEBUG = False
    LOG_LEVEL = "WARNING"
    # 生产环境优先从环境变量读数据库 URL，支持 PostgreSQL 等远程数据库
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_DIR}/interview.db")
elif APP_ENV == "testing":
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    DATABASE_URL = f"sqlite:///{DATABASE_DIR}/test.db"
else:
    LOG_LEVEL = "DEBUG"
    DATABASE_URL = f"sqlite:///{DATABASE_DIR}/interview.db"

# 面试配置 —— 每次面试 3 道题（对应前端 InterviewView 题目进度卡的固定渲染逻辑）
MAX_QUESTIONS = 3
MAX_FOLLOWUPS = 1
SCORE_THRESHOLD_FOR_FOLLOWUP = 55
