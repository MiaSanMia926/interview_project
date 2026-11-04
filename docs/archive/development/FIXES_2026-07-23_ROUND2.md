# 第二轮修复文档：Agent 评估 + 答题推进 + 用户画像

> 日期：2026-07-23  
> 范围：`agents/` `backend/` `frontend/`  
> 目标：修复 Agent 打分走离线兜底、追问死循环、打分不细致、无法跳过题目

---

## 修改总览

| 文件 | 类型 | 说明 |
|------|------|------|
| `agents/evaluator.py` | 🐛 崩溃修复 + ✨ 增强 | 补充缺失 import；重写评估 prompt，打分更细致 |
| `backend/services/interview_service.py` | 🐛 逻辑修复 | 修复并行生成污染 `current_question_index` → 追问死循环 |
| `backend/config.py` | 🔧 参数调整 | 降低追问门槛，减少追问次数 |
| `frontend/src/api/client.ts` | ➕ 新增 | 添加 `skipQuestion` API 方法 |
| `frontend/src/App.vue` | ➕ 新增 | 添加 `handleSkipQuestion` 回调 |
| `frontend/src/components/InterviewView.vue` | ➕ 新增 | 添加跳过按钮 + 处理逻辑 |

---

## 一、Agent 评估崩溃修复

### 问题：打分永远是兜底值 `{accuracy:78, completeness:72, logic:75, expression:70}`

#### 1.1 `agents/evaluator.py` — 缺失 import 导致 Agent 初始化崩溃

```diff
  from langchain_core.prompts import ChatPromptTemplate
+ from langchain_core.output_parsers import JsonOutputParser
```

**原因**：`EvaluatorAgent.__init__` 第 59 行调用了 `JsonOutputParser()`，但该符号只在 `base.py` 中 import，`evaluator.py` 自己没 import。
`NameError` 被 `_get_evaluator()` 的 `try/except` 静默捕获，设 `_EVALUATOR = False`，之后所有评估走静态兜底。

#### 1.2 `.env` API Key 被覆盖为中文占位文本

**现象**：`.env` 文件内容一度变成：
```
DEEPSEEK_API_KEY=#输入你的Deepseek API Key
```

**结果**：`httpx` 库在构建 HTTP Header 时触发：
```
UnicodeEncodeError: 'ascii' codec can't encode characters in position 8-11
```

Agent 初始化抛异常 → 被 `_get_interviewer()` / `_get_evaluator()` 静默捕获 → 全部走静态兜底。

**修复**：恢复正确的 API Key（注意：该 key 已因写入本文档而泄露，务必在 DeepSeek 控制台吊销并重新生成，不要再使用原值）。

---

## 二、追问死循环修复

### 问题：永远卡在第一题"深度追问"，无法推进到下一题，看不到诊断书

#### 根因分析

`start_interview` 使用 `ThreadPoolExecutor` 并行生成 3 道题。每个线程在自己的 DB session 中执行：

```python
# 线程内部
local_interview.current_question_index = idx  # idx = 0, 1, 2
db.commit()  # 将这个 idx 写入数据库
```

3 个线程各自 commit `current_question_index = 0/1/2`。主线程虽然后续设置 `= 0` 并 commit，但最终数据库中该值被最后一个完成的线程覆盖为 **2**。

`_decide_next` 使用 `current_question_index` 定位当前题：
```python
current = self._get_current_question(interview)  # 拿到索引 2 的题目（第 3 题）
answers_count = ...count()  # 第 3 题没有回答 → count = 0
if answers_count < MAX_FOLLOWUPS:  # 0 < 2 → 永远为真
    return "followup"  # 死循环！
```

**结果**：无论回答多少次第 1 题，`_decide_next` 总是查到第 3 题（无回答），永远返回"追问"。

#### 2.1 `backend/services/interview_service.py` — 并行生成不再修改 `current_question_index`

```diff
  def generate_one(idx):
      local_interview = db.query(Interview).filter(...).first()
-     local_interview.current_question_index = idx
-     q = self._generate_question_in_session(local_interview, db)
+     q = self._generate_question_in_session(local_interview, db, idx)
```

`idx` 仅作为 `question_index` 参数传入 LLM prompt，不再写入数据库。

#### 2.2 `_decide_next` 用 `question_id` 精确定位

```diff
- def _decide_next(self, interview, score, user_answer=""):
-     current = self._get_current_question(interview)  # 依赖可能被污染的 current_question_index
+ def _decide_next(self, interview, score, user_answer="", question_id=None):
+     current = self._get_current_question(interview, question_id=question_id)  # 精确匹配
```

#### 2.3 `submit_answer` 传入 `question_id`

```diff
- next_action, next_message = self._decide_next(interview, evaluation["score"], user_answer)
+ next_action, next_message = self._decide_next(interview, evaluation["score"], user_answer, question_id=question_id)
```

#### 2.4 跳转逻辑改用题目列表位置

```diff
- interview.current_question_index += 1
- next_question = self._get_question_by_index(interview, interview.current_question_index)

+ questions_list = self.db.query(Question)...order_by(Question.created_at).all()
+ current_idx = next(i for i, q in enumerate(questions_list) if q.id == current_question.id)
+ interview.current_question_index = current_idx + 1
+ next_question = questions_list[current_idx + 1] if current_idx + 1 < len(questions_list) else None
```

同理 `_decide_next` 的结束判断：
```diff
- if interview.current_question_index + 1 < MAX_QUESTIONS:
+ questions_list = self.db.query(Question)...all()
+ current_idx = next(i for i, q in enumerate(questions_list) if q.id == current.id)
+ if current_idx + 1 < len(questions_list):
```

#### 2.5 `_generate_question_in_session` / `_generate_fallback_question_in_session` 签名更新

```diff
- def _generate_question_in_session(self, interview, db):
+ def _generate_question_in_session(self, interview, db, idx=0):
      ...
-     question_index=interview.current_question_index,
+     question_index=idx,
```

```diff
- def _generate_fallback_question_in_session(self, interview, db):
+ def _generate_fallback_question_in_session(self, interview, db, idx=0):
      ...
-     f"请介绍一下你对 {first_tech} 的理解..."
+     fallback_pool = [
+         f"请介绍一下你对 {first_tech} 的理解...",
+         f"在 {first_tech} 的实际应用中...",
+         f"请谈谈 {first_tech} 的未来发展...",
+     ]
+     question_text = fallback_pool[idx % len(fallback_pool)]
```

---

## 三、评估 Prompt 增强

### 问题：打分只有简单的 4 个数字 + 一句话反馈，不够细致

#### `agents/evaluator.py` — 重写评估 prompt

**旧**：
```
评估维度（每项0-100分）：
1. accuracy - 准确性：技术概念是否正确
...
strengths: ["优点1", "优点2"]
feedback: "详细反馈文字"
```

**新**：增加了：

1. **4 级评分标准**（每个维度 90-100 / 70-89 / 50-69 / 0-49）及详细描述
2. **加权公式**：`score = accuracy×0.35 + completeness×0.30 + logic×0.20 + expression×0.15`
3. **strengths 要求**："做到了什么 + 为什么是亮点"，每条 15-40 字
4. **improvements 要求**："当前不足 + 如何改进 + 预期效果"，每条 15-50 字
5. **feedback 要求**：80-200 字，必须包含 `①整体评价 ②最突出亮点（具体展开） ③最需改进点（给出学习方向）`

---

## 四、追问参数调整

### `backend/config.py`

| 参数 | 旧值 | 新值 | 说明 |
|------|------|------|------|
| `MAX_FOLLOWUPS` | 2 | **1** | 每题最多追问 1 次 |
| `SCORE_THRESHOLD_FOR_FOLLOWUP` | 70 | **55** | 得分 ≥ 55 不追问 |

**效果**：单题最多回答 2 次（首答 + 1 次追问），3 题总计最多 6 轮回答，避免无限追问。

---

## 五、添加"跳过题目"功能

### 5.1 `frontend/src/api/client.ts` — 新增 API 方法

```typescript
skipQuestion: (interviewId: string) =>
    request<AnswerResponse>(`/api/interviews/${interviewId}/skip`, { method: 'POST' }),
```

### 5.2 `frontend/src/App.vue` — 新增回调

```typescript
const handleSkipQuestion = async () => {
  if (!currentInterview.value) return;
  const result = await api.skipQuestion(currentInterview.value.id);
  return result;
};
```

```html
<InterviewView ... :on-skip-question="handleSkipQuestion" />
```

### 5.3 `frontend/src/components/InterviewView.vue` — 添加跳过按钮

输入框右侧新增 **⏭ 跳过按钮**：

```html
<button @click="handleSkip" :disabled="isLoading" ...>
  <SkipForward class="w-4 h-4" />
</button>
```

新增 `handleSkip` 函数：调用跳过 API → 根据返回的 `nextAction` 自动推进到下一题或结束面试。

新增 props：
```typescript
interface InterviewViewProps {
  ...
  onSkipQuestion: () => Promise<AnswerResponse>;
}
```

---

## 六、验证结果

| 验证项 | 状态 | 详情 |
|--------|------|------|
| EvaluatorAgent 初始化 | ✅ | import 补齐后正常 |
| Agent 真实评估（非兜底） | ✅ | 返回自定义分数，不再总是 75 分 |
| `currentQuestionIndex` 无污染 | ✅ | 始终为正确值 0 |
| 追问死循环 | ✅ 修复 | 3 次提交后正常推进到 Q2 |
| 打分细致度 | ✅ | 含 4 级标准 + 加权公式 + 结构化反馈 |
| 跳过按钮 | ✅ | 可随时跳过当前题进入下一题 |
| 用户画像 API | ✅ | 返回完整 profile 数据 |

### 答题推进流程

```
提交回答 → AI 评估
  ├─ 得分 ≥ 55 → 直接进入下一题
  ├─ 得分 < 55 → AI 追问 1 次 → 无论如何进入下一题
  └─ 点击跳过 → 直接进入下一题

全部 3 题完成 → "生成大厂技术诊断书" → 查看报告
```
