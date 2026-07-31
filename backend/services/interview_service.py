from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict
from datetime import datetime, timezone
import json
import uuid

from ..database.models import User, Interview, Question, Answer, Evaluation
from ..config import MAX_QUESTIONS, MAX_FOLLOWUPS, SCORE_THRESHOLD_FOR_FOLLOWUP


# ── Agent/RAG 懒初始化（首次用到时才 import + 实例化，避免启动时强制要 Key） ──
_AGENT_ORCHESTRATOR = None
_INTERVIEWER = None
_EVALUATOR = None
_RAG_ENGINE = None


def _get_orchestrator():
    global _AGENT_ORCHESTRATOR
    if _AGENT_ORCHESTRATOR is None:
        try:
            from agents.orchestrator import AgentOrchestrator
            _AGENT_ORCHESTRATOR = AgentOrchestrator()
        except Exception:
            _AGENT_ORCHESTRATOR = False  # sentinel — 标记不可用
    return _AGENT_ORCHESTRATOR if _AGENT_ORCHESTRATOR else None


def _get_interviewer():
    global _INTERVIEWER
    if _INTERVIEWER is None:
        try:
            from agents.interviewer import InterviewerAgent
            _INTERVIEWER = InterviewerAgent()
            import os as _os
            with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "agent_debug.log"), "a", encoding="utf-8") as f:
                f.write(f"[OK] InterviewerAgent init success, model={_INTERVIEWER.llm.model_name}\n")
        except Exception as e:
            import os as _os
            with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "agent_debug.log"), "a", encoding="utf-8") as f:
                f.write(f"[FAIL] InterviewerAgent init: {e}\n")
                import traceback
                traceback.print_exc(file=f)
            _INTERVIEWER = False
    return _INTERVIEWER if _INTERVIEWER else None


def _get_evaluator():
    global _EVALUATOR
    if _EVALUATOR is None:
        try:
            from agents.evaluator import EvaluatorAgent
            _EVALUATOR = EvaluatorAgent()
            import os as _os
            with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "agent_debug.log"), "a", encoding="utf-8") as f:
                f.write(f"[OK] EvaluatorAgent init success, model={_EVALUATOR.llm.model_name}\n")
        except Exception as e:
            import os as _os
            with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "agent_debug.log"), "a", encoding="utf-8") as f:
                f.write(f"[FAIL] EvaluatorAgent init: {e}\n")
                import traceback
                traceback.print_exc(file=f)
            _EVALUATOR = False
    return _EVALUATOR if _EVALUATOR else None


def _get_rag():
    global _RAG_ENGINE
    if _RAG_ENGINE is None:
        try:
            from rag.engine import RAGEngine
            _RAG_ENGINE = RAGEngine()
        except Exception:
            _RAG_ENGINE = False
    return _RAG_ENGINE if _RAG_ENGINE else None


class InterviewService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_interview(
        self,
        user_id: str,
        target_company: Optional[str] = None,
        target_position: Optional[str] = None,
        tech_stack: Optional[List[str]] = None,
        interview_mode: str = "technical",
        session_id: Optional[str] = None
    ) -> Interview:
        """创建面试"""
        # 检查用户是否存在
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")
        
        interview = Interview(
            user_id=user_id,
            target_company=target_company,
            target_position=target_position,
            tech_stack=json.dumps(tech_stack or []),
            interview_mode=interview_mode,
            session_id=session_id,
            status="created",
            current_phase="START"
        )
        self.db.add(interview)
        self.db.commit()
        self.db.refresh(interview)
        return interview
    
    def start_interview(self, interview_id: str) -> Interview:
        """开始面试 —— 并行生成全部 MAX_QUESTIONS 道题

        返回 Interview ORM 对象，路由层通过 response_model=InterviewResponse
        让 Pydantic 自动序列化，确保前端拿到包含完整 questions[] 的结构
        （前端侧边栏题目进度、雷达图完成度等都依赖此数组）。

        生成失败时每题回退到占位，保证面试不因 LLM 异常而无法开始。
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError("面试不存在")
        if interview.status != "created":
            raise ValueError("面试已开始或已结束")

        # 并行生成 MAX_QUESTIONS 道题 —— 大幅缩短 LLM 调用总耗时
        def generate_one(idx: int) -> Question:
            """在独立线程中生成一道题，需要自己的 DB session"""
            from ..database import SessionLocal
            db = SessionLocal()
            try:
                local_interview = db.query(Interview).filter(Interview.id == interview_id).first()
                if not local_interview:
                    raise ValueError("面试不存在")
                # 不修改 current_question_index —— 这会导致多线程 commit 竞争，
                # 最终主线程写入的 0 被覆盖成最后一题的 idx（如 2），进而让
                # _decide_next 永远拿到错误的题目 → 追问死循环。
                try:
                    q = self._generate_question_in_session(local_interview, db, idx)
                    db.commit()
                    return q
                except Exception:
                    db.rollback()
                    q = self._generate_fallback_question_in_session(local_interview, db, idx)
                    db.commit()
                    return q
            finally:
                db.close()

        questions = []
        with ThreadPoolExecutor(max_workers=MAX_QUESTIONS) as executor:
            futures = {executor.submit(generate_one, idx): idx for idx in range(MAX_QUESTIONS)}
            for future in as_completed(futures):
                try:
                    q = future.result()
                    questions.append(q)
                except Exception:
                    pass  # 兜底已在 generate_one 内部处理

        # 更新面试状态
        interview.status = "in_progress"
        interview.current_phase = "TECHNICAL"
        interview.current_question_index = 0
        interview.started_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def submit_answer(
        self,
        interview_id: str,
        user_answer: str,
        question_id: Optional[str] = None,
    ) -> dict:
        """提交回答 —— 按 questionId 定位当前题

        question_id 由前端提交时携带（InterviewView 通过 currentQuestion.id
        传入）。如果未传则退化到按 current_question_index 定位，保持后向兼容。
        """
        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError("面试不存在")
        if interview.status != "in_progress":
            raise ValueError("面试未在进行中")

        # 获取当前问题
        current_question = self._get_current_question(interview, question_id=question_id)
        if not current_question:
            raise ValueError("没有当前问题")

        # 评估回答
        evaluation = self._evaluate_answer(current_question, user_answer)

        # 保存回答
        answer = Answer(
            interview_id=interview_id,
            question_id=current_question.id,
            user_answer=user_answer,
            score=evaluation["score"],
            dimension_scores=json.dumps(evaluation["dimensions"]),
            feedback=evaluation["feedback"],
            strengths=json.dumps(evaluation["strengths"]),
            improvements=json.dumps(evaluation["improvements"])
        )
        self.db.add(answer)

        # 保存评估历史
        eval_record = Evaluation(
            user_id=interview.user_id,
            category=current_question.category,
            score=evaluation["score"]
        )
        self.db.add(eval_record)

        # 决定下一步（传入 question_id 精确定位，防止 current_question_index 被污染）
        next_action, next_message = self._decide_next(interview, evaluation["score"], user_answer, question_id=question_id)

        # 更新面试状态
        if next_action == "followup":
            interview.current_phase = "FOLLOWUP"
        elif next_action == "next_question":
            # 基于当前题在 questions 列表中的位置计算下一题索引，
            # 不信任 interview.current_question_index（可能被并行线程污染）
            questions_list = self.db.query(Question).filter(
                Question.interview_id == interview_id
            ).order_by(Question.created_at).all()
            current_idx = next((i for i, q in enumerate(questions_list) if q.id == current_question.id), 0)
            next_idx = current_idx + 1
            interview.current_question_index = next_idx
            interview.current_phase = "TECHNICAL"
            if next_idx < len(questions_list):
                next_message = questions_list[next_idx].question_text
            else:
                next_message = ""
        elif next_action == "end":
            interview.status = "completed"
            interview.current_phase = "END"
            interview.completed_at = datetime.now(timezone.utc)
            interview.overall_score = self._calculate_overall_score(interview_id)

        self.db.commit()

        return {
            "interview_id": interview.id,
            "current_phase": interview.current_phase,
            "question_index": interview.current_question_index,
            "evaluation": evaluation,
            "next_action": next_action,
            "next_message": next_message,
            "is_finished": next_action == "end"
        }
    
    def skip_question(self, interview_id: str) -> dict:
        """跳过问题 —— 题目已预先在 start_interview 生成，这里只前进索引"""
        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError("面试不存在")
        if interview.status != "in_progress":
            raise ValueError("面试未在进行中")

        # 移动到下一题
        interview.current_question_index += 1
        interview.current_phase = "TECHNICAL"

        # 检查是否还有题目
        if interview.current_question_index >= MAX_QUESTIONS:
            interview.status = "completed"
            interview.current_phase = "END"
            interview.completed_at = datetime.now(timezone.utc)
            interview.overall_score = self._calculate_overall_score(interview_id)
            self.db.commit()

            return {
                "interview_id": interview.id,
                "current_phase": "END",
                "question_index": interview.current_question_index,
                "evaluation": None,
                "next_action": "end",
                "next_message": "面试已结束，请查看总结。",
                "is_finished": True
            }

        # 取已生成的下一题
        next_question = self._get_question_by_index(interview, interview.current_question_index)
        next_message = next_question.question_text if next_question else ""
        self.db.commit()

        return {
            "interview_id": interview.id,
            "current_phase": interview.current_phase,
            "question_index": interview.current_question_index,
            "evaluation": None,
            "next_action": "answer",
            "next_message": next_message,
            "is_finished": False
        }
    
    def get_interview_state(self, interview_id: str) -> Optional[dict]:
        """获取面试状态"""
        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            return None
        
        questions = self.db.query(Question).filter(Question.interview_id == interview_id).all()
        answers = self.db.query(Answer).filter(Answer.interview_id == interview_id).all()
        
        tech_stack = json.loads(interview.tech_stack) if interview.tech_stack else []
        
        return {
            "interview_id": interview.id,
            "user_id": interview.user_id,
            "target_company": interview.target_company,
            "target_position": interview.target_position,
            "tech_stack": tech_stack,
            "interview_mode": interview.interview_mode,
            "status": interview.status,
            "current_phase": interview.current_phase,
            "current_question_index": interview.current_question_index,
            "total_questions": len(questions),
            "overall_score": interview.overall_score,
            "started_at": interview.started_at,
            "completed_at": interview.completed_at,
            "questions": [
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "question_type": q.question_type,
                    "category": q.category,
                    "difficulty": q.difficulty
                }
                for q in questions
            ],
            "answers": [
                {
                    "question_id": a.question_id,
                    "score": a.score,
                    "created_at": a.created_at
                }
                for a in answers
            ]
        }
    
    def get_interview_summary(self, interview_id: str) -> dict:
        """获取面试总结"""
        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError("面试不存在")
        if interview.status != "completed":
            raise ValueError("面试尚未完成")
        
        answers = self.db.query(Answer).filter(Answer.interview_id == interview_id).all()
        questions = self.db.query(Question).filter(Question.interview_id == interview_id).all()
        
        # 计算时长
        duration_minutes = None
        if interview.started_at and interview.completed_at:
            duration = interview.completed_at - interview.started_at
            duration_minutes = int(duration.total_seconds() / 60)
        
        # 计算分类分数
        category_scores = {}
        for q in questions:
            for a in answers:
                if a.question_id == q.id and a.score is not None:
                    if q.category not in category_scores:
                        category_scores[q.category] = []
                    category_scores[q.category].append(a.score)
        
        category_avg = {k: round(sum(v)/len(v), 1) for k, v in category_scores.items()}
        
        # 计算维度汇总
        dimension_scores = {"accuracy": [], "completeness": [], "logic": [], "expression": []}
        for a in answers:
            if a.dimension_scores:
                dims = json.loads(a.dimension_scores)
                for key in dimension_scores:
                    if key in dims:
                        dimension_scores[key].append(dims[key])
        
        dimension_summary = {k: round(sum(v)/len(v), 1) if v else 0 for k, v in dimension_scores.items()}
        
        # ── AI 生成个性化诊断（PlannerAgent）──
        strengths = []
        weaknesses = []
        recommendations = []

        try:
            qa_history = []
            for q in questions:
                for a in answers:
                    if a.question_id == q.id:
                        qa_history.append({
                            "question": q.question_text,
                            "score": a.score or 0,
                        })
                        break

            from agents.planner import PlannerAgent
            planner = PlannerAgent()
            plan = planner.generate_plan(qa_history)

            strengths = plan.get("strengths", [])
            weaknesses = plan.get("weak_points", [])
            for item in plan.get("study_plan", []):
                recommendations.append(item.get("suggestion", ""))
        except Exception:
            # 降级：硬编码兜底
            strengths = [k for k, v in category_avg.items() if v >= 75]
            weaknesses = [k for k, v in category_avg.items() if v < 60]
            for weak in weaknesses:
                recommendations.append(f"建议深入学习{weak}相关知识")

        return {
            "interview_id": interview.id,
            "user_id": interview.user_id,
            "target_company": interview.target_company,
            "target_position": interview.target_position,
            "status": interview.status,
            "overall_score": interview.overall_score,
            "total_questions": len(questions),
            "answered_questions": len(answers),
            "started_at": interview.started_at,
            "completed_at": interview.completed_at,
            "duration_minutes": duration_minutes,
            "category_scores": category_avg,
            "dimension_summary": dimension_summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations
        }
    
    def list_interviews(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 20
    ) -> dict:
        """获取面试列表"""
        query = self.db.query(Interview)
        
        if user_id:
            query = query.filter(Interview.user_id == user_id)
        if status:
            query = query.filter(Interview.status == status)
        
        total = query.count()
        items = query.order_by(Interview.created_at.desc()).offset((page-1)*size).limit(size).all()
        
        return {
            "total": total,
            "page": page,
            "size": size,
            "items": [
                {
                    "id": i.id,
                    "user_id": i.user_id,
                    "target_company": i.target_company,
                    "target_position": i.target_position,
                    "tech_stack": json.loads(i.tech_stack) if i.tech_stack else [],
                    "status": i.status,
                    "overall_score": i.overall_score,
                    "created_at": i.created_at
                }
                for i in items
            ]
        }
    
    def _generate_question(self, interview: Interview) -> Question:
        """生成面试题 —— 使用 self.db session"""
        return self._generate_question_in_session(interview, self.db, interview.current_question_index)

    def _generate_question_in_session(self, interview: Interview, db: Session, idx: int = 0) -> Question:
        """生成面试题 —— 优先使用 InterviewerAgent + RAG 检索，失败则回退占位"""
        tech_stack = json.loads(interview.tech_stack) if interview.tech_stack else []
        first_tech = tech_stack[0] if tech_stack else "技术"

        # ---------- 尝试真实 Agent ----------
        try:
            interviewer = _get_interviewer()
            if interviewer:
                agent_question = interviewer.generate_question(
                    target_company=interview.target_company or "",
                    target_position=interview.target_position or "",
                    tech_stack=tech_stack,
                    question_index=idx,
                    previous_qa=[],
                )
                if agent_question and len(agent_question) > 10:
                    question = Question(
                        interview_id=interview.id,
                        question_text=agent_question,
                        question_type="technical",
                        category=first_tech,
                        difficulty=5,
                        source="agent",
                    )
                    db.add(question)
                    db.flush()
                    return question
                else:
                    import os as _os
                    with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "agent_debug.log"), "a", encoding="utf-8") as f:
                        f.write(f"[WARN] agent_question too short: {repr(agent_question)[:200]}\n")
        except Exception as e:
            import os as _os
            with open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "agent_debug.log"), "a", encoding="utf-8") as f:
                f.write(f"[FAIL] generate_question exception: {e}\n")
                import traceback
                traceback.print_exc(file=f)

        # ---------- 回退：占位题库 ----------
        placeholder_pool = [
            f"请介绍一下{first_tech}的核心特性",
            f"你在项目中如何使用{first_tech}？",
            f"请解释{tech_stack[1] if len(tech_stack) > 1 else 'MySQL'}的索引原理",
            "请介绍一下你最近的一个项目经历",
            "你在团队开发中遇到过什么挑战？如何解决的？"
        ]
        question_text = placeholder_pool[idx % len(placeholder_pool)]

        question = Question(
            interview_id=interview.id,
            question_text=question_text,
            question_type="technical",
            category=first_tech,
            difficulty=5,
            source="placeholder",
        )
        db.add(question)
        db.flush()
        return question

    def _generate_fallback_question(self, interview: Interview) -> Question:
        """start_interview 时的兜底题：即使 RAG/LLM 异常，也能保证开始一场面试"""
        return self._generate_fallback_question_in_session(interview, self.db, interview.current_question_index)

    def _generate_fallback_question_in_session(self, interview: Interview, db: Session, idx: int = 0) -> Question:
        """start_interview 时的兜底题（接受 session 参数，用于多线程环境）"""
        tech_stack = json.loads(interview.tech_stack) if interview.tech_stack else []
        first_tech = tech_stack[0] if tech_stack else "技术"
        fallback_pool = [
            f"请介绍一下你对 {first_tech} 的理解，并结合实际项目说明它的核心特性。",
            f"在 {first_tech} 的实际应用中，你遇到过哪些挑战？是如何解决的？",
            f"请谈谈 {first_tech} 的未来发展趋势和你个人的技术规划。",
        ]
        question_text = fallback_pool[idx % len(fallback_pool)]
        question = Question(
            interview_id=interview.id,
            question_text=question_text,
            question_type="technical",
            category=first_tech,
            difficulty=5,
            source="fallback",
        )
        db.add(question)
        db.flush()
        return question
    
    def _get_current_question(
        self,
        interview: Interview,
        question_id: Optional[str] = None,
    ) -> Optional[Question]:
        """获取当前问题 —— 优先按 questionId 精确查找，回退到索引定位"""
        if question_id:
            q = self.db.query(Question).filter(
                Question.id == question_id,
                Question.interview_id == interview.id,
            ).first()
            if q:
                return q
            # questionId 没命中就警告式回退，不直接报错，兼容老触点
        questions = self.db.query(Question).filter(
            Question.interview_id == interview.id
        ).order_by(Question.created_at).all()

        if interview.current_question_index < len(questions):
            return questions[interview.current_question_index]
        return None

    def _get_question_by_index(self, interview: Interview, idx: int) -> Optional[Question]:
        """按题号获取问题（题目已在 start 时全部生成好）"""
        questions = self.db.query(Question).filter(
            Question.interview_id == interview.id
        ).order_by(Question.created_at).all()
        if 0 <= idx < len(questions):
            return questions[idx]
        return None
    
    def _evaluate_answer(self, question: Question, user_answer: str) -> dict:
        """评估回答 —— 优先使用 EvaluatorAgent + RAG 标准答案检索，失败则回退"""
        import os as _os
        _log = lambda msg: open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "agent_debug.log"), "a", encoding="utf-8").write(msg + "\n")
        import traceback
        # ---------- 尝试真实 EvaluatorAgent ----------
        try:
            evaluator = _get_evaluator()
            _log(f"[DEBUG] _get_evaluator() returned: {evaluator}")
            if evaluator:
                _log(f"[DEBUG] Calling evaluator.evaluate()...")
                result = evaluator.evaluate(
                    question=question.question_text,
                    user_answer=user_answer,
                    question_type=question.question_type or "technical",
                    category=question.category or "通用",
                )
                _log(f"[DEBUG] evaluator.evaluate() returned: {result}")
                if result and result.get("score") is not None:
                    return result
        except Exception as e:
            _log(f"[ERROR] EvaluatorAgent failed: {e}")
            traceback.print_exc()

        # ---------- 回退：AI 评估失败，返回 0 分 ----------
        _log("[WARN] AI evaluation failed, returning score 0")
        return {
            "score": 0.0,
            "dimensions": {"accuracy": 0, "completeness": 0, "logic": 0, "expression": 0},
            "strengths": [],
            "improvements": ["AI 评估服务暂时不可用，请检查 API Key 配置"],
            "feedback": "AI 评估服务暂时不可用，本次回答未获得有效评分。请检查后端日志确认 DeepSeek API 连接状态。"
        }
    
    def _decide_next(self, interview: Interview, score: float, user_answer: str = "", question_id: str = None) -> tuple:
        """决定下一步

        question_id 由前端提交时传入，用于精确定位当前题。
        不依赖 interview.current_question_index —— 并行生成时
        该字段会被多线程 commit 覆盖，导致死循环追问。
        """
        # 获取当前问题 —— 优先按 question_id 查找
        current = self._get_current_question(interview, question_id=question_id)
        if not current:
            return "end", "面试已结束，请查看总结。"

        # 当前问题的回答次数 = 追问次数 + 1（首答）
        answers_count = self.db.query(Answer).filter(
            Answer.interview_id == interview.id,
            Answer.question_id == current.id
        ).count()

        # 判断是否应该追问
        if score < SCORE_THRESHOLD_FOR_FOLLOWUP and answers_count < MAX_FOLLOWUPS:
            # 优先使用 InterviewerAgent 生成追问
            followup_message = ""
            try:
                interviewer = _get_interviewer()
                if interviewer:
                    dims = {}
                    if current.dimension_scores:
                        dims = json.loads(current.dimension_scores)
                    followup_message = interviewer.generate_followup(
                        original_question=current.question_text,
                        user_answer=user_answer or "",
                        evaluation_result={"score": score, "dimensions": dims},
                        followup_count=answers_count - 1,
                    )
            except Exception:
                pass
            if not followup_message:
                followup_message = "能详细说说吗？"
            return "followup", followup_message

        # 判断是否还有题目（基于当前题在列表中的位置，而非可能被污染的 current_question_index）
        questions_list = self.db.query(Question).filter(
            Question.interview_id == interview.id
        ).order_by(Question.created_at).all()
        current_idx = next((i for i, q in enumerate(questions_list) if q.id == current.id), 0)
        if current_idx + 1 < len(questions_list):
            return "next_question", ""

        # 面试结束
        return "end", "面试已结束，请查看总结。"
    
    def _calculate_overall_score(self, interview_id: str) -> float:
        """计算总分"""
        answers = self.db.query(Answer).filter(
            Answer.interview_id == interview_id,
            Answer.score.isnot(None)
        ).all()
        
        if not answers:
            return 0.0
        
        scores = [a.score for a in answers]
        return round(sum(scores) / len(scores), 1)
