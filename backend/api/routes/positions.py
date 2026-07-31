"""
职位推荐接口
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List

router = APIRouter(prefix="/api/positions", tags=["positions"])


class SuggestPositionsRequest(BaseModel):
    """职位推荐请求"""
    target_company: str = Field(..., alias="targetCompany")

    class Config:
        populate_by_name = True


class SuggestPositionsResponse(BaseModel):
    """职位推荐响应"""
    positions: List[str]


# 静态职位列表（可根据公司类型扩展）
POSITIONS_DB = {
    "字节跳动": ["后端工程师", "前端工程师", "算法工程师", "数据工程师", "产品经理"],
    "阿里巴巴": ["Java开发工程师", "前端开发工程师", "算法工程师", "数据分析师", "产品经理"],
    "腾讯": ["后台开发工程师", "前端开发工程师", "游戏开发工程师", "数据工程师", "产品经理"],
    "百度": ["C++开发工程师", "Java开发工程师", "算法工程师", "数据挖掘工程师", "产品经理"],
    "美团": ["后端开发工程师", "前端开发工程师", "算法工程师", "数据分析师", "产品经理"],
    "default": ["软件工程师", "前端工程师", "后端工程师", "算法工程师", "数据工程师", "产品经理"]
}


@router.post("/suggest", response_model=SuggestPositionsResponse)
async def suggest_positions(request: SuggestPositionsRequest):
    """根据目标公司推荐职位列表"""
    positions = POSITIONS_DB.get(request.target_company, POSITIONS_DB["default"])
    return SuggestPositionsResponse(positions=positions)
