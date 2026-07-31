# PPT 答辩大纲（15-20 分钟）

---

## 第 1 页：封面
- 项目名称：面试突破助手
- 团队成员 / 角色
- 日期

## 第 2 页：选题背景
- 传统面试练习痛点：题目质量不稳定、评估主观、无法针对性改进
- 为什么不直接用大模型：无状态、不可复现、无个性化

## 第 3 页：需求分析
- 目标用户：求职者、应届毕业生
- 核心功能：RAG 出题、多 Agent 评估、追问、画像分析
- 输入输出规范：API 接口定义
- 异常处理：Agent 调用失败自动降级

## 第 4 页：系统架构图
- 前端 Vue3 -> FastAPI -> Agent/RAG -> DeepSeek LLM
- LCEL 管道：prompt | llm | parser
- 数据流：用户回答 -> 评估 Agent -> 四维度评分 -> 画像

## 第 5 页：核心技术栈
- 后端：Python + LangChain 1.3.x + LCEL + FastAPI
- 前端：Vue3 + Tailwind CSS + Vite
- 数据：SQLite + Chroma 向量数据库
- LLM：DeepSeek（OpenAI 兼容接口）

## 第 6 页：LCEL 管道（核心）
- `_build_chain(prompt, parser)` -> `RunnableSequence`
- 三段式：ChatPromptTemplate | ChatOpenAI | StrOutputParser
- 现场验证：打印 chain.steps 类型

## 第 7 页：RAG 知识库
- Embedding + Chroma 向量化入库（主路径）
- TF-IDF 降级（离线环境）
- MMR 重排序 + 文档来源标注

## 第 8 页：Multi-Agent 协作
- InterviewerAgent：出题 + 追问
- EvaluatorAgent：四维度评分
- KnowledgeAgent：本地 RAG 检索
- Orchestrator：LangGraph 状态机

## 第 9 页：对话记忆
- 基于 LangChain InMemoryChatMessageHistory
- 滑动窗口 + 摘要压缩
- sessionId 会话隔离

## 第 10 页：SSE 流式输出
- `/preview-question/stream` 逐 token 推送
- `_astream_chain` 异步流式管道
- 前端实时渲染

## 第 11 页：sessionId 全流程
- 前端生成 -> 请求头传递 -> 中间件提取 -> Agent 隔离
- 面试记录关联 sessionId

## 第 12 页：用户认证
- 注册/登录/退出
- bcrypt 密码哈希
- Bearer token 验证

## 第 13 页：前端功能演示
- 首页配置：公司/职位/技术栈选择
- 面试视图：流式出题 + 追问 + 评估展示
- 画像页面：雷达图 + 趋势图 + 知识图谱 + 挑战打卡

## 第 14 页：核心代码说明
- LCEL 管道代码片段
- Agent 懒初始化 + 降级机制
- RAG 双后端架构

## 第 15 页：开发问题总结
- 两套后端并存问题
- 前后端 API 契约不一致
- Pydantic schema 丢字段
- Windows GBK 编码崩溃

## 第 16 页：个人实训收获
- LangChain LCEL 管道理解
- Multi-Agent 架构设计
- 前后端联调经验
- AI 辅助开发的正确姿势

## 第 17 页：Q&A

---

## 答辩注意事项
- 控制在 15-20 分钟
- 不能只演示代码，必须讲技术原理
- 能讲清 LCEL 管道的数据流转机制
- 能解释为什么选 RAG（选项B）而不是其他模块
