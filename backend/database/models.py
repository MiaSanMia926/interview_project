from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from .connection import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # 存哈希值，绝不存明文密码
    email = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    interviews = relationship("Interview", back_populates="user")
    evaluations = relationship("Evaluation", back_populates="user")

class UserSession(Base):
    """登录会话表 —— 记录令牌与用户的对应关系，用于验证"这个请求确实是谁发的" """
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    token = Column(String(64), unique=True, nullable=False, index=True)  # 随机令牌，前端登录后拿到并保存
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    # 令牌有效期截止时间；超过这个时间视为登录已失效，需要重新登录。
    # nullable=True 是为了兼容迁移前（没有这一列时）创建的旧会话记录。
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User")

class Interview(Base):
    __tablename__ = "interviews"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100), index=True, nullable=True)  # 前端sessionId，用于会话隔离追踪
    target_company = Column(String(100))
    target_position = Column(String(100))
    tech_stack = Column(Text)  # JSON数组
    interview_mode = Column(String(50), default="technical")
    status = Column(String(20), default="created")  # created/in_progress/completed
    current_phase = Column(String(50), default="START")
    current_question_index = Column(Integer, default=0)
    overall_score = Column(Float)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="interviews")
    questions = relationship("Question", back_populates="interview")
    answers = relationship("Answer", back_populates="interview")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    interview_id = Column(String(36), ForeignKey("interviews.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50))  # technical/behavioral/system_design
    category = Column(String(100))  # Redis/MySQL/Python等
    difficulty = Column(Integer)  # 1-10
    source = Column(String(50), default="rag_generated")  # rag_generated/llm_generated
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    interview = relationship("Interview", back_populates="questions")
    answers = relationship("Answer", back_populates="question")

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    interview_id = Column(String(36), ForeignKey("interviews.id"), nullable=False)
    question_id = Column(String(36), ForeignKey("questions.id"), nullable=False)
    user_answer = Column(Text, nullable=False)
    score = Column(Float)
    dimension_scores = Column(Text)  # JSON
    feedback = Column(Text)
    strengths = Column(Text)  # JSON数组
    improvements = Column(Text)  # JSON数组
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    interview = relationship("Interview", back_populates="answers")
    question = relationship("Question", back_populates="answers")

class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    category = Column(String(100))  # Redis/MySQL等
    score = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="evaluations")
