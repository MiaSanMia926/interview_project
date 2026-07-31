/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 *
 * Express 开发服务器 —— 仅提供 Vite 中间件，不包含任何 API 路由。
 * 前端所有 API 请求由 FastAPI 后端（端口 8000）处理。
 */

import express from 'express';
import path from 'path';
import { createServer as createViteServer } from 'vite';

const PORT = 3003;
const app = express();

// -------------------------------------------------------------
// VITE OR STATIC ASSETS SERVING MIDDLEWARE
// -------------------------------------------------------------
async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Frontend server running on http://0.0.0.0:${PORT}`);
    console.log(`API requests proxied to FastAPI (http://localhost:8000)`);
  });
}

startServer();
