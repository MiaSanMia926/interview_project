# 面试突破助手 - 启动说明

## 环境要求

- **Python** 3.10+
- **Node.js** 18+
- **npm** 9+

## 1. 配置 API Key

将三处 `.env.example` 重命名为 `.env` 并填入你的 DeepSeek API Key：

```bash
# 项目根目录、backend/、frontend/ 下各有一份 .env.example
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

然后编辑三个 `.env` 文件，把 `YOUR_DEEPSEEK_API_KEY` 替换为真实 Key：

```
DEEPSEEK_API_KEY=sk-xxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

> 也可以使用其他兼容 OpenAI 格式的 API（如 MIMO），只需修改 `DEEPSEEK_BASE_URL` 和 `DEEPSEEK_MODEL`。

## 2. 安装依赖

```bash
# Python 后端
python -m venv .venv
source .venv/Scripts/activate   # Windows
# 或 source .venv/bin/activate  # macOS/Linux
pip install -r backend/requirements.txt

# 前端
cd frontend
npm install
cd ..
```

## 3. 启动后端 (FastAPI)

```bash
# 激活虚拟环境后
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001
```

启动后访问：
- API 文档：http://localhost:8001/docs
- 健康检查：http://localhost:8001/health

> **注意**：不要使用 `--reload` 参数（Windows 下会产生僵尸进程）。
> 如果端口被占用，换一个端口号即可。

## 4. 启动前端 (Vue + Express)

```bash
cd frontend
npm run dev
```

启动后访问：http://localhost:3003

## 5. 使用

1. 打开浏览器访问 http://localhost:3003
2. 在首页填写目标公司、目标职位、技术栈
3. 点击"开始面试"，AI 自动生成 3 道面试题
4. 依次回答每题（每题有追问环节）
5. 完成 3 题后查看"大厂诊断书"

## 架构说明

```
浏览器 (localhost:3003)
  └── Express (前端页面 + Vite HMR)
       └── Vue 前端 → API 请求 → FastAPI (localhost:8001)
                                    ├── InterviewerAgent (出题/追问)
                                    ├── EvaluatorAgent (评分)
                                    ├── PlannerAgent (诊断书)
                                    ├── KnowledgeAgent (RAG 检索)
                                    └── SQLite (数据持久化)
```

## 常见问题

**Q: 提示 "AI 评估服务暂时不可用"？**
A: 检查三处 `.env` 中的 `DEEPSEEK_API_KEY` 是否配置正确。

**Q: 前端页面空白？**
A: 确认前端 `frontend/.env` 中 `VITE_API_BASE_URL` 指向正确的后端地址（默认 http://localhost:8001）。

**Q: 出题是占位题而不是 AI 出题？**
A: 检查后端控制台日志，确认 `InterviewerAgent` 初始化成功。
