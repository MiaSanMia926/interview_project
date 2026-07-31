"""
通用Schema - 包含CamelModel基类
"""
from pydantic import BaseModel, Field
from typing import List, Any, Optional
from datetime import datetime
import json


def to_camel(string: str) -> str:
    """将snake_case转为camelCase"""
    parts = string.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


class CamelModel(BaseModel):
    """支持camelCase的基类"""
    
    class Config:
        alias_generator = to_camel
        populate_by_name = True  # 允许使用原始snake_case


class HealthResponse(CamelModel):
    """健康检查响应"""
    status: str
    version: str
    has_gemini_key: bool = Field(default=False, alias="hasGeminiKey")
    has_deepseek_key: bool = Field(default=False, alias="hasDeepseekKey")


class PaginatedResponse(CamelModel):
    """分页响应"""
    total: int
    page: int
    size: int
    items: List[Any]


class ErrorResponse(CamelModel):
    """错误响应"""
    detail: str
