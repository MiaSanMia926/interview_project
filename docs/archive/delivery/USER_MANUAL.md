# 用户手册

**项目名称**：面试突破助手
**文档版本**：v2.0（正式版，覆盖注册登录+会话隔离新增需求）
**编写人**：成员E（测试与文档专员）
**最后更新**：2026-07-25

---

## 一、项目简介

面试突破助手是一个基于 **RAG检索 + Multi-Agent架构（LangChain LCEL管道）** 的智能模拟面试系统。系统通过面试官Agent生成/追问问题、评估Agent对回答进行多维度打分，帮助用户练习技术面试、发现薄弱环节并针对性改进。

系统具备**完整的账号体系**：每个用户需要注册并登录后才能使用，不同账号的数据（面试记录、能力画像）完全隔离，互不可见。

> 相较早期版本，本手册所有描述的功能均已真实验证：题目生成与回答评估已真正接入LangChain Agent（不再是占位实现），并新增了SSE流式输出（打字机效果）和基于登录令牌的会话隔离机制。

---

## 二、环境准备

### 2.1 必需软件

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.10 及以上 | 建议使用虚拟环境，避免与系统/Anaconda环境冲突 |
| Node.js | 18及以上 | 运行前端（Vue3） |
| pip | 随Python自带 | 用于安装依赖 |

### 2.2 获取代码

从代码仓库拉取项目代码，确保以下目录/文件齐全：
```
项目根目录/
├── agents/              # Agent层（面试官/评估/知识检索等，LCEL管道实现）
├── backend/             # FastAPI后端服务
├── frontend/             # Vue3前端
├── data/                # 题库与标准答案数据
├── rag/                 # RAG检索模块
├── start_backend.bat    # Windows一键启动脚本
```

### 2.3 配置 API Key

在项目根目录（与`backend/`同级）新建`.env`文件，参考`.env.example`填写：
```
DEEPSEEK_API_KEY=你的DeepSeek API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v4-flash
```

> 说明：`DEEPSEEK_API_KEY`需自行申请。**如果未配置该变量，后端启动时会直接报错提示**，不会有默认Key兜底运行——这是有意为之的安全设计，避免误用他人凭证。

### 2.4 安装依赖并启动服务

**建议使用虚拟环境**：
```bash
python -m venv venv
venv\Scripts\activate
python -m pip install -r backend/requirements.txt
```

**启动后端服务**（二选一）：
```bash
# 方式一：双击运行
start_backend.bat

# 方式二：命令行手动启动
python -m uvicorn backend.main:app --reload
```

**验证启动成功**：浏览器访问`http://127.0.0.1:8000/docs`，能看到Swagger接口文档页面即为成功。

**启动前端**：
```bash
cd frontend
npm install
npm run dev
```
浏览器打开终端提示的地址（默认`http://localhost:3003`）。

> **提示**：Windows环境下建议使用`127.0.0.1`而非`localhost`访问本地服务，避免IPv6/IPv4解析导致的响应延迟。

---

## 三、核心使用流程

系统的完整使用流程分为两大阶段：**账号认证**，然后是**面试全流程**。

### 阶段一：账号认证

#### 步骤1：注册账号

```
POST /api/auth/register
Body: { "username": "your_name", "password": "your_password" }
```
- `username`长度需在3-50个字符之间，且不能与已有账号重复
- `password`至少6位
- 成功返回`201`，响应中的`token`字段是本次登录会话的令牌，**后续所有接口都需要在请求头中携带它**：
  ```
  Authorization: Bearer <token>
  ```
- 注册成功即完成登录，无需再单独调用登录接口

#### 步骤2：登录（已有账号时使用）

```
POST /api/auth/login
Body: { "username": "your_name", "password": "your_password" }
```
- 验证用户名密码，成功后返回一个**新的**令牌（和之前的令牌不同，之前的令牌不受影响，仍然有效直到各自过期）
- 令牌有效期为7天，过期后需要重新登录

#### 步骤3：退出登录

```
POST /api/auth/logout
Header: Authorization: Bearer <token>
```
- 使当前这个令牌立即失效，之后用这个令牌访问任何接口都会返回401

### 阶段二：面试全流程

以下所有接口都需要在请求头携带`Authorization: Bearer <token>`。

#### 步骤1：创建面试

```
POST /api/interviews
Body: {
  "targetCompany": "字节跳动",
  "targetPosition": "后端工程师",
  "techStack": ["Python", "Redis", "MySQL"],
  "interviewMode": "technical"
}
```
- 面试自动归属于当前登录账号，无需（也无法通过传参冒充他人）指定所属用户
- `interviewMode`默认为`"technical"`（技术面），可选`"behavioral"`（行为面）
- 成功返回`201`，响应中的`id`字段即为面试ID

#### 步骤2：开始面试

```
POST /api/interviews/{面试ID}/start
```
- 无需请求体
- **一次性生成全部面试题目**（由AI结合目标公司/职位/技术栈生成，非固定题库轮询），返回完整的`questions`数组
- 面试状态变为"进行中"

#### 步骤3：提交回答（可反复调用直至面试结束）

```
POST /api/interviews/{面试ID}/answer
Body: { "questionId": "当前题目的id", "userAnswer": "你的回答内容" }
```
- `userAnswer`不能为空
- `questionId`需要传入当前正在回答的题目id（前端从`start`接口返回的`questions`数组中获取）
- 返回结果中`evaluation`字段是AI对本次回答的**真实评估**（准确性/完整性/逻辑性/表达能力四维度打分+具体点评，非固定分数）
- `nextAction`字段说明下一步走向：
  - `"followup"`：AI判断当前回答不够充分，会针对性追问
  - `"next_question"`：进入下一题
  - `"end"`：面试结束

#### 步骤4：查看面试总结

```
GET /api/interviews/{面试ID}/summary
```
- 面试结束（`status`为`completed`）后调用，未结束时调用会返回明确的业务错误提示
- 返回总分、各分类得分、强弱项分析、改进建议等

### 辅助接口

| 接口 | 用途 |
|------|------|
| `POST /api/interviews/{面试ID}/skip` | 跳过当前问题，不计入错误统计 |
| `GET /api/interviews/{面试ID}/state` | 查询当前面试进度和状态 |
| `GET /api/interviews` | 查看**当前登录账号自己的**面试列表（支持`page`/`size`分页、`status`筛选） |
| `GET /api/users/me` | 查看当前登录账号信息 |
| `GET /api/users/{用户ID}/profile` | 查看用户能力画像（只能查看自己的，查询他人会返回403） |
| `GET /api/health` | 健康检查，确认服务是否正常运行 |

### SSE流式接口（打字机效果演示）

系统额外提供两个流式接口，用于展示AI"边生成边输出"的实时效果：

| 接口 | 用途 |
|------|------|
| `POST /api/interviews/{面试ID}/preview-question/stream` | 流式演示生成下一题的过程 |
| `POST /api/interviews/{面试ID}/preview-feedback/stream` | 先返回真实评分，再流式演示生成点评文字的过程 |

这两个接口返回的是SSE格式的事件流（`data: {...}`），每条消息含`type`字段（`chunk`/`score`/`done`/`error`），同样需要携带登录令牌，且只能操作自己的面试记录。

---

## 四、完整调用示例（Python）

```python
import requests

BASE_URL = "http://127.0.0.1:8000"

# 1. 注册账号（首次使用）
auth = requests.post(f"{BASE_URL}/api/auth/register", json={
    "username": "demo_user",
    "password": "demo_password_123"
}).json()
token = auth["token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. 创建面试
interview = requests.post(f"{BASE_URL}/api/interviews", json={
    "targetCompany": "字节跳动",
    "targetPosition": "后端工程师",
    "techStack": ["Python", "Redis"]
}, headers=headers).json()
interview_id = interview["id"]

# 3. 开始面试
start = requests.post(f"{BASE_URL}/api/interviews/{interview_id}/start", headers=headers).json()
first_question = start["questions"][0]
print("第一题：", first_question["questionText"])

# 4. 提交回答
answer = requests.post(f"{BASE_URL}/api/interviews/{interview_id}/answer", json={
    "questionId": first_question["id"],
    "userAnswer": "Python是一种解释型、面向对象的高级编程语言。"
}, headers=headers).json()
print("评估结果：", answer["evaluation"])
print("下一步：", answer["nextAction"])

# 5. 查看总结（面试结束后）
summary = requests.get(f"{BASE_URL}/api/interviews/{interview_id}/summary", headers=headers).json()
print("面试总结：", summary)

# 6. 退出登录
requests.post(f"{BASE_URL}/api/auth/logout", headers=headers)
```

---

## 五、常见问题（FAQ）

**Q1：启动服务时提示`No module named uvicorn`等**
A：说明当前Python环境里没装对应的包，执行`python -m pip install -r backend/requirements.txt`补装即可。如果电脑装了多个Python环境（如同时有Anaconda和官方Python），注意确认命令行实际用的是哪一个（`Get-Command python`可查看），统一用`python -m pip install`而不是单独的`pip install`，避免装到不同环境导致"装了却用不了"。

**Q2：忘记携带`Authorization`请求头会怎样**
A：除了`/api/auth/register`、`/api/auth/login`、`/api/health`这几个不需要登录的接口，其余所有接口都会返回401"未登录或令牌缺失"。

**Q3：访问接口时响应异常缓慢**
A：Windows环境下用`localhost`访问本地服务可能触发IPv6/IPv4解析延迟，改用`127.0.0.1`即可解决。

**Q4：注册时提示"用户名已被注册"**
A：系统对用户名做了唯一性校验，换一个用户名即可。

**Q5：面试还没结束就调用`/summary`会怎样**
A：接口会返回明确的业务错误提示（400），而非服务器内部错误，属于正常的边界处理。

**Q6：提交空回答会怎样**
A：接口会返回参数校验错误（422），`userAnswer`字段不允许为空字符串。

**Q7：能不能查看别人的面试记录或能力画像**
A：不能。系统所有涉及个人数据的接口都会校验"这份数据是不是当前登录账号自己的"，尝试访问他人数据会返回403。

**Q8：令牌过期了怎么办**
A：登录令牌有效期为7天，过期后需要重新调用登录接口获取新令牌，之前创建的面试记录、能力画像数据不会因为重新登录而丢失。

---

## 六、当前实现说明

- 核心问题生成与回答评估已真实接入LangChain Agent（基于LCEL管道`prompt | llm | parser`），并配合RAG检索题库/标准答案作为参考。
- 系统采用真实密码认证（bcrypt哈希存储）+ 基于登录令牌的会话隔离，不同账号数据完全独立。
- RAG检索核心采用TF-IDF + 余弦相似度方案（而非Embedding+向量数据库），并实现了MMR多样性重排序、来源标注、元数据管理；该技术选型的具体理由详见`docs/RAG_DELIVERY.md`。
- LangSmith等外部追踪工具目前未接入。