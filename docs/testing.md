# 测试指南

安装后端依赖后，在仓库根目录运行无需真实 Key 的基线测试：

```bash
python -m pytest tests/test_rag.py tests/test_api.py tests/test_integration.py -q -k "not stream"
```

请在独立的开发环境中运行且不要配置真实模型 Key：有 Key 时，部分业务路径和 RAG 可能尝试在线服务。`tests/conftest.py` 设置 `APP_ENV=testing`，测试数据库为 `data/test.db`，不会使用默认开发库。

| 文件 | 覆盖 |
| --- | --- |
| `test_api.py` | 健康检查、注册登录、请求校验、面试和画像接口 |
| `test_integration.py` | 注册至面试总结的完整业务链路 |
| `test_rag.py` | 检索结果、MMR、提示词缓存和标准答案 |
| `test_agents.py` | 真实模型下的问题生成、评估与流式输出 |

在线 Agent 测试需单独配置模型与网络，然后显式运行：

```bash
python -m pytest tests/test_agents.py -q
```

在线测试可能产生模型调用费用。离线降级测试通过不能证明真实模型效果；归档中的旧测试报告也不等同于本次执行结果。测试目录从原成员提交目录迁入，包导入层级保持一致。

`test_api.py` 的两项 `preview_*_stream` 用例要求真实流式 Agent，未配置 Key 时返回错误事件；离线命令显式排除名称含 `stream` 的用例。配置真实模型后可通过 `python -m pytest tests/test_api.py -q -k stream` 单独验证。
