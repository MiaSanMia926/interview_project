# AI 对话提示词记录 & 个人开发日志

> **考核要求**：必须留存 AI 提示词对话记录、个人完整开发日志（缺少个人开发日志直接扣 2 分）。
> 每人一个文件，以 `姓名_角色.md` 命名（如 `张三_后端.md`）。

---

## 一、模板：个人开发日志

```markdown
# 个人开发日志 — 姓名 / 角色

## 2026-07-XX

| 时间段 | 工作内容 | 涉及文件 | 耗时 |
|--------|---------|---------|------|
| 上午 | 【填写：今天做了什么】 | | 2h |
| 下午 | | | 3h |

### 关键决策/问题
- 

### 与 AI 协作记录（见下方）
```

---

## 二、模板：AI 提示词对话记录

```markdown
## AI 对话记录 — 日期

### 会话 1
- **AI 工具**：Cursor / Claude / 文心一言 / ...
- **目的**：【填写本次对话要解决什么问题】
- **主要提示词**：
  > 在此粘贴你的提示词
- **AI 回复要点**：
  - 
- **采纳/不采纳**：采纳 / 部分采纳 / 不采纳（原因：...）

---

### 会话 2
...
```

---

## 三、按模块整理建议

| 模块 | 建议记录的对话主题 |
|------|------------------|
| 后端 API | FastAPI 路由设计、Pydantic schema、参数校验、异常处理 |
| Agent | LangChain Agent 结构、LCEL 管道写法、提示词模板设计 |
| RAG | Chroma 集成、TF-IDF 降级、Embedding 模型选择 |
| 前端 | Vue 组件、API client、状态管理、面试流程交互 |
| 数据库 | SQLAlchemy 模型、SQLite 配置 |
| 测试 | pytest 配置、TestClient、mock LLM |

---

## 四、示例（后端同学可参考）

```markdown
## AI 对话记录 — 2026-07-22

### 会话 1
- **AI 工具**：Claude (ZCode)
- **目的**：修 LCEL 管道，把 agents/base.py 的裸 llm.invoke() 改成 prompt | llm | parser 管道
- **主要提示词**：
  > agents/base.py 是裸调 LLM 接口，没有搭建 LCEL 管道，踩中考核"后端总分上限22分"的规则。
  > 帮忙在 BaseAgent 里加 _build_chain 方法，返回 RunnableSequence 类型的 LCEL 管道，
  > 并把 interviewer.py 和 evaluator.py 的主方法改走管道。
- **AI 回复要点**：
  - 加了 `_build_chain(prompt, parser)` 返回 `prompt | self.llm | parser`
  - 加了 `_invoke_chain(chain, inputs)` 带指数退避重试
  - `interviewer.py` 的 `generate_question`、`generate_followup` 改为 `_build_chain` + `_invoke_chain`
  - `evaluator.py` 的 `evaluate` 改为 `_build_chain` + `JsonOutputParser`
- **采纳/不采纳**：全部采纳

### 会话 2
- **AI 工具**：Claude (ZCode)
- **目的**：RAG 引擎升级，加入 Embedding + Chroma 作为主路径，TF-IDF 降级为 fallback
- **主要提示词**：
  > rag/engine.py 目前是纯 TF-IDF，考核要求"向量化入库、相似度检索"，
  > 需要加上 Embedding 模型 + Chroma 向量数据库。Embedding 不可用时自动降级到 TF-IDF。
- **AI 回复要点**：
  - 拆出 `_VectorBackend` 抽象基类，`_ChromaBackend` 和 `_TfidfBackend` 各实现一个
  - `_ChromaBackend` 用 `langchain_openai.OpenAIEmbeddings` + `Chroma`
  - `_TfidfBackend` 保留原有的 TF-IDF 实现
  - `RAGEngine._init_backend()` 优先尝试 Chroma，失败自动切 TF-IDF
- **采纳/不采纳**：全部采纳
```

---

## 使用说明

1. 每人复制这份模板，以 `姓名_角色.md` 命名保存到 `docs/` 目录
2. 按日期倒序填写（最新的在最上面）
3. AI 对话记录**只要保留每次对话的核心提示词和采纳决策**，不需要逐字记录对话原文
4. 如果有些对话已经丢失，按记忆补一个概要，标注「回忆整理」
