# API 导览

以运行服务的 `/docs` 中自动生成的 OpenAPI 文档为接口字段的准确来源。下表用于快速定位代码：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/health`、`/api/health` | 服务及 Key 是否已配置 |
| POST | `/api/auth/register` | 注册并获得会话令牌 |
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/logout` | 使当前会话失效 |
| GET | `/api/users/{id}/profile` | 用户画像 |
| POST | `/api/interviews` | 创建面试 |
| POST | `/api/interviews/{id}/start` | 开始面试并生成题目 |
| POST | `/api/interviews/{id}/answer` | 提交回答 |
| POST | `/api/interviews/{id}/skip` | 跳过题目 |
| GET | `/api/interviews/{id}/state` | 获取面试状态 |
| GET | `/api/interviews/{id}/summary` | 获取面试总结 |
| POST | `/api/positions/suggest` | 职位推荐 |

登录态请求使用 `Authorization: Bearer <token>`。令牌保存在数据库会话表中，不是 JWT；有效期由认证服务管理。前端提交答案时携带 `questionId`，以避免仅依赖题目游标造成错位。

`/api/health/agents` 会尝试实际调用 Agent，可能触发外部模型请求，不能用作纯离线存活检查。普通 `/health` 只检查 Key 是否存在，不验证模型可用性。
