# 成员E指引 - 测试与文档专员

> **角色**：测试、文档与答辩汇报专员
> **职责**：测试、文档、答辩PPT

---

## 一、你的任务

### 1.1 核心任务

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 编写单元测试 | 测试各个模块 |
| P0 | 全链路测试 | 测试完整流程 |
| P0 | 编写技术文档 | 项目说明书 |
| P0 | 制作答辩PPT | 结项汇报 |
| P1 | 性能测试 | 响应时间、并发 |
| P1 | LangSmith追踪 | Agent调用分析 |

### 1.2 交付物

| 文件 | 说明 | 必须 |
|------|------|------|
| `tests/test_api.py` | API接口测试 | ✅ |
| `tests/test_agent.py` | Agent测试 | ✅ |
| `tests/test_rag.py` | RAG测试 | ✅ |
| `tests/test_integration.py` | 集成测试 | ✅ |
| `docs/TEST_CASES.md` | 测试用例 | ✅ |
| `docs/TEST_REPORT.md` | 测试报告 | ✅ |
| `docs/USER_MANUAL.md` | 用户手册 | ✅ |
| `docs/TECHNICAL_DOC.md` | 技术文档 | ✅ |
| `presentation.pptx` | 答辩PPT | ✅ |

---

## 二、测试指南

### 2.1 API接口测试

```python
# tests/test_api.py
import requests
import pytest

BASE_URL = "http://localhost:8000"

class TestHealth:
    def test_health_check(self):
        """测试健康检查接口"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

class TestUsers:
    def test_create_user(self):
        """测试创建用户"""
        response = requests.post(f"{BASE_URL}/api/users", json={
            "username": "test_user_123"
        })
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["username"] == "test_user_123"
    
    def test_create_duplicate_user(self):
        """测试创建重复用户"""
        # 先创建一个用户
        requests.post(f"{BASE_URL}/api/users", json={"username": "dup_user"})
        # 再创建同名用户
        response = requests.post(f"{BASE_URL}/api/users", json={"username": "dup_user"})
        assert response.status_code == 400
    
    def test_get_user(self):
        """测试获取用户"""
        # 先创建
        create_resp = requests.post(f"{BASE_URL}/api/users", json={"username": "get_user"})
        user_id = create_resp.json()["id"]
        
        # 再获取
        response = requests.get(f"{BASE_URL}/api/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["id"] == user_id
    
    def test_get_nonexistent_user(self):
        """测试获取不存在的用户"""
        response = requests.get(f"{BASE_URL}/api/users/nonexistent")
        assert response.status_code == 404

class TestInterviews:
    @pytest.fixture
    def user_id(self):
        """创建测试用户"""
        response = requests.post(f"{BASE_URL}/api/users", json={"username": "interview_user"})
        return response.json()["id"]
    
    def test_create_interview(self, user_id):
        """测试创建面试"""
        response = requests.post(f"{BASE_URL}/api/interviews", json={
            "user_id": user_id,
            "target_company": "字节跳动",
            "target_position": "后端工程师",
            "tech_stack": ["Python", "Redis"]
        })
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "created"
        return data["id"]
    
    def test_start_interview(self, user_id):
        """测试开始面试"""
        # 创建面试
        create_resp = requests.post(f"{BASE_URL}/api/interviews", json={
            "user_id": user_id,
            "tech_stack": ["Python"]
        })
        interview_id = create_resp.json()["id"]
        
        # 开始面试
        response = requests.post(f"{BASE_URL}/api/interviews/{interview_id}/start")
        assert response.status_code == 200
        data = response.json()
        assert data["current_phase"] == "TECHNICAL"
        assert data["next_action"] == "answer"
        assert "next_message" in data
    
    def test_submit_answer(self, user_id):
        """测试提交回答"""
        # 创建并开始面试
        create_resp = requests.post(f"{BASE_URL}/api/interviews", json={"user_id": user_id})
        interview_id = create_resp.json()["id"]
        requests.post(f"{BASE_URL}/api/interviews/{interview_id}/start")
        
        # 提交回答
        response = requests.post(f"{BASE_URL}/api/interviews/{interview_id}/answer", json={
            "user_answer": "Python是一种解释型语言..."
        })
        assert response.status_code == 200
        data = response.json()
        assert "evaluation" in data
        assert "score" in data["evaluation"]
    
    def test_skip_question(self, user_id):
        """测试跳过问题"""
        # 创建并开始面试
        create_resp = requests.post(f"{BASE_URL}/api/interviews", json={"user_id": user_id})
        interview_id = create_resp.json()["id"]
        requests.post(f"{BASE_URL}/api/interviews/{interview_id}/start")
        
        # 跳过
        response = requests.post(f"{BASE_URL}/api/interviews/{interview_id}/skip")
        assert response.status_code == 200
        data = response.json()
        assert data["question_index"] == 1
    
    def test_get_interview_state(self, user_id):
        """测试获取面试状态"""
        create_resp = requests.post(f"{BASE_URL}/api/interviews", json={"user_id": user_id})
        interview_id = create_resp.json()["id"]
        
        response = requests.get(f"{BASE_URL}/api/interviews/{interview_id}/state")
        assert response.status_code == 200
        assert "status" in response.json()
```

### 2.2 Agent测试

```python
# tests/test_agent.py
import pytest
from agents.interviewer import InterviewerAgent
from agents.evaluator import EvaluatorAgent

class TestInterviewerAgent:
    @pytest.fixture
    def agent(self):
        return InterviewerAgent()
    
    def test_generate_question(self, agent):
        """测试生成问题"""
        question = agent.generate_question(
            target_company="字节跳动",
            target_position="后端工程师",
            tech_stack=["Python", "Redis"],
            question_index=0,
            previous_qa=[]
        )
        assert isinstance(question, str)
        assert len(question) > 10
    
    def test_generate_followup(self, agent):
        """测试生成追问"""
        followup = agent.generate_followup(
            original_question="请介绍Redis持久化",
            user_answer="Redis有RDB和AOF两种方式",
            evaluation_result={"score": 75},
            followup_count=0
        )
        assert isinstance(followup, str)
        assert len(followup) > 10

class TestEvaluatorAgent:
    @pytest.fixture
    def agent(self):
        return EvaluatorAgent()
    
    def test_evaluate(self, agent):
        """测试评估"""
        result = agent.evaluate(
            question="请介绍Redis持久化",
            user_answer="Redis有RDB和AOF两种方式，RDB是快照，AOF是日志追加",
            question_type="technical",
            category="Redis"
        )
        # 验证返回格式
        assert "score" in result
        assert "dimensions" in result
        assert "strengths" in result
        assert "improvements" in result
        assert "feedback" in result
        
        # 验证分数范围
        assert 0 <= result["score"] <= 100
        assert 0 <= result["dimensions"]["accuracy"] <= 100
        assert 0 <= result["dimensions"]["completeness"] <= 100
```

### 2.3 RAG测试

```python
# tests/test_rag.py
import pytest
from rag.engine import RAGEngine

class TestRAGEngine:
    @pytest.fixture
    def engine(self):
        return RAGEngine()
    
    def test_search(self, engine):
        """测试检索"""
        results = engine.search(
            query="Redis持久化",
            k=3
        )
        assert isinstance(results, list)
        assert len(results) > 0
        
        # 验证返回格式
        for r in results:
            assert "question" in r
            assert "category" in r
    
    def test_search_with_filter(self, engine):
        """测试带过滤的检索"""
        results = engine.search(
            query="缓存",
            tech_stack=["Redis"],
            k=3
        )
        assert isinstance(results, list)
```

### 2.4 集成测试

```python
# tests/test_integration.py
import requests

BASE_URL = "http://localhost:8000"

def test_full_interview_flow():
    """完整面试流程测试"""
    # 1. 创建用户
    user_resp = requests.post(f"{BASE_URL}/api/users", json={"username": "integration_user"})
    assert user_resp.status_code == 201
    user_id = user_resp.json()["id"]
    
    # 2. 创建面试
    interview_resp = requests.post(f"{BASE_URL}/api/interviews", json={
        "user_id": user_id,
        "target_company": "字节跳动",
        "target_position": "后端工程师",
        "tech_stack": ["Python", "Redis"]
    })
    assert interview_resp.status_code == 201
    interview_id = interview_resp.json()["id"]
    
    # 3. 开始面试
    start_resp = requests.post(f"{BASE_URL}/api/interviews/{interview_id}/start")
    assert start_resp.status_code == 200
    assert start_resp.json()["next_action"] == "answer"
    
    # 4. 回答问题
    for i in range(5):  # 回答5道题
        answer_resp = requests.post(f"{BASE_URL}/api/interviews/{interview_id}/answer", json={
            "user_answer": f"这是第{i+1}个回答，关于技术的理解..."
        })
        assert answer_resp.status_code == 200
        
        data = answer_resp.json()
        if data["is_finished"]:
            break
        
        if data["next_action"] == "next_question":
            continue
    
    # 5. 获取总结
    summary_resp = requests.get(f"{BASE_URL}/api/interviews/{interview_id}/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert "overall_score" in summary
    assert "category_scores" in summary
```

---

## 三、测试运行

### 3.1 安装依赖

```bash
pip install pytest requests
```

### 3.2 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_api.py -v

# 运行并显示覆盖率
pytest tests/ -v --cov=backend
```

---

## 四、文档编写

### 4.1 测试报告模板

```markdown
# 测试报告

## 测试概览
- 测试时间：2026-07-XX
- 测试环境：Windows 11, Python 3.11
- 测试人员：成员E

## 测试结果

| 模块 | 测试用例数 | 通过数 | 失败数 | 通过率 |
|------|-----------|--------|--------|--------|
| API接口 | 15 | 15 | 0 | 100% |
| Agent | 8 | 7 | 1 | 87.5% |
| RAG | 5 | 5 | 0 | 100% |
| 集成测试 | 3 | 3 | 0 | 100% |

## 发现的问题
1. Agent评估偶尔回复格式不正确（已修复）
2. ...

## 结论
系统整体稳定，核心功能正常。
```

### 4.2 用户手册模板

```markdown
# 用户手册

## 快速开始
1. 启动后端：`start_backend.bat`
2. 启动前端：`streamlit run frontend/app.py`
3. 访问：http://localhost:8501

## 功能说明
### 创建面试
1. 输入用户名
2. 选择目标公司和职位
3. 选择技术栈
4. 点击"开始面试"

### 回答问题
1. 阅读问题
2. 在输入框输入回答
3. 点击"提交"或按回车
4. 查看评估结果

### 查看报告
面试完成后，点击"查看报告"查看详细分析。
```

### 4.3 技术文档模板

```markdown
# 技术文档

## 架构设计
（插入架构图）

## 技术栈
- LLM: MiMo
- 框架: LangChain + LangGraph
- 向量数据库: ChromaDB
- 业务数据库: SQLite
- Web框架: FastAPI
- 前端: Streamlit

## 核心模块
### RAG系统
...

### Agent系统
...

### 状态机
...

## API接口
详见 `docs/API.md`
```

---

## 五、答辩PPT大纲

### 5.1 建议结构（10页）

| 页码 | 内容 | 时间 |
|------|------|------|
| 1 | 封面 | - |
| 2 | 项目背景与痛点 | 1分钟 |
| 3 | 技术架构 | 2分钟 |
| 4 | 核心功能演示1：RAG检索 | 1分钟 |
| 5 | 核心功能演示2：Agent协作 | 1分钟 |
| 6 | 核心功能演示3：状态机 | 1分钟 |
| 7 | 核心功能演示4：评估系统 | 1分钟 |
| 8 | 技术亮点 | 1分钟 |
| 9 | 团队分工 | 0.5分钟 |
| 10 | 总结与展望 | 0.5分钟 |

### 5.2 PPT要点

**痛点页**：
- 列出5个痛点
- 说明为什么直接用大模型解决不了

**架构页**：
- 插入架构图
- 说明6层架构

**演示页**：
- 截图或录屏
- 强调技术亮点

**亮点页**：
- RAG vs 直接生成
- Multi-Agent vs 单Agent
- 状态机 vs 简单对话
- 量化评估 vs 主观打分

---

## 六、协作接口

### 6.1 你依赖的

| 来源 | 内容 | 位置 |
|------|------|------|
| 成员A | API接口文档 | `docs/API.md` |
| 成员B | Agent接口文档 | `docs/GUIDE_FOR_B.md` |
| 成员C | RAG接口文档 | `docs/GUIDE_FOR_C.md` |
| 成员D | 界面截图 | `frontend/` |

### 6.2 依赖你的

| 来源 | 内容 |
|------|------|
| 全员 | 测试报告、PPT |

---

## 七、开发顺序

| 步骤 | 任务 | 预计时间 |
|------|------|----------|
| 1 | 编写API测试用例 | 1天 |
| 2 | 编写Agent测试用例 | 0.5天 |
| 3 | 编写RAG测试用例 | 0.5天 |
| 4 | 执行测试并记录问题 | 1天 |
| 5 | 编写测试报告 | 0.5天 |
| 6 | 编写技术文档 | 1天 |
| 7 | 制作PPT | 1天 |
| 8 | 模拟答辩 | 0.5天 |

**总计**：约6天

---

**文档版本**：v1.0
**后端工程师**：成员A
