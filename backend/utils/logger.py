"""
日志系统 - 记录应用运行日志
"""
import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

# 项目根目录 = 本文件(backend/utils/logger.py) 往上退2层
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_LOG_DIR = os.path.join(_PROJECT_ROOT, "data", "logs")

def setup_logger(
    name: str = "interview_coach",
    log_dir: str = "data/logs",
    level: int = logging.INFO
) -> logging.Logger:
    """配置日志记录器"""
    
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 文件handler（自动轮转，最大10MB，保留5个备份）
    log_file = os.path.join(log_dir, f"{name}.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # 控制台只显示警告以上
    console_handler.setFormatter(formatter)
    
    # 添加handler
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 全局logger实例
logger = setup_logger()


def log_api_call(method: str, path: str, status_code: int, duration: float):
    """记录API调用日志"""
    logger.info(f"API {method} {path} -> {status_code} ({duration:.3f}s)")


def log_agent_call(agent_name: str, action: str, success: bool, duration: float):
    """记录Agent调用日志"""
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"Agent [{agent_name}] {action} -> {status} ({duration:.3f}s)")


def log_error(error: Exception, context: str = ""):
    """记录错误日志"""
    logger.error(f"{context}: {type(error).__name__}: {error}", exc_info=True)


def log_interview_event(interview_id: str, event: str, details: str = ""):
    """记录面试事件日志"""
    logger.info(f"Interview [{interview_id}] {event} {details}")
