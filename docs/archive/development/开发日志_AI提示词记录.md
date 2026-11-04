# AI 对话提示词记录 & 个人开发日志

> 考核要求：必须留存 AI 提示词对话记录、个人完整开发日志（缺少直接扣 2 分）

---

## 2026-07-22 后端架构打通

### 会话 1：前后端打通
- **AI 工具**：Claude (ZCode)
- **目的**：前端连的是 Express 假数据，需要切到 FastAPI
- **提示词**：
  > 前端 client.ts 的 BASE_URL 改为 http://localhost:8000，
  > 后端 start_interview 改为一次性生成 3 道题返回 InterviewResponse，
  > submit_answer 接受 questionId 精确定位题目
- **AI 回复要点**：改了 BASE_URL、start_interview 返回 Interview ORM、AnswerSubmit 加 question_id、InterviewResponse 嵌套 QuestionInfo
- **采纳**：全部采纳

### 会话 2：Agent/RAG 真实接入
- **AI 工具**：Claude (ZCode)
- **目的**：出题/评估/追问全是 stub，需接真实 Agent
- **提示词**：
  > interview_service.py 的 _generate_question 和 _evaluate_answer 接入真实 Agent，
  > try Agent -> catch fallback 占位逻辑
- **AI 回复要点**：懒初始化 _get_interviewer/_get_evaluator、try-catch 降级机制
- **采纳**：全部采纳

### 会话 3：LCEL 管道搭建
- **AI 工具**：Claude (ZCode)
- **目的**：考核要求 LCEL 管道，当前是裸 llm.invoke
- **提示词**：
  > agents/base.py 加 _build_chain 返回 RunnableSequence，
  > interviewer 和 evaluator 主方法改走 LCEL 管道
- **AI 回复要点**：_build_chain(prompt, parser) -> prompt | llm | parser、_invoke_chain 带重试、evaluator 用 JsonOutputParser
- **采纳**：全部采纳

---

## 2026-07-23 画像页修复

### 会话 4：RAG 向量化升级
- **AI 工具**：Claude (ZCode)
- **目的**：RAG 是纯 TF-IDF，需加 Embedding + Chroma
- **提示词**：
  > rag/engine.py 加 Chroma + OpenAIEmbeddings 主路径，
  > TF-IDF 作为降级
- **AI 回复要点**：_ChromaBackend + _TfidfBackend 双后端架构、自动降级
- **采纳**：全部采纳

### 会话 5：画像页 bug 修复
- **AI 工具**：Claude (ZCode)
- **目的**：雷达图四维分数相同、趋势图日期重复、知识图谱节点无坐标
- **提示词**：
  > _generate_radar_data 从 Answer.dimension_scores 取真实分数，
  > 趋势图日期改 MM-DD HH:MM，
  > KnowledgeGraph 改动态圆形布局
- **AI 回复要点**：radar_data 从 answers 取维度分数、trend_data 加时间、图谱动态布局
- **采纳**：全部采纳

### 会话 6：挑战打卡系统
- **AI 工具**：Claude (ZCode)
- **目的**：挑战打卡需要影响评分
- **提示词**：
  > 建 UserChallenge 模型 + API，
  > 完成挑战 +2 分/项，最高 +8
- **AI 回复要点**：UserChallenge 表、toggle API、画像计算加 challenge_bonus
- **采纳**：全部采纳

---

## 2026-07-24 前端组件升级

### 会话 7：RadarChart 重写
- **AI 工具**：Claude (ZCode)
- **目的**：雷达图不显示分数、颜色不变化、无动画
- **提示词**：
  > RadarChart 加分数标签、按分数着色、tooltip、生长动画、空数据占位
- **AI 回复要点**：getScoreColor 四级着色、requestAnimationFrame 动画、tooltip 浮层
- **采纳**：全部采纳

### 会话 8：TrendLineChart 重写
- **AI 工具**：Claude (ZCode)
- **目的**：趋势图 Y 轴固定、无填充、无平均线
- **提示词**：
  > TrendLineChart 动态 Y 轴范围、渐变填充、平均虚线、生长动画、骨架屏
- **AI 回复要点**：yMin/yMax 动态计算、linearGradient、stroke-dashoffset 动画
- **采纳**：全部采纳

---

## 2026-07-25 认证系统接入

### 会话 9：用户认证
- **AI 工具**：Claude (ZCode)
- **目的**：接入注册/登录/退出认证系统
- **提示词**：
  > 加 auth 路由（register/login/logout）、User.password_hash、UserSession 模型、
  > get_current_user 依赖注入
- **AI 回复要点**：bcrypt 哈希、Bearer token 验证、_verify_owner 权限校验
- **采纳**：全部采纳

### 会话 10：记忆模块升级
- **AI 工具**：Claude (ZCode)
- **目的**：记忆模块是手写的，需改用 LangChain 组件
- **提示词**：
  > agents/memory.py 改用 InMemoryChatMessageHistory + HumanMessage/AIMessage
- **AI 回复要点**：基于 langchain_core.chat_history、滑动窗口、summarize_older、clear
- **采纳**：全部采纳

---

## 开发日志总结

| 日期 | 工作内容 | 耗时 |
|------|---------|------|
| 07-22 | 前后端打通 + Agent 接入 + LCEL 管道 | 4h |
| 07-23 | RAG 升级 + 画像修复 + 挑战系统 | 5h |
| 07-24 | 前端图表重写 + 趋势图升级 | 3h |
| 07-25 | 认证接入 + 记忆模块 + 最终核查 | 3h |
