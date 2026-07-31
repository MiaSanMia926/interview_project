# 面试突破手 AI 智能模拟面试系统 — 前端

Vue3 + Vite + TypeScript 前端，通过 `/api/*` 调用后端接口，展示面试配置、
模拟对话、评估雷达图和历史能力画像。

> **技术栈说明**：本项目最初由 Google AI Studio 的 Vibe Coding 工具生成，
> 后端目前是 Node.js/Express + 直接调用 DeepSeek/Gemini API，
> **尚未采用课程要求的 Python + LangChain（LCEL）架构**。本次改动只涉及
> 前端部分，后端接口契约保持不变；后端迁移需要单独排期。

## 本地运行

**前置条件**：Node.js

1. 安装依赖：`npm install`
2. 配置 `.env`（参考 [.env.example](.env.example)）：
   - `DEEPSEEK_API_KEY` / `GEMINI_API_KEY`：后端调用大模型用，未配置时走内置的高保真兜底题库
   - `VITE_API_BASE_URL`：前端调用后端的地址，本地开发留空即可（同源），
     前后端分离部署时填后端的实际域名
3. 启动：`npm run dev`，访问 http://localhost:3000

## 前端目录结构

```
src/
├── api/
│   ├── client.ts      # 统一 API 客户端：收敛所有 /api 请求，区分网络异常/后端异常
│   └── session.ts      # 生成并持久化 sessionId，通过 X-Session-Id 请求头传给后端
├── components/         # HomeView / InterviewView / ReportView / ProfileView 及图表组件
├── types.ts
└── App.vue              # 视图路由（简单 tab 切换）+ 页面级状态
```

## 开发过程材料

- [docs/开发日志.md](./docs/开发日志.md)
- [docs/AI提示词记录.md](./docs/AI提示词记录.md)

这两份是考核要求的交付材料模板，需要按实际开发过程持续补充，不是一次性文档。
