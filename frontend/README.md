# Interview Coach 前端

Vue 3 + TypeScript + Tailwind CSS 界面。Express 在端口 3003 承载 Vite 开发中间件或静态资源；所有业务 API 由 Python FastAPI 后端提供。

在本目录执行：

```bash
npm ci
npm run dev
```

默认访问 `http://localhost:3003`，API 默认为 `http://localhost:8000`。需要修改时复制 `.env.example` 为 `.env` 并配置 `VITE_API_BASE_URL`。不要将模型密钥放入 `VITE_` 变量中。

`npm run lint` 执行 TypeScript 检查；`npm run build` 输出前端静态文件和 Express 服务到 `dist/`。运行构建服务时需设置 `NODE_ENV=production` 后执行 `npm start`。

`src/api/` 封装请求和会话，`src/components/` 包含页面与图表，`src/types.ts` 维护接口类型。完整启动与文档见[仓库 README](../README.md)。
