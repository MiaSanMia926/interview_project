# 面试突破助手 — Interview Coach

基于 **FastAPI + Vue 3 + RAG + Multi-Agent** 架构的智能面试模拟系统。
通过构建真实面试题库、多 Agent 协作、LangGraph 状态机驱动面试流程，
解决传统面试练习中"题目质量不稳定、评估主观、无法针对性改进"等痛点。

---

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端 | Vue 3 + Tailwind CSS | 用户界面 |
| 前端构建 | Vite + tsx (Express dev server) | 开发 & 构建 |
| 后端 API | FastAPI + Uvicorn | RESTful 接口 |
| LLM 框架 | LangChain + LangGraph | Agent 编排 & 状态机 |
| 检索 | 自研 TF-IDF 引擎 | 本地知识库检索（无外部依赖） |
| 数据存储 | SQLite + SQLAlchemy | 业务数据持久化 |
| LLM | DeepSeek / MiMo（OpenAI 兼容接口） | 问题生成 & 评估 |

## 项目结构

```
interview-coach/
├── backend/              # FastAPI 后端
│   ├── api/routes/       # REST 路由
│   ├── database/         # SQLAlchemy 模型 & 连接
│   ├── schemas/          # Pydantic 请求/响应模型
│   ├── services/         # 业务逻辑层
│   └── config.py         # 配置
├── agents/               # Multi-Agent 模块
│   ├── interviewer.py    # 面试官 Agent（生成问题 & 追问）
│   ├── evaluator.py      # 评估 Agent（多维度评分）
│   ├── orchestrator.py   # LangGraph 状态机协调器
│   ├── knowledge.py      # 知识检索 Agent
│   └── memory.py         # 对话记忆窗口
├── rag/                  # RAG 引擎
│   ├── engine.py         # TF-IDF 检索 & MMR 重排序
│   ├── loader.py         # 题库加载 & 清洗
│   └── splitter.py       # 文本分块
├── frontend/src/         # Vue 3 组件
│   └── api/client.ts     # API 客户端（默认连 localhost:8000）
├── data/                 # 运行时数据
│   ├── questions/        # 题库 JSON
│   └── chroma/           # 检索索引缓存
└── tests/                # 测试
```

## 快速开始

### 1. 配置环境变量

在项目根目录创建 `.env`：

```env
DEEPSEEK_API_KEY=你的API密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```

### 2. 安装 Python 依赖

```bash
pip install -r backend/requirements.txt
```

### 3. 启动后端

```bash
# 方式一：启动脚本
start_backend.bat

# 方式二：手动
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 启动前端（开发模式）

```bash
cd frontend
npm install
npm run dev
```

### 5. 访问

- API 服务：http://localhost:8000
- Swagger 文档：http://localhost:8000/docs
- 前端页面：http://localhost:3003

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/users` | 创建用户 |
| GET | `/api/users/{id}/profile` | 用户画像 |
| POST | `/api/interviews` | 创建面试 |
| POST | `/api/interviews/{id}/start` | 开始面试（生成全部题目） |
| POST | `/api/interviews/{id}/answer` | 提交回答 |
| POST | `/api/interviews/{id}/skip` | 跳过当前题 |
| GET | `/api/interviews/{id}/state` | 面试状态 |
| GET | `/api/interviews/{id}/summary` | 面试总结 |
| GET | `/api/interviews` | 面试列表 |
| POST | `/api/positions/suggest` | 职位推荐 |

## 架构要点

- **RAG 本地检索**：题库存储在 `data/questions/`，启动时加载并建立 TF-IDF 索引，无需外部向量数据库
- **try-catch 安全降级**：Agent/RAG 调用失败时自动回退到占位实现，保证无 Key 或断网环境下也可使用
- **一次生成全部题目**：`start` 接口一次性生成 N 道题（默认 3 道），前端侧边栏/进度卡依赖此数组
- **questionId 双向校验**：提交答案时前端携带 `questionId`，后端精确查找，不再依赖 `current_question_index`
