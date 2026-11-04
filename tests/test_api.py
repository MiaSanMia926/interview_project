"""
API接口单元测试
"""
import pytest
import sys
import os
import uuid
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """创建测试客户端（with 语法触发 lifespan → init_db()）"""
    with TestClient(app) as c:
        yield c


def _register(client, username=None, password="test_pw_123"):
    """注册一个新账号，返回 (headers, user_id, username)。

    背景：注册/登录改造后，/api/users 的免密 get-or-create 接口被移除，
    所有需要登录态的接口都要求携带 Authorization: Bearer <token>；
    这里统一封装，避免每个用例重复写注册+组装请求头的样板代码。
    """
    if username is None:
        username = f"test_{uuid.uuid4().hex[:8]}"
    resp = client.post("/api/auth/register", json={"username": username, "password": password})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    headers = {"Authorization": f"Bearer {data['token']}"}
    return headers, data["userId"], username


class TestHealthAPI:
    """健康检查接口测试"""

    def test_health(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestAuthAPI:
    """注册/登录接口测试"""

    def test_register(self, client):
        """测试注册"""
        username = f"reg_{uuid.uuid4().hex[:8]}"
        response = client.post("/api/auth/register", json={"username": username, "password": "test_pw_123"})
        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert data["username"] == username

    def test_register_duplicate_username(self, client):
        """测试用户名重复注册应被拒绝"""
        username = f"dup_{uuid.uuid4().hex[:8]}"
        client.post("/api/auth/register", json={"username": username, "password": "test_pw_123"})
        response = client.post("/api/auth/register", json={"username": username, "password": "another_pw"})
        assert response.status_code == 400

    def test_register_username_too_short(self, client):
        """测试用户名少于3个字符应被拒绝"""
        response = client.post("/api/auth/register", json={"username": "ab", "password": "test_pw_123"})
        assert response.status_code == 422

    def test_register_password_too_short(self, client):
        """测试密码少于6位应被拒绝"""
        username = f"shortpw_{uuid.uuid4().hex[:8]}"
        response = client.post("/api/auth/register", json={"username": username, "password": "123"})
        assert response.status_code == 422

    def test_login_success(self, client):
        """测试正确的用户名密码可以登录"""
        username = f"login_{uuid.uuid4().hex[:8]}"
        client.post("/api/auth/register", json={"username": username, "password": "correct_pw"})
        response = client.post("/api/auth/login", json={"username": username, "password": "correct_pw"})
        assert response.status_code == 200
        assert "token" in response.json()

    def test_login_wrong_password(self, client):
        """测试密码错误应被拒绝"""
        username = f"wrong_{uuid.uuid4().hex[:8]}"
        client.post("/api/auth/register", json={"username": username, "password": "correct_pw"})
        response = client.post("/api/auth/login", json={"username": username, "password": "wrong_pw"})
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """测试用户名不存在应被拒绝"""
        response = client.post("/api/auth/login", json={"username": "nonexistent_user", "password": "whatever"})
        assert response.status_code == 401

    def test_get_me_requires_token(self, client):
        """测试未登录访问 /api/users/me 应返回 401"""
        response = client.get("/api/users/me")
        assert response.status_code == 401

    def test_get_me_with_token(self, client):
        """测试携带正确 token 可以拿到自己的信息"""
        headers, user_id, username = _register(client)
        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["id"] == user_id
        assert response.json()["username"] == username

    def test_logout_invalidates_token(self, client):
        """测试退出登录后旧 token 不能再用"""
        headers, _, _ = _register(client)
        assert client.get("/api/users/me", headers=headers).status_code == 200

        logout_resp = client.post("/api/auth/logout", headers=headers)
        assert logout_resp.status_code == 204

        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == 401

    def test_expired_token_is_rejected(self, client):
        """测试超过有效期的 token 会被拒绝（并被顺手清理掉）"""
        from datetime import datetime, timedelta
        from backend.database.models import UserSession
        from backend.database.connection import SessionLocal

        headers, _, _ = _register(client)
        token = headers["Authorization"].split(" ", 1)[1]

        # 直接把这条会话的过期时间改到过去，模拟"token 已经过期"
        db = SessionLocal()
        try:
            session = db.query(UserSession).filter(UserSession.token == token).first()
            session.expires_at = datetime.utcnow() - timedelta(seconds=1)
            db.commit()
        finally:
            db.close()

        response = client.get("/api/users/me", headers=headers)
        assert response.status_code == 401


def _create_user_and_interview_headers(client):
    """注册一个账号并创建一场面试，返回 (headers, interview_id)"""
    headers, _, _ = _register(client)
    interview_resp = client.post("/api/interviews", json={
        "userId": "ignored-by-backend",  # 后端会强制用 token 对应的用户，忽略这个字段
        "targetCompany": "字节跳动",
        "targetPosition": "后端工程师",
        "techStack": ["Python", "Redis"]
    }, headers=headers)
    assert interview_resp.status_code == 201, interview_resp.text
    return headers, interview_resp.json()["id"]

def _complete_interview(client, headers, interview_id):
    """让一场面试从开始跑到完全结束，返回最后一次响应的完整数据。

    通过反复提交回答，正确处理 followup/next_question/end 三种分支，
    直到 is_finished 为 True。避免死循环加了一个安全上限。
    """
    start_resp = client.post(f"/api/interviews/{interview_id}/start", headers=headers)
    assert start_resp.status_code == 200
    questions = start_resp.json()["questions"]

    q_index = 0
    last_data = None
    for _ in range(50):  # 安全上限，防止真出bug时死循环卡住测试
        current_qid = questions[q_index]["id"]
        response = client.post(f"/api/interviews/{interview_id}/answer", json={
            "questionId": current_qid,
            "userAnswer": "这是一个较为完整的回答，涉及具体的技术细节和实践经验。"
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        last_data = data

        if data["isFinished"]:
            break
        if data["nextAction"] == "next_question":
            q_index += 1
        # nextAction == "followup" 时不推进 q_index，继续回答同一题的追问

    return last_data

def _collect_sse_events(client, method, url, headers, json_body=None):
    """
    用流式方式请求一个SSE接口，把返回的每一条 `data: {...}` 消息
    解析成dict，收集成列表返回，方便断言里检查事件类型和内容。
    """
    events = []
    with client.stream(method, url, headers=headers, json=json_body) as response:
        assert response.status_code == 200
        for line in response.iter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[len("data: "):]))
    return events

class TestUserIsolationAPI:
    """多用户隔离测试 —— 确认账号之间的数据互相看不到"""

    def test_cannot_view_others_profile(self, client):
        """A 不能看 B 的能力画像"""
        headers_a, user_id_a, _ = _register(client)
        headers_b, user_id_b, _ = _register(client)

        response = client.get(f"/api/users/{user_id_b}/profile", headers=headers_a)
        assert response.status_code == 403

    def test_interview_list_only_shows_own(self, client):
        """A 创建的面试不应出现在 B 的历史记录里"""
        headers_a, _, _ = _register(client)
        headers_b, _, _ = _register(client)

        client.post("/api/interviews", json={
            "userId": "ignored-by-backend",
            "targetCompany": "字节跳动",
            "targetPosition": "后端工程师",
            "techStack": ["Python", "Redis"]
        }, headers=headers_a)

        response_b = client.get("/api/interviews", headers=headers_b)
        assert response_b.status_code == 200
        assert response_b.json()["total"] == 0

    def test_interview_list_pagination(self, client):
        """测试面试列表的分页参数正确生效"""
        headers, _, _ = _register(client)
        for _ in range(3):
            client.post("/api/interviews", json={
                "userId": "ignored-by-backend",
                "targetCompany": "字节跳动",
                "targetPosition": "后端工程师",
                "techStack": ["Python"]
            }, headers=headers)

        response = client.get("/api/interviews?page=1&size=2", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["size"] == 2
        assert len(data["items"]) == 2
    
    def test_cannot_access_others_interview(self, client):
        """A 不能通过 interview_id 访问 B 创建的面试"""
        headers_a, interview_id = _create_user_and_interview_headers(client)
        headers_b, _, _ = _register(client)

        response = client.get(f"/api/interviews/{interview_id}/state", headers=headers_b)
        assert response.status_code == 403


class TestInterviewAPI:
    """面试接口测试"""

    def _create_user_and_interview(self, client):
        """注册账号并创建面试，返回 (headers, interview_id) 供后续请求复用"""
        return _create_user_and_interview_headers(client)

    def test_create_interview(self, client):
        """测试创建面试"""
        headers, interview_id = self._create_user_and_interview(client)
        assert interview_id is not None

    def test_create_interview_requires_login(self, client):
        """测试未登录创建面试应被拒绝"""
        response = client.post("/api/interviews", json={
            "userId": "whatever",
            "targetCompany": "字节跳动",
            "targetPosition": "后端工程师",
            "techStack": ["Python"]
        })
        assert response.status_code == 401

    def test_start_interview(self, client):
        """测试开始面试（返回 InterviewResponse，含 questions 数组）"""
        headers, interview_id = self._create_user_and_interview(client)

        response = client.post(f"/api/interviews/{interview_id}/start", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["currentPhase"] == "TECHNICAL"
        assert data["status"] == "in_progress"
        # start 应一次性生成 MAX_QUESTIONS 道题
        assert "questions" in data
        assert len(data["questions"]) > 0

    def test_submit_answer(self, client):
        """测试提交回答（带 questionId）"""
        headers, interview_id = self._create_user_and_interview(client)
        resp = client.post(f"/api/interviews/{interview_id}/start", headers=headers)
        qid = resp.json()["questions"][0]["id"]

        response = client.post(f"/api/interviews/{interview_id}/answer", json={
            "questionId": qid,
            "userAnswer": "Python是一种解释型语言"
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "evaluation" in data
        assert "score" in data["evaluation"]

    def test_skip_question(self, client):
        """测试跳过问题"""
        headers, interview_id = self._create_user_and_interview(client)
        client.post(f"/api/interviews/{interview_id}/start", headers=headers)

        response = client.post(f"/api/interviews/{interview_id}/skip", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # skip 返回 AnswerResponse（camelCase）
        assert "questionIndex" in data or "question_index" in data

    def test_get_interview_state(self, client):
        """测试获取面试状态"""
        headers, interview_id = self._create_user_and_interview(client)

        response = client.get(f"/api/interviews/{interview_id}/state", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "currentPhase" in data

    def test_get_interview_summary(self, client):
        """测试跑完整个面试流程后，能正确拿到总结报告"""
        headers, interview_id = self._create_user_and_interview(client)
        _complete_interview(client, headers, interview_id)

        response = client.get(f"/api/interviews/{interview_id}/summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "overallScore" in data
        assert 0 <= data["overallScore"] <= 100
        assert "categoryScores" in data
        assert "strengths" in data
        assert "weaknesses" in data
        assert "recommendations" in data
        assert data["answeredQuestions"] > 0

    def test_preview_question_stream_requires_login(self, client):
        """未登录访问SSE出题接口应被拒绝"""
        headers, interview_id = self._create_user_and_interview(client)
        response = client.post(f"/api/interviews/{interview_id}/preview-question/stream")
        assert response.status_code == 401

    def test_preview_question_stream_returns_chunks(self, client):
        """测试SSE出题接口：应该收到多个chunk事件，最后以done结尾"""
        headers, interview_id = self._create_user_and_interview(client)

        events = _collect_sse_events(
            client, "POST",
            f"/api/interviews/{interview_id}/preview-question/stream",
            headers=headers
        )
        assert events, "应该至少收到一条事件"
        chunk_events = [e for e in events if e["type"] == "chunk"]
        assert len(chunk_events) > 1  # 真流式应该是好几块，不是一次性一整段
        assert events[-1]["type"] == "done"

    def test_preview_feedback_stream_returns_score_then_chunks(self, client):
        """测试SSE点评接口：应该先收到score事件（含完整评分），再收到chunk事件，最后done"""
        headers, interview_id = self._create_user_and_interview(client)
        start_resp = client.post(f"/api/interviews/{interview_id}/start", headers=headers)
        qid = start_resp.json()["questions"][0]["id"]

        events = _collect_sse_events(
            client, "POST",
            f"/api/interviews/{interview_id}/preview-feedback/stream",
            headers=headers,
            json_body={"questionId": qid, "userAnswer": "这是一个测试回答，包含一些技术细节。"}
        )
        assert events[0]["type"] == "score"
        assert "score" in events[0]["evaluation"]

        chunk_events = [e for e in events if e["type"] == "chunk"]
        assert len(chunk_events) > 1
        assert events[-1]["type"] == "done"

    def test_preview_stream_ownership_check(self, client):
        """测试他人不能访问你的面试SSE演示接口"""
        headers_a, interview_id = self._create_user_and_interview(client)
        headers_b, _, _ = _register(client)

        response = client.post(
            f"/api/interviews/{interview_id}/preview-question/stream",
            headers=headers_b
        )
        assert response.status_code == 403

    def test_summary_before_completion_rejected(self, client):
        """测试面试还没跑完就调用summary，应返回业务错误而非服务器内部错误"""
        headers, interview_id = self._create_user_and_interview(client)
        # 注意：不调用 _complete_interview，面试还处于 created/in_progress 状态

        response = client.get(f"/api/interviews/{interview_id}/summary", headers=headers)
        assert response.status_code == 400
        assert "尚未完成" in response.json()["detail"] or "未完成" in response.json()["detail"]

    def test_empty_answer_rejected(self, client):
        """测试提交空回答应返回参数校验错误（422），而非被当成正常回答处理"""
        headers, interview_id = self._create_user_and_interview(client)
        resp = client.post(f"/api/interviews/{interview_id}/start", headers=headers)
        qid = resp.json()["questions"][0]["id"]

        response = client.post(f"/api/interviews/{interview_id}/answer", json={
            "questionId": qid,
            "userAnswer": ""
        }, headers=headers)
        assert response.status_code == 422    