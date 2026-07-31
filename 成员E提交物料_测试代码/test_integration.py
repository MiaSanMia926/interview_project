"""
全链路集成测试 —— 验证"一个真实用户从注册到拿到面试报告"这条最长的业务链路
是否端到端跑得通。

和 test_api.py 的区别：test_api.py 侧重单个接口/单个校验点是否正确；
这里侧重完整流程串起来是否顺畅，包括跨越登录、创建、答题、总结这几个
阶段之间状态是否正确传递。
"""
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from backend.main import app


def _register_and_login(client) -> dict:
    """注册一个新账号，返回登录态需要的完整信息"""
    username = f"integration_{uuid.uuid4().hex[:8]}"
    password = "test_pw_123456"
    resp = client.post("/api/auth/register", json={"username": username, "password": password})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    return {
        "headers": {"Authorization": f"Bearer {data['token']}"},
        "user_id": data["userId"],
        "username": username,
        "password": password,
    }


class TestFullInterviewFlow:
    """完整面试流程：注册 → 创建 → 开始 → 连续答题 → 查看总结"""

    def test_full_interview_flow_end_to_end(self):
        with TestClient(app) as client:
            account = _register_and_login(client)
            headers = account["headers"]

            # 1. 创建面试
            create_resp = client.post("/api/interviews", json={
                "userId": "ignored-by-backend",
                "targetCompany": "字节跳动",
                "targetPosition": "后端工程师",
                "techStack": ["Python", "Redis", "MySQL"]
            }, headers=headers)
            assert create_resp.status_code == 201, create_resp.text
            interview_id = create_resp.json()["id"]
            assert create_resp.json()["status"] == "created"

            # 2. 开始面试 —— 应一次性生成全部题目
            start_resp = client.post(f"/api/interviews/{interview_id}/start", headers=headers)
            assert start_resp.status_code == 200, start_resp.text
            start_data = start_resp.json()
            assert start_data["status"] == "in_progress"
            assert start_data["currentPhase"] == "TECHNICAL"
            questions = start_data["questions"]
            assert len(questions) > 0
            total_questions = len(questions)

            # 3. 连续提交回答，正确处理 followup/next_question/end 三种分支
            q_index = 0
            answered_count = 0
            is_finished = False
            for _ in range(50):  # 安全上限，避免真出bug时死循环卡住整条流水线
                current_qid = questions[q_index]["id"]
                answer_resp = client.post(f"/api/interviews/{interview_id}/answer", json={
                    "questionId": current_qid,
                    "userAnswer": "这是一个较为完整的技术回答，涉及具体实现细节、性能考量和实际项目中的权衡取舍。"
                }, headers=headers)
                assert answer_resp.status_code == 200, answer_resp.text
                data = answer_resp.json()
                answered_count += 1

                assert "evaluation" in data
                assert data["evaluation"] is not None
                assert 0 <= data["evaluation"]["score"] <= 100
                assert data["nextAction"] in ("followup", "next_question", "end")

                if data["isFinished"]:
                    is_finished = True
                    break
                if data["nextAction"] == "next_question":
                    q_index += 1
                    assert q_index < total_questions

            assert is_finished, "面试应该在安全上限内正常结束，而不是一直卡在追问循环里"

            # 4. 查看总结报告，验证结构完整、数值合理
            summary_resp = client.get(f"/api/interviews/{interview_id}/summary", headers=headers)
            assert summary_resp.status_code == 200, summary_resp.text
            summary = summary_resp.json()
            assert summary["status"] == "completed"
            assert summary["totalQuestions"] == total_questions
            assert summary["answeredQuestions"] > 0
            assert 0 <= summary["overallScore"] <= 100
            assert isinstance(summary["categoryScores"], dict)
            assert isinstance(summary["strengths"], list)
            assert isinstance(summary["weaknesses"], list)
            assert isinstance(summary["recommendations"], list)

            # 5. 面试结束后，这场面试应该出现在自己的历史记录里
            history_resp = client.get("/api/interviews", headers=headers)
            assert history_resp.status_code == 200
            history_ids = [item["id"] for item in history_resp.json()["items"]]
            assert interview_id in history_ids

    def test_flow_blocked_at_every_step_without_login(self):
        """验证流程里任何一步缺少登录令牌，都会在对应环节被拒绝，而不是只在第一步生效"""
        with TestClient(app) as client:
            account = _register_and_login(client)
            headers = account["headers"]

            create_resp = client.post("/api/interviews", json={
                "userId": "ignored", "targetCompany": "测试公司",
                "targetPosition": "测试职位", "techStack": ["Python"]
            }, headers=headers)
            interview_id = create_resp.json()["id"]

            # 不带 headers 逐一尝试后续每个步骤，都应该被 401 拦截
            assert client.post(f"/api/interviews/{interview_id}/start").status_code == 401
            client.post(f"/api/interviews/{interview_id}/start", headers=headers)  # 用正确身份真正开始
            assert client.post(f"/api/interviews/{interview_id}/answer", json={
                "questionId": "whatever", "userAnswer": "test"
            }).status_code == 401
            assert client.post(f"/api/interviews/{interview_id}/skip").status_code == 401
            assert client.get(f"/api/interviews/{interview_id}/state").status_code == 401
            assert client.get(f"/api/interviews/{interview_id}/summary").status_code == 401
            assert client.get("/api/interviews").status_code == 401

    def test_logout_does_not_lose_created_data(self):
        """验证退出登录后重新登录，之前创建的数据（面试记录）依然完整可见"""
        with TestClient(app) as client:
            account = _register_and_login(client)
            headers = account["headers"]

            create_resp = client.post("/api/interviews", json={
                "userId": "ignored", "targetCompany": "测试公司",
                "targetPosition": "测试职位", "techStack": ["Python"]
            }, headers=headers)
            interview_id = create_resp.json()["id"]

            # 退出登录
            logout_resp = client.post("/api/auth/logout", headers=headers)
            assert logout_resp.status_code == 204

            # 旧令牌应该失效
            assert client.get("/api/interviews", headers=headers).status_code == 401

            # 用同一账号密码重新登录
            login_resp = client.post("/api/auth/login", json={
                "username": account["username"], "password": account["password"]
            })
            assert login_resp.status_code == 200
            new_headers = {"Authorization": f"Bearer {login_resp.json()['token']}"}

            # 之前创建的面试记录应该依然完整存在
            history_resp = client.get("/api/interviews", headers=new_headers)
            assert history_resp.status_code == 200
            history_ids = [item["id"] for item in history_resp.json()["items"]]
            assert interview_id in history_ids