"""
用户服务
"""
import json
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from ..database.models import User, Interview, Evaluation, Answer, Question


class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, username: str) -> User:
        """获取或创建用户（与前端 Express 版行为保持一致）"""
        existing = self.db.query(User).filter(User.username == username).first()
        if existing:
            return existing

        user = User(username=username)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_profile(self, user_id: str) -> Optional[dict]:
        """获取用户画像 —— 调用 PlannerAgent 生成 AI 驱动的分析"""
        user = self.get_user(user_id)
        if not user:
            return None

        # 获取已完成的面试
        interviews = self.db.query(Interview).filter(
            Interview.user_id == user_id,
            Interview.status == "completed"
        ).order_by(Interview.completed_at.desc()).all()

        total_interviews = len(interviews)

        if total_interviews == 0:
            return self._empty_profile(user)

        # 计算平均分
        scores = [i.overall_score for i in interviews if i.overall_score is not None]
        average_score = sum(scores) / len(scores) if scores else 0.0

        # 获取评估历史
        evaluations = self.db.query(Evaluation).filter(Evaluation.user_id == user_id).all()

        # 计算分类分数
        category_scores = self._calculate_category_scores(evaluations)

        # 生成雷达图数据 —— 从 Answer.dimension_scores 取真实四维度分数
        radar_data = self._generate_radar_data(user_id)

        # 生成分类数据
        category_data = self._generate_category_data(category_scores)

        # 生成趋势数据
        trend_data = self._generate_trend_data(interviews)

        # ─── 调用 PlannerAgent 生成 AI 学习规划 ───
        planner_result = self._call_planner(interviews, evaluations)

        # 使用 PlannerAgent 产出：优势 / 弱点 / 建议 / 挑战
        strengths = planner_result.get("strengths") or self._analyze_strengths_weaknesses(category_scores)[0]
        weaknesses = planner_result.get("weaknesses") or self._analyze_strengths_weaknesses(category_scores)[1]
        recommendations = planner_result.get("recommendations") or self._generate_recommendations(weaknesses)
        challenges = planner_result.get("challenges") or self._generate_default_challenges(weaknesses)

        # 生成知识图谱（优先用 PlannerAgent 的 weak_points 增强）
        knowledge_graph = self._generate_knowledge_graph(
            evaluations, strengths, weaknesses,
            planner_weak_points=planner_result.get("planner_weak_points"),
        )

        return {
            "user_id": user.id,
            "username": user.username,
            "total_interviews": total_interviews,
            "average_score": round(average_score, 1),
            "radar_data": radar_data,
            "category_data": category_data,
            "trend_data": trend_data,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
            "challenges": challenges,
            "knowledge_graph": knowledge_graph,
        }
    
    def _call_planner(self, interviews, evaluations) -> dict:
        """调用 PlannerAgent 生成 AI 学习规划，失败时返回空 dict"""
        import traceback
        try:
            from agents.planner import PlannerAgent
            from agents.knowledge import KnowledgeAgent

            print("[INFO] Initializing PlannerAgent...")
            planner = PlannerAgent(knowledge_agent=KnowledgeAgent())

            # 构建问答历史（收集所有面试中的问题+回答+得分）
            qa_history = []
            for interview in interviews:
                questions = self.db.query(Question).filter(
                    Question.interview_id == interview.id
                ).order_by(Question.created_at).all()
                for q in questions:
                    answers = self.db.query(Answer).filter(
                        Answer.question_id == q.id
                    ).order_by(Answer.created_at).all()
                    for a in answers:
                        qa_history.append({
                            "question": q.question_text,
                            "answer": a.user_answer or "",
                            "score": a.score or 0,
                        })

            if not qa_history:
                print("[WARN] No Q&A history found, PlannerAgent skipped")
                return {}

            print(f"[INFO] Calling PlannerAgent with {len(qa_history)} Q&A items...")
            plan = planner.generate_plan(qa_history)
            print(f"[INFO] PlannerAgent returned: strengths={len(plan.get('strengths', []))}, weak_points={len(plan.get('weak_points', []))}")

            # 将 PlannerAgent 产出映射为 UserProfile 所需字段
            challenges = []
            for item in plan.get("study_plan", []):
                challenges.append({
                    "id": len(challenges) + 1,
                    "text": item.get("topic", "") + "：" + item.get("suggestion", ""),
                    "priority": item.get("priority", "medium"),
                })

            return {
                "strengths": plan.get("strengths") or [],
                "weaknesses": plan.get("weak_points") or [],
                "recommendations": [
                    item.get("suggestion", "")
                    for item in plan.get("study_plan", [])
                ],
                "challenges": challenges,
                "planner_weak_points": plan.get("weak_points") or [],
            }
        except Exception as e:
            print(f"[ERROR] PlannerAgent failed: {e}")
            traceback.print_exc()
            return {}

    def _generate_default_challenges(self, weaknesses) -> list:
        """当 PlannerAgent 不可用时，基于弱点生成挑战（无弱点则返回空）"""
        if not weaknesses:
            return []
        return [
            {"id": i + 1, "text": f"重点攻克「{w}」相关知识点", "priority": "high" if i == 0 else "medium"}
            for i, w in enumerate(weaknesses[:4])
        ]

    def _empty_profile(self, user: User) -> dict:
        """空用户画像"""
        return {
            "user_id": user.id,
            "username": user.username,
            "total_interviews": 0,
            "average_score": 0.0,
            "radar_data": [
                {"name": "准确性", "score": 0, "fullMark": 100},
                {"name": "完整性", "score": 0, "fullMark": 100},
                {"name": "逻辑性", "score": 0, "fullMark": 100},
                {"name": "表达能力", "score": 0, "fullMark": 100}
            ],
            "category_data": [],
            "trend_data": [],
            "strengths": [],
            "weaknesses": [],
            "recommendations": ["暂无数据，请先完成一次面试"],
            "knowledge_graph": {"nodes": [], "links": []}
        }
    
    def _calculate_category_scores(self, evaluations: List[Evaluation]) -> Dict[str, List[float]]:
        """计算分类分数"""
        category_scores = {}
        for eval in evaluations:
            if eval.category:
                if eval.category not in category_scores:
                    category_scores[eval.category] = []
                category_scores[eval.category].append(eval.score)
        return category_scores
    
    def _analyze_strengths_weaknesses(self, category_scores: Dict[str, List[float]]):
        """分析强项和弱项 —— 返回带描述文本的列表"""
        strengths = []
        weaknesses = []
        for category, scores in category_scores.items():
            if scores:
                avg = sum(scores) / len(scores)
                if avg >= 75:
                    strengths.append(f"{category}（均分 {round(avg, 1)}，表现扎实）")
                elif avg < 60:
                    weaknesses.append(f"{category}（均分 {round(avg, 1)}，需要加强）")
        return strengths, weaknesses
    
    def _generate_radar_data(self, user_id: str) -> List[dict]:
        """生成雷达图数据 —— 从 Answer.dimension_scores 取真实四维度分数"""
        answers = self.db.query(Answer).filter(
            Answer.interview_id.in_(
                self.db.query(Interview.id).filter(
                    Interview.user_id == user_id,
                    Interview.status == "completed"
                )
            ),
            Answer.dimension_scores.isnot(None),
        ).all()

        dim_scores = {"accuracy": [], "completeness": [], "logic": [], "expression": []}
        for a in answers:
            try:
                dims = json.loads(a.dimension_scores)
                for key in dim_scores:
                    if key in dims and dims[key] is not None:
                        dim_scores[key].append(float(dims[key]))
            except (json.JSONDecodeError, TypeError):
                continue

        dim_labels = {
            "accuracy": "准确性",
            "completeness": "完整性",
            "logic": "逻辑性",
            "expression": "表达能力",
        }

        return [
            {
                "name": dim_labels[key],
                "score": round(sum(dim_scores[key]) / len(dim_scores[key]), 1) if dim_scores[key] else 0,
                "fullMark": 100,
            }
            for key in ["accuracy", "completeness", "logic", "expression"]
        ]
    
    def _generate_category_data(self, category_scores: Dict[str, List[float]]) -> List[dict]:
        """生成分类数据"""
        category_data = []
        for category, scores in category_scores.items():
            if scores:
                avg = sum(scores) / len(scores)
                category_data.append({
                    "category": category,
                    "score": round(avg, 1)
                })
        return category_data
    
    def _generate_trend_data(self, interviews: List[Interview]) -> List[dict]:
        """生成趋势数据"""
        trend_data = []
        for interview in interviews[:10]:  # 最近10次
            if interview.overall_score is not None:
                trend_data.append({
                    "date": interview.completed_at.strftime("%Y-%m-%d") if interview.completed_at else "",
                    "score": round(interview.overall_score, 1),
                    "title": f"{interview.target_company or ''} {interview.target_position or ''}".strip() or "面试"
                })
        return trend_data
    
    def _generate_knowledge_graph(
        self, evaluations: List[Evaluation], strengths: List[str], weaknesses: List[str],
        planner_weak_points: Optional[List[str]] = None,
    ) -> dict:
        """生成知识图谱"""
        nodes = []
        links = []
        
        # 核心节点
        nodes.append({"id": "core", "label": "面试能力", "group": "core"})

        # 强项节点（只用前 3 个，优先用简短标签）
        for i, strength in enumerate(strengths[:3]):
            node_id = f"strength_{i}"
            label = strength[:20] + "…" if len(strength) > 20 else strength
            nodes.append({"id": node_id, "label": label, "group": "core"})
            links.append({"source": "core", "target": node_id, "label": "强项"})

        # PlannerAgent 弱项节点（优先使用 AI 识别的弱项）
        if planner_weak_points:
            for i, wp in enumerate(planner_weak_points[:5]):
                node_id = f"planner_weak_{i}"
                label = wp[:20] + "…" if len(wp) > 20 else wp
                nodes.append({"id": node_id, "label": label, "group": "weak"})
                links.append({"source": "core", "target": node_id, "label": "AI 识别弱点"})

        # 传统弱项节点（补充 Planner 未覆盖的）
        for i, weakness in enumerate(weaknesses[:3]):
            node_id = f"weakness_{i}"
            label = weakness[:20] + "…" if len(weakness) > 20 else weakness
            if not planner_weak_points or not any(
                weakness.lower()[:10] in wp.lower() for wp in planner_weak_points
            ):
                nodes.append({"id": node_id, "label": label, "group": "weak"})
                links.append({"source": "core", "target": node_id, "label": "待提升"})
        
        # 如果没有数据，返回空图谱（不再添加示例节点）
        if len(nodes) == 1:
            return {"nodes": [], "links": []}
        
        return {"nodes": nodes, "links": links}
    
    def _generate_recommendations(self, weaknesses: List[str]) -> List[str]:
        """生成学习建议（无弱点则返回空）"""
        if not weaknesses:
            return []
        return [f"建议深入学习{weakness}相关知识" for weakness in weaknesses[:3]]
