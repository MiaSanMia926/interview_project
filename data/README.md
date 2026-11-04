# 数据目录

| 路径 | 管理方式 |
| --- | --- |
| `questions/*.json` | 纳入 Git，维护题库与清洗后的数据 |
| `standard_answers.json` | 纳入 Git，维护标准答案样例 |
| `interview.db`、`test.db` | 运行或测试时创建，不提交 |
| `chroma/` | 生成的向量 / 检索索引与缓存，不提交 |
| `logs/` | 运行日志，不提交 |

新环境通过启动后端创建业务表，索引可用 `python scripts/load_questions.py` 重建。旧运行库和日志从新版本跟踪清单移除，原版本仍保留在 Git 历史中。不要将真实用户回答、会话令牌或密钥作为样例数据提交。
