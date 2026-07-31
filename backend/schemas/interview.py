"""
面试相关Schema
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from .common import CamelModel


class InterviewCreate(CamelModel):
    """创建面试请求"""
    user_id: str = Field(..., alias="userId", description="用户ID")
    target_company: Optional[str] = Field(None, alias="targetCompany", description="目标公司")
    target_position: Optional[str] = Field(None, alias="targetPosition", description="目标职位")
    tech_stack: Optional[List[str]] = Field(default=[], alias="techStack", description="技术栈")
    interview_mode: Optional[str] = Field("technical", alias="interviewMode", description="面试模式")


class QuestionInfo(CamelModel):
    """问题信息（供 InterviewResponse 嵌套使用）"""
    id: str
    interview_id: Optional[str] = Field(None, alias="interviewId")
    question_text: str = Field(alias="questionText")
    question_type: Optional[str] = Field(None, alias="questionType")
    category: Optional[str] = None
    difficulty: Optional[int] = None

    class Config:
        from_attributes = True


class InterviewResponse(CamelModel):
    """面试响应"""
    id: str
    user_id: str = Field(alias="userId")
    target_company: Optional[str] = Field(alias="targetCompany")
    target_position: Optional[str] = Field(alias="targetPosition")
    tech_stack: Optional[List[str]] = Field(alias="techStack")
    interview_mode: str = Field(alias="interviewMode")
    status: str
    current_phase: str = Field(alias="currentPhase")
    current_question_index: int = Field(alias="currentQuestionIndex")
    overall_score: Optional[float] = Field(alias="overallScore")
    started_at: Optional[datetime] = Field(alias="startedAt")
    completed_at: Optional[datetime] = Field(alias="completedAt")
    created_at: datetime = Field(alias="createdAt")
    duration_minutes: Optional[int] = Field(None, alias="durationMinutes")
    questions: Optional[List[QuestionInfo]] = None

    @field_validator('tech_stack', mode='before')
    @classmethod
    def parse_tech_stack(cls, v):
        """解析tech_stack字段，支持JSON字符串和列表"""
        if v is None:
            return []
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        if isinstance(v, list):
            return v
        return []

    class Config:
        from_attributes = True


class InterviewListResponse(CamelModel):
    """面试列表响应"""
    total: int
    page: int
    size: int
    items: List["InterviewListItem"]


class AnswerInfo(CamelModel):
    """回答信息"""
    question_id: str = Field(alias="questionId")
    user_answer: Optional[str] = Field(None, alias="userAnswer")
    score: Optional[float]
    created_at: datetime = Field(alias="createdAt")


class InterviewState(CamelModel):
    """面试状态"""
    interview_id: str = Field(alias="interviewId")
    user_id: str = Field(alias="userId")
    target_company: Optional[str] = Field(alias="targetCompany")
    target_position: Optional[str] = Field(alias="targetPosition")
    tech_stack: Optional[List[str]] = Field(alias="techStack")
    interview_mode: str = Field(alias="interviewMode")
    status: str
    current_phase: str = Field(alias="currentPhase")
    current_question_index: int = Field(alias="currentQuestionIndex")
    total_questions: int = Field(alias="totalQuestions")
    overall_score: Optional[float] = Field(alias="overallScore")
    started_at: Optional[datetime] = Field(alias="startedAt")
    completed_at: Optional[datetime] = Field(alias="completedAt")
    questions: List[QuestionInfo]
    answers: List[AnswerInfo]


class DimensionScores(CamelModel):
    """维度分数"""
    accuracy: float
    completeness: float
    logic: float
    expression: float


class EvaluationResult(CamelModel):
    """评估结果"""
    score: Optional[float]
    dimensions: DimensionScores
    strengths: List[str]
    improvements: List[str]
    feedback: str
    error: Optional[str] = None
    retry: Optional[bool] = None


class AnswerSubmit(CamelModel):
    """提交回答"""
    question_id: Optional[str] = Field(None, alias="questionId", description="当前问题ID（前端必传）")
    user_answer: str = Field(..., alias="userAnswer", min_length=1, description="用户回答内容")


class AnswerResponse(CamelModel):
    """回答响应"""
    interview_id: str = Field(alias="interviewId")
    current_phase: str = Field(alias="currentPhase")
    question_index: int = Field(alias="questionIndex")
    evaluation: Optional[EvaluationResult]
    next_action: str = Field(alias="nextAction")
    next_message: str = Field(alias="nextMessage")
    is_finished: bool = Field(alias="isFinished")


class InterviewSummary(CamelModel):
    """面试总结"""
    interview_id: str = Field(alias="interviewId")
    user_id: str = Field(alias="userId")
    target_company: Optional[str] = Field(alias="targetCompany")
    target_position: Optional[str] = Field(alias="targetPosition")
    status: str
    overall_score: Optional[float] = Field(alias="overallScore")
    total_questions: int = Field(alias="totalQuestions")
    answered_questions: int = Field(alias="answeredQuestions")
    started_at: Optional[datetime] = Field(alias="startedAt")
    completed_at: Optional[datetime] = Field(alias="completedAt")
    duration_minutes: Optional[int] = Field(alias="durationMinutes")
    category_scores: Dict[str, float] = Field(alias="categoryScores")
    dimension_summary: Dict[str, float] = Field(alias="dimensionSummary")
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


class InterviewListItem(CamelModel):
    """面试列表项"""
    id: str
    user_id: str = Field(alias="userId")
    target_company: Optional[str] = Field(alias="targetCompany")
    target_position: Optional[str] = Field(alias="targetPosition")
    tech_stack: Optional[List[str]] = Field(None, alias="techStack")
    status: str
    overall_score: Optional[float] = Field(alias="overallScore")
    created_at: datetime = Field(alias="createdAt")
