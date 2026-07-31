"""
面试接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import json

from ...database import get_db
from ...database.models import Interview
from ..deps import get_session_id, get_current_user
from ...database.models import User
from ...schemas.interview import (
    InterviewCreate, InterviewResponse, InterviewState, 
    InterviewSummary, AnswerSubmit, AnswerResponse, InterviewListItem,
    InterviewListResponse
)
from ...services.interview_service import InterviewService, _get_interviewer, _get_evaluator

router = APIRouter(prefix="/api/interviews", tags=["interviews"])

def _verify_owner(interview_id: str, current_user: User, db: Session) -> None:
    """校验这场面试确实属于当前登录用户，否则拒绝访问"""
    from ...database.models import Interview
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="面试不存在")
    if interview.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问他人的面试记录")

@router.post("", response_model=InterviewResponse, status_code=201)
def create_interview(
    data: InterviewCreate,
    db: Session = Depends(get_db),
    session_id: Optional[str] = Depends(get_session_id),
    current_user: User = Depends(get_current_user)
):
    """创建面试 —— 强制归属于登录用户，忽略请求体里的userId（防止冒充他人）"""
    service = InterviewService(db)
    try:
        interview = service.create_interview(
            user_id=current_user.id,
            target_company=data.target_company,
            target_position=data.target_position,
            tech_stack=data.tech_stack,
            interview_mode=data.interview_mode,
            session_id=session_id
        )
        return interview
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{interview_id}/start", response_model=InterviewResponse)
def start_interview(interview_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """开始面试 —— 一次性生成全部 N 道题，返回 Interview 对象"""
    _verify_owner(interview_id, current_user, db)
    service = InterviewService(db)
    try:
        interview = service.start_interview(interview_id)
        return interview
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{interview_id}/answer", response_model=AnswerResponse)
def submit_answer(interview_id: str, data: AnswerSubmit, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """提交回答 —— 前端通过 questionId 定位当前题目"""
    _verify_owner(interview_id, current_user, db)
    service = InterviewService(db)
    try:
        result = service.submit_answer(interview_id, data.user_answer, question_id=data.question_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{interview_id}/skip", response_model=AnswerResponse)
def skip_question(interview_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """跳过当前问题"""
    _verify_owner(interview_id, current_user, db)
    service = InterviewService(db)
    try:
        result = service.skip_question(interview_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{interview_id}/state", response_model=InterviewState)
def get_interview_state(interview_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取面试状态"""
    _verify_owner(interview_id, current_user, db)
    service = InterviewService(db)
    state = service.get_interview_state(interview_id)
    if not state:
        raise HTTPException(status_code=404, detail="面试不存在")
    return state


@router.get("/{interview_id}/summary", response_model=InterviewSummary)
def get_interview_summary(interview_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取面试总结"""
    _verify_owner(interview_id, current_user, db)
    service = InterviewService(db)
    try:
        summary = service.get_interview_summary(interview_id)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=InterviewListResponse)
def list_interviews(
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取面试列表 —— 只返回当前登录用户自己的记录"""
    service = InterviewService(db)
    result = service.list_interviews(user_id=current_user.id, status=status, page=page, size=size)
    return result


def _sse_format(data: dict) -> str:
    """把一个dict包装成SSE协议要求的格式：data: {json}\n\n"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/{interview_id}/preview-question/stream")
async def preview_question_stream(interview_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    流式演示接口：展示"生成下一道面试题"的实时生成过程。
    仅用于前端打字机效果展示，不写数据库、不影响正式的 /start 流程。
    """
    _verify_owner(interview_id, current_user, db)
    interview = db.query(Interview).filter(Interview.id == interview_id).first()

    async def event_generator():
        try:
            interviewer = _get_interviewer()
            if not interviewer:
                yield _sse_format({"type": "error", "message": "Agent暂不可用"})
                return
            tech_stack = json.loads(interview.tech_stack) if interview.tech_stack else []
            async for piece in interviewer.generate_question_stream(
                target_company=interview.target_company or "",
                target_position=interview.target_position or "",
                tech_stack=tech_stack,
                question_index=interview.current_question_index,
                previous_qa=[],
            ):
                yield _sse_format({"type": "chunk", "content": piece})
            yield _sse_format({"type": "done"})
        except Exception as e:
            yield _sse_format({"type": "error", "message": str(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{interview_id}/preview-feedback/stream")
async def preview_feedback_stream(interview_id: str, data: AnswerSubmit, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    流式演示接口：先计算评分（不流式，JSON结构无法流式解析），
    再流式生成一段自然语言点评。仅用于展示效果，不写入数据库。
    """
    from ...database.models import Question

    _verify_owner(interview_id, current_user, db)
    interview = db.query(Interview).filter(Interview.id == interview_id).first()

    question = db.query(Question).filter(Question.id == data.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="问题不存在")

    async def event_generator():
        try:
            evaluator = _get_evaluator()
            if not evaluator:
                yield _sse_format({"type": "error", "message": "Agent暂不可用"})
                return

            evaluation = evaluator.evaluate(
                question=question.question_text,
                user_answer=data.user_answer,
                question_type=question.question_type or "technical",
                category=question.category or "通用",
            )
            yield _sse_format({"type": "score", "evaluation": evaluation})

            async for piece in evaluator.generate_feedback_stream(
                question=question.question_text,
                user_answer=data.user_answer,
                evaluation=evaluation,
            ):
                yield _sse_format({"type": "chunk", "content": piece})
            yield _sse_format({"type": "done"})
        except Exception as e:
            yield _sse_format({"type": "error", "message": str(e)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")