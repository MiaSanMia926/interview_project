# 本次整理验证记录

验证日期：2026-11-04；本地 Python 3.13.9、Node.js 22.20.0。使用当前已安装的 Python 库，未重新安装 requirements 中的完整锁定版本。

| 检查 | 结果 |
| --- | --- |
| Python 源码语法检查 | 通过 |
| RAG 用例 | 3 通过 |
| API 与面试流程用例 | 30 通过、2 失败 |
| 前端 `npm ci --offline --ignore-scripts` | 成功，使用本机缓存 |
| 前端 `npm run lint` | 通过 |
| 前端 `npm run build` | 通过 |

两项失败为 `test_preview_question_stream_returns_chunks` 与 `test_preview_feedback_stream_returns_score_then_chunks`：无模型 Key 时接口返回错误事件，而原测试要求真实流式文本 / 分数。相关后端和测试逻辑均未因目录整理而修改。离线基线命令因此显式排除 `stream`，在线流式行为需配置服务后验证，见 [testing.md](testing.md)。

Windows 受限执行环境的 TestClient 在创建本地 socket pair 时卡住；在允许本地套接字的环境中重新执行后得到上述结果。测试使用 `APP_ENV=testing`，运行库与日志未纳入提交。
