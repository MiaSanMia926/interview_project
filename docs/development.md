# 开发指南

## 运行约定

后端与 Python 工具从仓库根目录运行，前端命令从 `frontend/` 运行。保留现有 `backend`、`agents`、`rag` 包路径，避免仅为增加层级而改动全部导入。

Windows 可使用根目录 `start_backend.bat`；它会创建 `venv/`、安装后端依赖并启动开发服务。已经使用 `.venv/` 的开发者可按 README 手动启动。

## 配置

| 变量 | 用途 |
| --- | --- |
| `DEEPSEEK_API_KEY` | Agent API 密钥；兼容 `MIMO_API_KEY` |
| `DEEPSEEK_BASE_URL` | 模型接口根地址；Agent 兼容 `MIMO_API_BASE` |
| `DEEPSEEK_MODEL` | 对话模型；兼容 `MIMO_MODEL` |
| `EMBEDDING_MODEL` | Embedding 模型名称 |
| `APP_ENV` | `development`、`testing`、`production` |
| `DEBUG` | 开发调试开关 |
| `VITE_API_BASE_URL` | 前端配置，放在 `frontend/.env` |

示例显式填写 DeepSeek 地址和模型，以覆盖代码中的 MiMo 默认值。Embedding 与聊天模型不是同一种接口能力；提供聊天服务不代表支持 `text-embedding-3-small`，不支持时会走本地降级。

`APP_ENV=testing` 使用 `data/test.db`，默认开发使用 `data/interview.db`。当前数据库连接包含 SQLite 专用参数；配置代码虽有生产 `DATABASE_URL` 入口，未经适配不能据此宣称已支持其他数据库。

## 题库维护

维护 `data/questions/` 的 JSON 后，可运行：

```bash
python scripts/load_questions.py
```

工具清洗题库并在 `data/chroma/` 写入可重建的索引。不要提交缓存目录、数据库或日志。

## 前端检查

```bash
cd frontend
npm ci
npm run lint
npm run build
```

配置变化后重启开发服务。API 地址变化时，同时检查后端 CORS 允许的来源。
