# 目录迁移记录

保留 `backend/`、`frontend/`、`agents/`、`rag/` 的模块边界和现有启动入口。

| 原位置 / 类型 | 处理 |
| --- | --- |
| `成员E提交物料_测试代码/` | 移至 `tests/` |
| `成员E提交物料_文档/` | 移至 `docs/archive/delivery/` |
| 根目录旧结构、启动与项目文档 | 移至 `docs/archive/` |
| 原 `docs/` 开发日志与成员指南 | 移至 `docs/archive/development/` |
| 根目录答辩、问题报告、Word 材料 | 移至 `docs/archive/` |
| 前后端提示词记录 | 移至 `docs/archive/` 对应位置 |
| 周报生成工具 | 移至 `docs/archive/development/`，保留历史脚本 |
| `__pycache__`、日志、数据库、索引缓存 | 停止跟踪，添加忽略规则 |
| 仓库内部的重复 ZIP、空 `bun.lock` | 从新版本移除；前端以 `package-lock.json` 为准 |

历史文档可能提到旧 Node 后端、旧 API 或成员分工，保留原文便于追溯；当前接口与启动方法以新 README 和当前开发文档为准。整理不改变项目的课程来源或原始协作记录。
