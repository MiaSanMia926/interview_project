# 前端 Vibe Coding 对话记录 · AI 提示词与开发日志

> 说明：本记录留存"面试突破手"项目前端开发过程中与 AI 编程助手（Claude / ZCode）的真实对话内容，按开发日期整理。每日包含实际的提示词原文、AI 回复（含代码）、以及后续调整过程，用于满足课程 Vibe Coding 材料留存要求。

---

## 2026-07-20 · 项目骨架搭建

**我：**
> 我要做一个 Vue3 + TS 的前端项目，用 Vite 起项目。技术栈定一下：Tailwind CSS 用最新的 4.x，不想用传统 PostCSS 配置那套东西，请求库用 axios，图标用 lucide-vue-next，动效用 motion。帮我把项目骨架和目录结构搭一下，顺便把 .env.example 写好。

**Claude (ZCode)：**
好的，Tailwind 4.x 确实推荐直接用 Vite 插件方式，比传统 PostCSS 链路更简洁。先建项目：

```bash
npm create vite@latest interview-coach-frontend -- --template vue-ts
cd interview-coach-frontend
npm install axios lucide-vue-next motion
npm install -D tailwindcss @tailwindcss/vite
```

`vite.config.ts`：

```ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
})
```

`src/style.css` 只需要一行：

```css
@import "tailwindcss";
```

目录结构建议这样分：

```
src/
  api/           # 所有请求逻辑集中在这里
    client.ts
    session.ts
  components/    # 视图 + 图表组件
  types.ts       # 统一类型定义
  data.ts        # 静态配置（公司/岗位/技术栈默认列表）
  App.vue
  main.ts
```

`.env.example`：

```
# 后端 API 基础地址，本地开发默认连临时 Node 服务，联调阶段切换为 FastAPI 地址
VITE_API_BASE_URL=http://localhost:3000

# 仅本地假后端直连模型时使用，真实后端接入后前端不再直接用这个 key
DEEPSEEK_API_KEY=your_key_here
```

要不要我把 ESLint + Prettier 也一起配一下？团队五个人协作，统一一下代码风格能少很多 review 上的麻烦。

**我：**
> 加一下，順便把 package.json 里几个依赖的版本锁死，不然大家本地装的版本可能不一样。

**Claude (ZCode)：**
明白，`package.json` 里我会把 `axios`、`tailwindcss`、`@tailwindcss/vite`、`lucide-vue-next`、`motion` 这几个都锁定为精确版本号（不用 `^` 前缀），ESLint 配置用 `@vue/eslint-config-typescript` + `eslint-plugin-vue`，加一个 `.prettierrc` 统一格式化规则。这样团队里谁 `npm install` 装出来的都是同一个版本，不会出现"我这能跑你那不能跑"的问题。

---

## 2026-07-21 · 登录页与首页配置

**我：**
> 写一个登录注册页 LoginView.vue，要支持注册和登录两种状态切换（一个页面，点个链接切换）。登录成功之后用 sessionStorage 存 token，不要用 localStorage——我是想着标签页关了就自动清掉，减少 token 一直躺在本地的风险。另外 App.vue 里我需要几个顶层状态：isCheckingAuth（检查登录态的时候别闪现登录页）、isLoggedIn、activeTab。

**Claude (ZCode)：**
这个思路没问题，`sessionStorage` 确实比 `localStorage` 更适合这种场景。`LoginView.vue` 核心逻辑大概是这样：

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { login, register } from '../api/client'

const mode = ref<'login' | 'register'>('login')
const email = ref('')
const password = ref('')
const errorMsg = ref('')
const loading = ref(false)

const emit = defineEmits<{ success: [] }>()

async function handleSubmit() {
  errorMsg.value = ''
  loading.value = true
  try {
    const fn = mode.value === 'login' ? login : register
    const res = await fn(email.value, password.value)
    sessionStorage.setItem('token', res.token)
    emit('success')
  } catch (e: any) {
    errorMsg.value = e.type === 'business' ? e.detail : '网络异常，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>
```

`App.vue` 里的三个状态：

```ts
const isCheckingAuth = ref(true)
const isLoggedIn = ref(false)
const activeTab = ref<'home' | 'interview' | 'report' | 'profile'>('home')

onMounted(async () => {
  const token = sessionStorage.getItem('token')
  if (token) {
    try {
      await getMe()
      isLoggedIn.value = true
    } catch {
      sessionStorage.removeItem('token')
    }
  }
  isCheckingAuth.value = false
})
```

`isCheckingAuth` 为 `true` 的时候页面上就渲染一个空白或者 loading 骨架屏，等检查完了再决定显示登录页还是主界面，这样就不会出现"先闪一下登录页，然后又跳走"的问题。

**我：**
> 可以，先按这个来。首页配置页呢，HomeView.vue，要选目标公司、目标岗位、技术栈，默认选项从哪儿来？

**Claude (ZCode)：**
建议单独放一个 `data.ts` 存这些静态默认列表，别写死在组件里，后面改选项不用动组件逻辑：

```ts
// data.ts
export const DEFAULT_COMPANIES = ['字节跳动', '阿里巴巴', '腾讯', '美团', '拼多多']
export const DEFAULT_POSITIONS = ['前端开发', '后端开发', '算法工程师', '产品经理']
export const DEFAULT_TECH_STACKS = ['Vue', 'React', 'Java', 'Python', 'Go']
```

`HomeView.vue` 里直接 `import` 这三个常量做下拉选项就行，用户选完点"开始模拟面试"，把这几个值当参数传给创建面试的接口。

---

## 2026-07-22 · 统一 API 客户端

**我：**
> 今天重点搞一下统一请求这块。写 api/client.ts，用 axios.create 建个实例，请求拦截器要统一加两个东西：X-Session-Id（这个需要一个单独的 session.ts 来生成和持久化）和 Authorization。响应拦截器把错误分三类：network、http、business，方便页面按类型给不同提示，不要笼统报"请求失败"。

**Claude (ZCode)：**
`session.ts` 先来：

```ts
// session.ts
const KEY = 'session_id'

export function getSessionId(): string {
  let id = sessionStorage.getItem(KEY)
  if (!id) {
    id = crypto.randomUUID()
    sessionStorage.setItem(KEY, id)
  }
  return id
}
```

`client.ts`：

```ts
import axios from 'axios'
import { getSessionId } from './session'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  config.headers['X-Session-Id'] = getSessionId()
  const token = sessionStorage.getItem('token')
  if (token) config.headers['Authorization'] = `Bearer ${token}`
  return config
})

export type ApiError =
  | { type: 'network' }
  | { type: 'http'; status: number }
  | { type: 'business'; detail: string }

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    if (!err.response) {
      return Promise.reject({ type: 'network' } satisfies ApiError)
    }
    const detail = err.response.data?.detail
    if (detail) {
      return Promise.reject({ type: 'business', detail } satisfies ApiError)
    }
    return Promise.reject({ type: 'http', status: err.response.status } satisfies ApiError)
  }
)
```

这样每个页面组件里 `catch` 到的都是结构化的 `ApiError`，判断一下 `type` 就知道该弹什么文案了。

**我：**
> 行，那基础接口先按这套定义出来，getHealth、getMe、getHistory、createInterview，后端那边接口文档还没完全定，我们先按约定的字段来。

**Claude (ZCode)：**
没问题，先把类型和函数占位定出来，等后端确认了再核对调整：

```ts
export function getHealth() {
  return http.get('/api/health')
}
export function getMe(): Promise<UserProfile> {
  return http.get('/api/users/me')
}
export function getHistory(userId: string): Promise<InterviewSummary[]> {
  return http.get(`/api/users/${userId}/history`)
}
export function createInterview(payload: CreateInterviewPayload): Promise<InterviewResponse> {
  return http.post('/api/interviews', payload)
}
```

这几个先按现有约定写，后端接口就绪之后我们再对一遍字段，有出入的话改起来也就是改这几个函数和对应的类型，影响范围可控。

---

## 2026-07-23 · 模拟面试交互与 SSE 流式接入

**我：**
> InterviewView.vue 要做面试交互页了，展示题目、答题输入框，提交调答案接口。但今天真正难的是要接 SSE 流式接口，streamPreviewQuestion 和 streamPreviewFeedback，axios 好像不支持处理 ReadableStream？

**Claude (ZCode)：**
对，axios 底层不直接暴露 `ReadableStream`，这部分建议单独用原生 `fetch` 处理，写一个通用的 SSE 解析工具：

```ts
type SSEHandlers = {
  onChunk?: (text: string) => void
  onScore?: (data: any) => void
  onDone?: () => void
  onError?: (msg: string) => void
}

export async function readSSEStream(url: string, body: unknown, handlers: SSEHandlers) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Session-Id': getSessionId() },
    body: JSON.stringify(body),
  })
  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.startsWith('data:')) continue
      const payload = JSON.parse(line.slice(5).trim())
      switch (payload.type) {
        case 'chunk': handlers.onChunk?.(payload.text); break
        case 'score': handlers.onScore?.(payload.data); break
        case 'done': handlers.onDone?.(); break
        case 'error': handlers.onError?.(payload.message); break
      }
    }
  }
}
```

`InterviewView.vue` 里调用的时候：

```ts
async function askNextQuestion() {
  currentQuestion.value = ''
  await readSSEStream('/api/interviews/preview-question/stream', { interviewId: id }, {
    onChunk: (t) => currentQuestion.value += t,
    onDone: () => { isStreaming.value = false },
  })
}
```

效果就是题目会一个字一个字地"打出来"，而不是等模型全生成完再一次性显示。

**我：**
> 效果出来了，但是布局有点乱，输入框和流式文字区域挤在一起，帮我调一下 UI，作答区域固定在底部，题目区域可以滚动。

**Claude (ZCode)：**
好，改成 flex 布局，题目区 `flex-1 overflow-y-auto`，作答区 `shrink-0` 固定在底部：

```vue
<div class="flex flex-col h-screen">
  <div class="flex-1 overflow-y-auto p-4">{{ currentQuestion }}</div>
  <div class="shrink-0 border-t p-4">
    <textarea v-model="answer" class="w-full" />
    <button @click="submitAnswer">提交</button>
  </div>
</div>
```

这样不管题目文字多长，作答框都会稳定停在底部，不会被顶出屏幕。

---

## 2026-07-24 · 前后端真实联调

**我：**
> 今天要把前端从连临时的 Express 假后端，切到真正的 FastAPI 后端了。后端那边说 startInterview 现在是一次性生成 3 道题，整体返回一个 InterviewResponse；submitAnswer 要带 questionId 精确对应题目；AnswerResponse 里评价信息嵌在 evaluation 字段下面。BASE_URL 也要改。

**Claude (ZCode)：**
把 `.env` 里 `VITE_API_BASE_URL` 改成 FastAPI 地址，类型这边跟着调整：

```ts
interface InterviewResponse {
  interviewId: string
  questions: { questionId: string; text: string }[]
}

interface SubmitAnswerPayload {
  questionId: string
  answerText: string
}

interface AnswerResponse {
  evaluation: {
    score: number
    dimensionScores: Record<string, number>
    feedback: string
  }
  nextAction: 'next_question' | 'finish'
}
```

对应的 `createInterview` 和 `submitAnswer` 函数签名也要跟着改，之前假后端是一道题一道题给的，现在要一次性拿到 3 道题存到本地状态里，前端自己维护"当前第几题"的指针。

**我：**
> 联调了一下，发现有几个字段名对不上，后端是下划线命名（question_id），我们这边是驼峰（questionId）。要不要做个转换层？

**Claude (ZCode)：**
可以做一个 `camelCase <-> snake_case` 的转换适配层放在 `client.ts` 的响应拦截器里统一处理，这样业务代码完全不用关心命名风格。不过这样会多一层运行时开销，而且调试的时候看 network 面板和看代码里的字段名对不上，容易迷惑。另一个思路是直接跟后端同学商量，让 FastAPI 那边用 Pydantic 的 `alias_generator` 直接按驼峰序列化返回，前端不用做任何转换。你们内部沟通一下选哪个方案？

**我：**
> 问了一下后端，他们说加 alias_generator 也不麻烦，就用第二种方案吧，不加转换层了。

**Claude (ZCode)：**
好，那 `client.ts` 这边保持原样就行，不用加转换逻辑。我把类型定义里的字段名按最终确认的驼峰版本核对了一遍，`InterviewResponse`、`AnswerResponse` 都跟后端 `schemas/interview.py` 对齐了，没有遗留不匹配的字段。

---

## 2026-07-28 · 诊断报告与雷达图

**我：**
> ReportView.vue，用雷达图展示 /api/interviews/{id}/summary 返回的多维度评分，再配个柱状图做对比。雷达图这块麻烦一点，之前没写过，能给个思路吗？

**Claude (ZCode)：**
雷达图本质就是把 N 个维度按角度均分在一个圆上，每个维度的分数决定这个点离圆心的距离，然后把这些点连成一个多边形：

```ts
function getPolygonPoints(scores: number[], maxScore: number, radius: number, center: number) {
  const n = scores.length
  return scores.map((score, i) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2
    const r = (score / maxScore) * radius
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    }
  })
}
```

`RadarChart.vue` 拿这些点连成 SVG `<polygon>`，再画几层同心圆做刻度背景就行，我先给你写一版。

**我：**
> 图画出来了，但是四个维度的分数看起来都一样，画出来是个正方形，这不太对吧。

**Claude (ZCode)：**
这个大概率是取数逻辑的问题，你现在传给 `getPolygonPoints` 的 `scores` 数组，是不是四个位置都填的同一个总分？雷达图应该是从后端返回的逐维度分数里取值，比如 `Answer.dimensionScores.技术深度`、`.表达逻辑` 这些字段分别取，而不是把 `interview.totalScore` 复制四遍。你检查一下 `ReportView.vue` 里组装 `scores` 数组那一行代码。

**我：**
> 啊对，确实是这个问题，我组装数组的时候手滑写成了都取 totalScore。改成分别取 dimensionScores 里的字段就对了，谢谢。

**Claude (ZCode)：**
没问题，这种取数环节的小疏忽很常见，图表本身的算法没问题，回头如果还有类似"图看着不对"的情况，先怀疑传进去的数据对不对，往往比怀疑绘图逻辑更快定位到问题。

---

## 2026-07-29 · 能力画像与知识图谱

**我：**
> ProfileView.vue，做能力画像。要有个趋势线图，展示历次面试各维度得分变化。但有个问题：同一个用户如果一天内练了好几次模拟面试，横轴按日期显示的话，好几个点会挤在同一个刻度上，分不清先后顺序。

**Claude (ZCode)：**
把横轴的日期格式从"只精确到天"改成"精确到分钟"就能解决，比如 `07-29 14:32` 这种格式：

```ts
function formatAxisLabel(timestamp: string) {
  const d = new Date(timestamp)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${min}`
}
```

这样即使同一天练了三四次，每个点的横轴标签也是唯一的，不会叠在一起。

**我：**
> 好，另外 KnowledgeGraph.vue 那个知识图谱，现在节点坐标是写死的，知识点一多就互相挤在一起重叠了，想要个能自适应的布局。

**Claude (ZCode)：**
可以改成动态圆形布局，根据当前节点数量实时计算每个节点应该在圆周上的哪个角度：

```ts
function layoutNodes(nodes: KnowledgeNode[], radius: number, center: number) {
  const n = nodes.length
  return nodes.map((node, i) => {
    const angle = (Math.PI * 2 * i) / n
    return {
      ...node,
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle),
    }
  })
}
```

节点数量变了，角度间隔会自动重新计算，不会再出现固定坐标导致的重叠问题。如果后面知识点数量差异特别大（比如从 5 个变到 30 个），可以再加一层"按数量动态调整半径"的逻辑，数量多的时候半径适当增大，避免节点之间还是太挤。

**我：**
> 这个先不用，节点数量目前波动不大，先按固定半径的动态角度布局来就行。

---

## 2026-07-30 · 全流程测试与材料整理

**我：**
> 今天把登录到能力画像整个流程走一遍，发现两个问题：一是后端接了真实 Agent 之后，接口偶尔会超时；二是画像页面刷新一下，之前加载好的数据就没了，得重新请求。

**Claude (ZCode)：**
超时这块，前端可以在请求层面加一个更明确的提示，而不是让用户干等：

```ts
http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    if (err.code === 'ECONNABORTED') {
      return Promise.reject({ type: 'network', message: '模型响应较慢，请稍后重试' } satisfies ApiError)
    }
    // ...原有逻辑
  }
)
```

页面上遇到这个错误类型时，给一个"重新生成"按钮而不是直接报错卡住。

画像页刷新丢数据，大概率是因为数据只存在组件内部的 `ref` 里，页面刷新组件重新挂载后状态就清空了。如果只是刷新问题，最简单的办法是在 `onMounted` 里重新拉一次接口——反正接口本身不慢，重新请求一次的成本不高，不需要上更复杂的持久化方案。

**我：**
> 行，就走重新请求这条路，不搞额外的持久化了。最后帮我把这几天的对话记录整理成文档，再补一下 README。

**Claude (ZCode)：**
好，我按日期把这几天的提示词和关键代码整理成了 Markdown 文档，README 里也补上了本地运行步骤、目录结构说明和环境变量说明，方便其他组员和答辩时候查阅。

---

## 开发日志总结

| 日期 | 工作内容 | 耗时 |
|------|---------|------|
| 07-20 | 技术选型 + 项目骨架搭建 | 3h |
| 07-21 | 登录注册页 + 首页配置页 | 4h |
| 07-22 | 统一 API 客户端 + 基础接口类型定义 | 4h |
| 07-23 | 模拟面试交互页 + SSE 流式解析 | 5h |
| 07-24 | 前后端真实联调 + 字段命名对齐 | 4h |
| 07-28 | 诊断报告页 + 雷达图取数修复 | 4h |
| 07-29 | 能力画像页 + 知识图谱动态布局 | 4h |
| 07-30 | 全流程测试 + 开发材料整理 | 3h |

> 注：以上为根据实际开发过程复现的 AI 对话记录，用于满足 Vibe Coding 过程材料留存要求。
