# 测试报告

**项目名称**：面试突破助手
**文档版本**：v2.0（正式版，覆盖注册登录+会话隔离新增需求后的全量复测）
**测试人员**：成员E（测试与文档专员）
**最后更新**：2026-07-25

---

## 一、测试概览

- **测试环境**：Windows，Python 3.12.7，pytest 9.1.1，后端服务基于FastAPI，真实调用DeepSeek API（模型 `deepseek-v4-flash`）
- **测试范围**：健康检查、认证与会话隔离（注册/登录/令牌/退出）、多用户数据隔离、面试全流程接口、SSE流式接口、Agent层（含LCEL管道验证、流式方法、对话记忆）、RAG检索模块、全链路集成测试。共**8大模块，累计44个测试用例，44个通过**。
- **版本背景说明**：相较v0.1版本（针对早期占位实现阶段的代码），本轮测试对应的代码已完成重大升级——服务层真正接入了Agent/RAG（不再是占位返回）、新增了完整的注册登录与基于账号的会话隔离、新增了SSE流式输出。v0.1版本记录的ISSUE-07（服务层未接入Agent）等历史问题已不再适用，本报告不再重复记录，仅在"历史问题回顾"一节简要说明其解决情况。

---

## 二、测试结果汇总

| 模块 | 测试用例数 | 通过数 | 失败数 | 通过率 | 状态 |
|------|-----------|--------|--------|--------|------|
| 健康检查 | 1 | 1 | 0 | 100% | ✅ 已完成 |
| 认证与会话（注册/登录/令牌/退出） | 11 | 11 | 0 | 100% | ✅ 已完成 |
| 多用户数据隔离 | 4 | 4 | 0 | 100% | ✅ 已完成 |
| 面试全流程接口 | 9 | 9 | 0 | 100% | ✅ 已完成 |
| SSE流式接口 | 4 | 4 | 0 | 100% | ✅ 已完成 |
| Agent层（含LCEL验证、流式方法、对话记忆） | 9 | 9 | 0 | 100% | ✅ 已完成 |
| RAG检索模块 | 3 | 3 | 0 | 100% | ✅ 已完成（过程中发现并修复1项生产代码bug，见"四、发现的问题"） |
| 全链路集成测试 | 3 | 3 | 0 | 100% | ✅ 已完成 |
| **合计** | **44** | **44** | **0** | **100%** | ✅ |

---

## 三、测试详情

### 3.1 健康检查 + 认证与会话（`tests/test_api.py::TestHealthAPI`、`TestAuthAPI`）

| 用例 | 测试点 | 结果 |
|------|--------|------|
| `test_health` | 健康检查接口返回服务状态 | ✅ PASSED |
| `test_register` | 注册新账号，返回令牌+用户信息 | ✅ PASSED |
| `test_register_duplicate_username` | 用户名重复应被拒绝 | ✅ PASSED |
| `test_register_username_too_short` | 用户名少于3字符应返回422 | ✅ PASSED |
| `test_register_password_too_short` | 密码少于6位应返回422 | ✅ PASSED |
| `test_login_success` | 正确用户名密码登录成功 | ✅ PASSED |
| `test_login_wrong_password` | 密码错误应返回401 | ✅ PASSED |
| `test_login_nonexistent_user` | 用户名不存在应返回401 | ✅ PASSED |
| `test_get_me_requires_token` | 不带令牌访问`/api/users/me`应返回401 | ✅ PASSED |
| `test_get_me_with_token` | 带令牌能正确拿到当前登录用户信息 | ✅ PASSED |
| `test_logout_invalidates_token` | 退出登录后，旧令牌应立即失效 | ✅ PASSED |
| `test_expired_token_is_rejected` | 过期令牌（7天有效期机制）应被拒绝 | ✅ PASSED |

**说明**：密码采用bcrypt哈希存储（不存明文），登录令牌具备7天有效期机制，退出登录会主动使令牌失效，三项均已通过用例验证其真实生效，不只是接口"看起来有"。

### 3.2 多用户数据隔离（`tests/test_api.py::TestUserIsolationAPI`）

| 用例 | 测试点 | 结果 |
|------|--------|------|
| `test_cannot_view_others_profile` | 用户A不能查看用户B的画像 | ✅ PASSED |
| `test_interview_list_only_shows_own` | 面试列表只返回当前登录用户自己的记录，不会拉取他人数据 | ✅ PASSED |
| `test_interview_list_pagination` | 分页参数（page/size）正确生效 | ✅ PASSED |
| `test_cannot_access_others_interview` | 用户A不能访问用户B创建的面试（返回403） | ✅ PASSED |

**说明**：这一批用例是本轮新增"会话隔离"需求的核心验证——不再是基于匿名UUID的伪隔离，而是基于真实账号身份+登录令牌的数据隔离，且已通过跨账号越权测试确认能真正拦截未授权访问。

### 3.3 面试全流程接口（`tests/test_api.py::TestInterviewAPI`）

| 用例 | 测试点 | 结果 |
|------|--------|------|
| `test_create_interview` | 创建面试，成功返回`created`状态 | ✅ PASSED |
| `test_create_interview_requires_login` | 未登录创建面试应被拒绝 | ✅ PASSED |
| `test_start_interview` | 开始面试，一次性生成全部题目 | ✅ PASSED |
| `test_submit_answer` | 提交回答，返回真实评估结果 | ✅ PASSED |
| `test_skip_question` | 跳过当前问题 | ✅ PASSED |
| `test_get_interview_state` | 查询面试当前状态 | ✅ PASSED |
| `test_get_interview_summary` | 跑完整个面试流程后，正确生成总结报告（总分、分类得分、强弱项、建议） | ✅ PASSED |
| `test_summary_before_completion_rejected` | 面试未结束时调用总结接口，返回400业务错误而非500服务器错误 | ✅ PASSED |
| `test_empty_answer_rejected` | 空回答应返回422参数校验错误 | ✅ PASSED |

### 3.4 SSE流式接口（`tests/test_api.py::TestInterviewAPI`）

| 用例 | 测试点 | 结果 |
|------|--------|------|
| `test_preview_question_stream_requires_login` | 未登录访问流式出题接口应被拒绝 | ✅ PASSED |
| `test_preview_question_stream_returns_chunks` | 流式出题接口能收到多个文本片段（chunk），非一次性整段返回 | ✅ PASSED |
| `test_preview_feedback_stream_returns_score_then_chunks` | 流式点评接口先返回真实评分（score事件），再流式吐出点评文字（chunk事件） | ✅ PASSED |
| `test_preview_stream_ownership_check` | 他人不能访问你的面试流式演示接口 | ✅ PASSED |

**说明**：这4项验证了SSE流式输出（考核标准"FastAPI接口开发"优秀线要求）不仅接口层真实可用，而且和其他新增的登录/隔离机制正确融合，没有因为叠加多个功能而产生遗漏。

### 3.5 Agent层（`tests/test_agents.py`）

| 用例 | 测试点 | 结果 |
|------|--------|------|
| `test_generate_question` | 生成面试问题，返回非空文本 | ✅ PASSED |
| `test_uses_lcel_pipeline` | **核心用例**：验证核心链路确实是LCEL的`RunnableSequence`管道，而非裸`llm.invoke()` | ✅ PASSED |
| `test_generate_followup` | 生成追问 | ✅ PASSED |
| `test_generate_question_stream` | 流式生成问题，能收到多个文本片段 | ✅ PASSED |
| `test_evaluate` | 评估结果结构完整性（score/dimensions/strengths/improvements/feedback字段齐全） | ✅ PASSED |
| `test_generate_feedback_stream` | 流式生成点评：先有真实评分，再流式吐出自然语言点评文字 | ✅ PASSED |
| `test_add_and_context` | 对话记忆：消息添加与上下文获取 | ✅ PASSED |
| `test_window_trim` | 对话记忆：滑动窗口机制，超出窗口大小后正确丢弃最早记录、保留最新记录 | ✅ PASSED |
| `test_clear` | 对话记忆：清空会话历史接口 | ✅ PASSED |

**重要说明**：`test_uses_lcel_pipeline`这条用例是本轮新增的关键验证点——直接用代码断言核心生成链路的对象类型确实是LangChain的`RunnableSequence`，为"项目采用LCEL管道架构"这一考核硬性要求提供了可复现、可自动化验证的证据，而不只是文档里的文字描述。

另外，`agents/memory.py`的`ConversationMemory`类已重构为基于LangChain内置的`InMemoryChatMessageHistory`实现，并补充了`clear()`清空会话、`summarize_older()`摘要压缩等能力，对应考核标准"对话记忆智能体"可选模块的优秀线要求。测试过程中发现旧版`TestMemoryManager`用例（基于已废弃的`max_tokens`参数）与重构后的构造函数签名不匹配导致报错，已同步修复为匹配新的`window_size`滑动窗口机制。

### 3.6 RAG检索模块（`tests/test_rag.py`）

| 用例 | 测试点 | 结果 |
|------|--------|------|
| `test_rag_load_and_search` | 题库文档加载 + 基础检索，验证返回字段完整性及分类正确性 | ✅ PASSED |
| `test_rag_mmr_and_prompt_cache` | MMR多样性重排序 + Prompt Cache命中统计 | ✅ PASSED（过程中发现并修复真实bug，见下） |
| `test_standard_answers` | 标准答案库按ID/分类查询 | ✅ PASSED |

**⚠️ 过程中发现的重要bug（已修复，详见"四、发现的问题"ISSUE-A）**：`rag/engine.py`中`_TfidfBackend.mmr()`方法存在下标类型错误与候选池未按相关性排序两个问题，导致MMR重排序功能实际调用时必定抛出`TypeError`崩溃。由于生产代码里`agents/knowledge.py`的检索调用路径走的是`search()`而非`search_with_mmr()`，这个bug此前从未被真实业务流程触发过，是本轮系统性执行全部测试后才首次暴露。已定位根因并修复，修复后MMR重排序功能真实可用。

**说明**：核心检索仍为自研TF-IDF+余弦相似度方案（非Embedding+向量数据库），该技术选型的具体理由已记录于`docs/RAG_DELIVERY.md`补充章节，测试重点在于验证检索准确性、MMR多样性效果、Prompt缓存的命中/未命中统计逻辑均按预期工作。

### 3.7 全链路集成测试（`tests/test_integration.py`）

| 用例 | 测试点 | 结果 |
|------|--------|------|
| `test_full_interview_flow_end_to_end` | 完整业务链路：注册→创建面试→开始（生成全部题目）→连续提交回答（正确处理追问/下一题/结束三种分支）→查看总结报告→确认出现在历史记录中 | ✅ PASSED |
| `test_flow_blocked_at_every_step_without_login` | 验证流程中每一个环节（开始/答题/跳过/查状态/查总结/查列表）缺少登录令牌都会被正确拦截，而非只在第一步生效 | ✅ PASSED |
| `test_logout_does_not_lose_created_data` | 退出登录后用同一账号密码重新登录，之前创建的面试记录依然完整可见 | ✅ PASSED |

**说明**：这是本轮测试中耗时最长、验证范围最广的一组用例——`test_full_interview_flow_end_to_end`真实走完一整场面试的全部题目和多轮LLM调用，验证的不是某个接口"看起来正确"，而是整条业务链路从登录态传递、题目生成、真实评分、状态流转到最终总结报告，各环节衔接是否严丝合缝。

---

## 四、发现的问题

| 编号 | 问题描述 | 严重程度 | 状态 |
|------|---------|---------|------|
| ISSUE-A | `rag/engine.py`的`_TfidfBackend.mmr()`方法：①把文档字典误当作整数下标使用，导致`self._vectors[idx]`直接抛`TypeError`；②候选池未按相关性分数排序即截取，导致重排序作用在任意顺序的候选上而非最相关的一批 | 高（MMR重排序功能此前完全无法正常调用，属于考核标准"RAG优秀线"里明确写入文档、但实际是摆设的功能） | ✅ 已修复：改用`id()`映射正确追踪文档在向量列表中的真实位置，并在候选池截取前补上按分数排序这一步。修复后`test_rag_mmr_and_prompt_cache`用例通过 |
| ISSUE-B | `agents/memory.py`的`ConversationMemory`类构造函数参数已从`max_tokens`重构为`window_size`（配合LangChain `InMemoryChatMessageHistory`的滑动窗口实现），但`tests/test_agents.py`中旧版`TestMemoryManager`用例仍按旧签名调用，导致`TypeError` | 中（测试脚本与代码实现不同步，非生产代码缺陷） | ✅ 已修复：更新用例改用`window_size`参数，并针对滑动窗口截断、清空会话两项能力补充了对应断言 |
| ISSUE-C | `backend/schemas/`下多个类使用Pydantic V2里已标记废弃的`class Config`写法，运行测试时出现`PydanticDeprecatedSince20`警告 | 低（当前不影响功能，Pydantic V3发布后需要跟进迁移到`ConfigDict`） | ⏳ 暂不处理，记录留档 |
| ISSUE-D | `tests/test_api.py::test_expired_token_is_rejected`用例内部使用了已弃用的`datetime.utcnow()`（测试代码本身，非生产代码） | 低 | ⏳ 暂不处理，记录留档 |

---

## 五、历史问题回顾（v0.1版本记录的问题，现状说明）

v0.1版本测试报告中记录的以下问题，在本轮测试对应的代码版本中均已解决，不再是待办事项：

- **ISSUE-07（服务层未接入Agent）**：`backend/services/interview_service.py`现已真正调用`agents/interviewer.py`、`agents/evaluator.py`完成出题与评估，不再是固定占位返回，本轮`test_get_interview_summary`、`test_full_interview_flow_end_to_end`等用例的评分均为0-100区间的真实动态分值即为证明。
- **LCEL管道与分支问题**：`backend/chains/`（旧LCEL封装层）与`agents/`两套实现已收敛为一套——`agents/base.py`内部直接采用LCEL的`prompt | llm | parser`管道写法，`test_uses_lcel_pipeline`用例对此提供了自动化验证。
- **依赖清单不完整（ISSUE-03/04）**：`backend/requirements.txt`已补齐所有必需依赖并锁定精确版本号。
- **命名不一致（ISSUE-08）**：`DEEPSEEK_*`与`MIMO_*`环境变量命名已统一处理，无需临时别名打通。

---

## 六、待完成事项

- **LangSmith追踪分析**：目前代码中仍未发现LangSmith集成，需与负责Agent层的队友确认是否要接入；若不接入，将改为基于现有请求日志中间件（`request.log`）的接口耗时分析。
- **`docs/TEST_CASES.md`（测试用例文档）**：本报告记录的是测试**执行结果**；按老师新增要求，还需单独编写一份测试用例设计文档（用例编号、测试目的、前置条件、步骤、预期结果），供不阅读代码的评审快速理解测试覆盖范围，计划下一步启动。

---

## 七、结论

本轮测试覆盖健康检查、认证与会话隔离、多用户数据隔离、面试全流程、SSE流式接口、Agent层（含LCEL管道验证）、RAG检索、全链路集成共8大模块，**累计44个测试用例，全部通过**。

相较早期版本，测试范围随项目实际进展有大幅扩展：新增了完整的账号注册登录与基于真实身份的会话隔离验证、新增了SSE流式输出的接口级测试、新增了直接验证LCEL管道对象类型的自动化用例。测试过程中不仅验证了既有功能的正确性，还额外发现并修复了两处此前从未被真实调用路径触发过的问题——RAG模块MMR重排序的下标错误、对话记忆模块重构后遗留的测试失效，均已在本轮修复并通过复测。

早期版本记录的核心问题（服务层未接入Agent、分支与命名不统一、依赖缺失）在当前代码版本中均已解决，不再是遗留风险。剩余待推进事项为LangSmith集成确认与测试用例设计文档编写，均已列入下一步计划。