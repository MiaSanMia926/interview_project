"""
用户相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

from .common import CamelModel


class UserCreate(CamelModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")


class UserResponse(CamelModel):
    """用户响应"""
    id: str
    username: str
    created_at: datetime = Field(alias="createdAt")
    
    class Config:
        from_attributes = True


class RadarDataItem(CamelModel):
    """雷达图数据项"""
    name: str
    score: float
    full_mark: float = Field(alias="fullMark")


class CategoryDataItem(CamelModel):
    """分类数据项"""
    category: str
    score: float


class TrendDataItem(CamelModel):
    """趋势数据项"""
    date: str
    score: float
    title: str


class KnowledgeNode(CamelModel):
    """知识图谱节点"""
    id: str
    label: str
    group: str  # core/sub/weak


class KnowledgeLink(CamelModel):
    """知识图谱连线"""
    source: str
    target: str
    label: Optional[str] = None


class KnowledgeGraph(CamelModel):
    """知识图谱"""
    nodes: List[KnowledgeNode]
    links: List[KnowledgeLink]


class ChallengeItem(CamelModel):
    """打卡挑战项"""
    id: int
    text: str
    priority: str = "medium"  # high / medium / low


class UserProfile(CamelModel):
    """用户画像"""
    user_id: str = Field(alias="userId")
    username: str
    total_interviews: int = Field(alias="totalInterviews")
    average_score: float = Field(alias="averageScore")
    radar_data: List[RadarDataItem] = Field(alias="radarData")
    category_data: List[CategoryDataItem] = Field(alias="categoryData")
    trend_data: List[TrendDataItem] = Field(alias="trendData")
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    challenges: List[ChallengeItem] = []
    knowledge_graph: KnowledgeGraph = Field(alias="knowledgeGraph")

class RegisterRequest(CamelModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码，至少6位")


class LoginRequest(CamelModel):
    """登录请求"""
    username: str
    password: str


class AuthResponse(CamelModel):
    """注册/登录成功响应"""
    token: str
    user_id: str = Field(alias="userId")
    username: str