# 项目结构说明

---

## 目录结构

```
interview-coach/
├── PROJECT_DOCUMENT.md          # 项目主文档
├── start_backend.bat            # 后端启动脚本
├── test_api.py                  # API测试脚本
│
├── backend/                     # 后端代码（成员A）
│   ├── main.py                  # FastAPI入口
│   ├── config.py                # 配置文件
│   ├── requirements.txt         # Python依赖
│   │
│   ├── database/                # 数据库模块
│   │   ├── __init__.py
│   │   ├── connection.py        # SQLite连接
│   │   └── models.py            # SQLAlchemy模型
│   │
│   ├── api/                     # API模块
│   │   ├── __init__.py
│   │   ├── deps.py              # 依赖注入
│   │   └── routes/              # 路由
│   │       ├── __init__.py
│   │       ├── health.py        # 健康检查
│   │       ├── users.py         # 用户接口
│   │       └── interviews.py    # 面试接口
│   │
│   ├── schemas/                 # Pydantic模型
│   │   ├── __init__.py
│   │   ├── user.py              # 用户Schema
│   │   ├── interview.py         # 面试Schema
│   │   └── common.py            # 通用Schema
│   │
│   ├── services/                # 业务逻辑
│   │   ├── __init__.py
│   │   ├── user_service.py      # 用户服务
│   │   └── interview_service.py # 面试服务
│   │
│   └── utils/                   # 工具函数
│       ├── __init__.py
│       └── helpers.py           # 辅助函数
│
├── agents/                      # Agent代码（成员B）
│   ├── __init__.py
│   ├── base.py                  # Agent基类（DeepSeek LLM封装）
│   ├── orchestrator.py          # LangGraph 协调器
│   ├── interviewer.py           # 面试官Agent
│   ├── evaluator.py             # 评估Agent
│   ├── knowledge.py             # 知识检索Agent（无LLM依赖）
│   ├── planner.py               # 学习规划Agent（P2可选）
│   └── memory.py                # 对话记忆窗口管理

├── rag/                         # RAG代码（成员C）
│   ├── __init__.py
│   ├── engine.py                # TF-IDF检索引擎
│   ├── loader.py                # 题库加载与清洗
│   ├── splitter.py              # 文本分块（预留）
│   └── standard_answers.py      # 标准答案库管理

├── frontend/                    # 前端代码（成员D）
│   ├── package.json             # 依赖
│   ├── server.ts                # Express开发服务器（开发用）
│   ├── vite.config.ts           # Vite构建配置
│   ├── src/                     # Vue 3 组件
│   │   ├── api/
│   │   │   ├── client.ts        # API客户端（默认连8000端口）
│   │   │   └── session.ts       # 会话标识工具
│   │   ├── components/          # 视图组件
│   │   └── types.ts             # TypeScript类型定义
│   └── index.html               # 入口页面
│
├── tests/                       # 测试代码（成员E）
│   └── ...
│
├── data/                        # 数据目录
│   └── interview.db             # SQLite数据库（运行时生成）
│
└── docs/                        # 文档目录
    ├── API.md                   # 接口文档
    └── DATABASE_SCHEMA.md       # 数据库Schema
```

---

## 各成员工作目录

| 成员 | 角色 | 工作目录 | 主要产出 |
|------|------|----------|----------|
| 成员A | 后端工程师 | `backend/` | FastAPI接口、数据库 |
| 成员B | Agent工程师 | `agents/` | LangChain Agent |
| 成员C | RAG工程师 | `rag/` | RAG系统、题库 |
| 成员D | 前端工程师 | `frontend/` | Streamlit界面 |
| 成员E | 测试专员 | `tests/` | 测试用例 |

---

## 代码集成方式

**方式**：同一项目，直接调用

后端直接 import 其他成员的代码：

```python
# 调用Agent（成员B）
from agents.interviewer import InterviewerAgent
from agents.evaluator import EvaluatorAgent

# 调用RAG（成员C）
from rag.engine import RAGEngine
```

---

## 启动方式

### 后端服务

```bash
# 方式1：使用启动脚本
start_backend.bat

# 方式2：手动启动
cd interview-coach
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 访问地址

- **API服务**：http://localhost:8000
- **Swagger文档**：http://localhost:8000/docs
- **ReDoc文档**：http://localhost:8000/redoc

---

## 测试

```bash
# 运行API测试
python test_api.py
```

---

**文档版本**：v1.0
