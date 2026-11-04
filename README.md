# 面试突破助手 · Interview Coach

基于 FastAPI、Vue 3、RAG 与多个面试 Agent 的模拟面试应用，覆盖账号登录、面试配置、问答与追问、评估报告和历史能力画像。

## 核心能力

- **模拟面试流程**：创建面试、批量生成题目、提交或跳过回答、生成总结。
- **面试 Agent**：面试官、评估、规划、知识检索与记忆模块；含 LangGraph 编排实现。
- **题库检索**：优先使用 Embedding + Chroma，初始化或调用失败时回退到本地 TF-IDF 检索。
- **结果展示**：Vue 页面展示评估、雷达图、知识图谱与历史趋势。
- **账号与会话**：bcrypt 密码哈希，数据库保存有过期时间的会话令牌。

## 技术栈

| 层次 | 技术 |
| --- | --- |
| 页面 | Vue 3、TypeScript、Tailwind CSS |
| 前端开发服务 | Vite + Express（端口 3003，只托管前端） |
| API 与数据 | FastAPI、Pydantic、SQLAlchemy、SQLite |
| AI 与编排 | LangChain、LangGraph、OpenAI 兼容接口 |
| 检索 | Chroma / Embedding、TF-IDF、MMR |

## 目录结构

```text
.
├── backend/              # API 路由、配置、数据库、业务服务
├── agents/               # 面试官、评估、规划、记忆和编排
├── rag/                  # 题库加载、检索、重排与标准答案
├── frontend/             # Vue 应用与前端开发服务
├── data/                 # 受控题库；运行时生成数据库、日志和索引
├── tests/                # API、RAG、流程与在线 Agent 测试
├── scripts/              # 题库索引构建与手动冒烟工具
├── docs/                 # 架构、开发、测试与 API 说明
│   └── archive/          # 原开发日志、课程交付和答辩材料
├── .env.example
└── start_backend.bat     # Windows 后端启动入口
```

## 快速开始

建议使用 Python 3.12、Node.js 22。在仓库根目录执行：

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS / Linux: source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

复制根目录 `.env.example` 为 `.env`，按实际模型服务填写 Key、地址和模型。未填写 Key 时可检查账号、API 和降级路径，但不能据此验证真实 AI 生成质量。

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

另开终端：

```bash
cd frontend
npm ci
npm run dev
```

- 前端：`http://localhost:3003`
- API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`

数据库、表和日志目录会自动创建，无需复制旧数据库。前端默认直连 `http://localhost:8000`；需改地址时，复制 `frontend/.env.example` 为 `frontend/.env` 并设置 `VITE_API_BASE_URL`。模型 Key 只放在后端环境中。

## 开发文档

- [架构与模块职责](docs/architecture.md)
- [环境配置与日常开发](docs/development.md)
- [API 导览](docs/api.md)
- [测试方式与覆盖边界](docs/testing.md)
- [数据约定](data/README.md)
- [目录迁移记录](docs/migration.md)
- [贡献指南](CONTRIBUTING.md)

项目当前采用本地 SQLite 和开发服务。真实模型效果、负载能力与生产部署需另行验证；历史报告保留在归档中，不作为当前版本验证结果。

本次目录整理的实际检查结果见[验证记录](docs/validation.md)。
