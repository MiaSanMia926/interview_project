"""
健康检查接口
"""
from fastapi import APIRouter
from datetime import datetime
import os

from ...schemas.common import HealthResponse
from ...config import APP_VERSION

router = APIRouter()


def check_api_keys():
    """检查API Key配置（兼容 DEEPSEEK_* 和 MIMO_* 两组变量名）"""
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_deepseek = bool(os.getenv("DEEPSEEK_API_KEY") or os.getenv("MIMO_API_KEY"))
    return has_gemini, has_deepseek


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    has_gemini, has_deepseek = check_api_keys()
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        hasGeminiKey=has_gemini,
        hasDeepseekKey=has_deepseek
    )


@router.get("/api/health", response_model=HealthResponse)
async def health_check_api():
    """健康检查接口（兼容前端路径）"""
    has_gemini, has_deepseek = check_api_keys()
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        hasGeminiKey=has_gemini,
        hasDeepseekKey=has_deepseek
    )


@router.get("/api/health/agents")
async def health_agents():
    """诊断 agents 是否可用"""
    result = {}
    try:
        from backend.services.interview_service import _get_interviewer, _get_evaluator
        i = _get_interviewer()
        if i:
            q = i.generate_question('TestCo', 'dev', ['Python'], 0, [])
            result['interviewer'] = {'ok': True, 'question': q[:200]}
        else:
            result['interviewer'] = {'ok': False, 'reason': 'None returned'}
    except Exception as ex:
        result['interviewer'] = {'ok': False, 'error': str(ex)}

    try:
        e = _get_evaluator()
        if e:
            r = e.evaluate('What is Python?', 'Python is a language.', 'technical', 'Python')
            result['evaluator'] = {'ok': True, 'score': r.get('score'), 'feedback': str(r.get('feedback', ''))[:200]}
        else:
            result['evaluator'] = {'ok': False, 'reason': 'None returned'}
    except Exception as ex:
        result['evaluator'] = {'ok': False, 'error': str(ex)}

    return result
