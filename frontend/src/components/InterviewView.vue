<template>
  <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
    <!-- Left Column: Progress Sidebar -->
    <div class="lg:col-span-1 space-y-6">
      <!-- Timing and General Card -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div class="flex justify-between items-center border-b border-slate-100 pb-3">
          <span class="text-xs text-slate-500 font-medium">面试用时</span>
          <span class="text-sm font-mono font-bold text-emerald-600 flex items-center gap-1.5">
            <Clock class="w-4 h-4 text-emerald-500 animate-pulse" />
            {{ formatTime(elapsedSeconds) }}
          </span>
        </div>

        <div class="space-y-1.5 text-left">
          <span class="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">当前目标</span>
          <h4 class="text-sm font-bold text-slate-800">{{ interview.targetCompany }}</h4>
          <p class="text-xs text-slate-600 leading-snug">{{ interview.targetPosition }}</p>
        </div>

        <!-- Stepper progress -->
        <div class="pt-2">
          <div class="flex justify-between text-[10px] text-slate-400 font-bold mb-1.5">
            <span>问题进度</span>
            <span>{{ Math.min(currentQuestionIndex + 1, questions.length) }} / {{ questions.length }}</span>
          </div>
          <div class="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
            <div 
              class="bg-indigo-600 h-1.5 rounded-full transition-all duration-300"
              :style="{ width: `${(Math.min(currentQuestionIndex + 1, questions.length) / questions.length) * 100}%` }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Live Multi-dimension Radar Overview -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4 text-left">
        <div>
          <h4 class="text-xs font-bold text-slate-800 flex items-center gap-1.5">
            <Compass class="w-4 h-4 text-indigo-600" />
            实时专家评估雷达
          </h4>
          <p class="text-[10px] text-slate-500 mt-1 leading-snug">
            基于已完结问题的实时各维度能力推演，帮助您在后续答题中及时微调策略。
          </p>
        </div>
        <RadarChart :data="getLiveRadarData()" />
      </div>
    </div>

    <!-- Right Column: Active Interactive Chat Interface -->
    <div class="lg:col-span-3 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between h-[640px] overflow-hidden">
      <!-- Chat Header -->
      <div class="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600 font-extrabold relative">
            🤖
            <span class="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 rounded-full border-2 border-slate-50 animate-ping"></span>
            <span class="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 rounded-full border-2 border-slate-50"></span>
          </div>
          <div class="text-left">
            <span class="text-xs font-bold text-slate-800 block">AI 面试官 & 评估 Agent 联合会话</span>
            <span class="text-[9px] text-slate-500 leading-none">工作流：题库真题索引 & 条件深挖</span>
          </div>
        </div>

        <button
          @click="$emit('finish-interview')"
          class="text-[10px] bg-red-50 border border-red-200 hover:bg-red-100 text-red-600 font-bold px-2.5 py-1.5 rounded flex items-center gap-1 transition-colors cursor-pointer"
        >
          <LogOut class="w-3.5 h-3.5" />
          中止面试生成报告
        </button>
      </div>

      <!-- Chat History Flow -->
      <div class="flex-1 p-6 overflow-y-auto space-y-6 bg-white">
        <div 
          v-for="msg in messages" 
          :key="msg.id" 
          :class="['flex gap-3 text-left', msg.sender === 'user' ? 'flex-row-reverse' : '']"
        >
          <!-- Avatar -->
          <div :class="[
            'w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold',
            msg.sender === 'user' 
              ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' 
              : 'bg-indigo-50 text-indigo-600 border border-indigo-200'
          ]">
            {{ msg.sender === 'user' ? '👤' : '🤖' }}
          </div>

          <!-- Message bubble -->
          <div class="max-w-2xl space-y-3">
            <!-- Text Content -->
            <div 
              v-if="msg.text"
              :class="[
                'px-4 py-3 rounded-xl border leading-relaxed text-sm whitespace-pre-wrap',
                msg.sender === 'user'
                  ? 'bg-emerald-50 border-emerald-100 text-slate-800'
                  : msg.isFollowUp
                    ? 'bg-indigo-50/70 border-indigo-100 text-indigo-900 font-medium'
                    : 'bg-slate-50 border-slate-200 text-slate-800'
              ]"
            >
              {{ msg.text }}
            </div>

            <!-- Sub evaluation result layout (linked inside ai bubble if present) -->
            <div v-if="msg.evaluation" class="bg-slate-50 rounded-xl border border-slate-200 p-5 space-y-4 shadow-sm">
              <div class="flex items-center justify-between border-b border-slate-200 pb-2.5">
                <h5 class="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                  <Award class="w-4 h-4 text-amber-600" />
                  专家评估面板：单题打分
                </h5>
                <div class="flex items-center gap-1.5 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded text-xs font-bold text-emerald-700 shadow-sm">
                  {{ msg.evaluation.score }}分
                </div>
              </div>

              <!-- Dimensions sliders -->
              <div class="grid grid-cols-2 gap-3">
                <div v-for="(value, key) in msg.evaluation.dimensions" :key="key" class="space-y-1">
                  <div class="flex justify-between text-[9px] text-slate-500 font-semibold">
                    <span>{{ getDimensionLabel(key) }}</span>
                    <span class="text-slate-700">{{ value }}</span>
                  </div>
                  <div class="w-full h-1 bg-slate-200 rounded-full overflow-hidden">
                    <div class="bg-emerald-600 h-1 rounded-full" :style="{ width: `${value}%` }"></div>
                  </div>
                </div>
              </div>

              <!-- Strengths & improvements -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 text-[11px] leading-relaxed">
                <div class="bg-emerald-50/50 p-2.5 rounded border border-emerald-200 space-y-1 text-left">
                  <span class="font-bold text-emerald-800 block">🌟 亮点：</span>
                  <p v-for="(s, i) in msg.evaluation.strengths" :key="i" class="text-slate-600">• {{ s }}</p>
                </div>
                <div class="bg-amber-50/50 p-2.5 rounded border border-amber-200 space-y-1 text-left">
                  <span class="font-bold text-amber-800 block">💡 改进建议：</span>
                  <p v-for="(s, i) in msg.evaluation.improvements" :key="i" class="text-slate-600">• {{ s }}</p>
                </div>
              </div>

              <p class="text-[11px] text-slate-600 text-left bg-white p-2.5 rounded leading-relaxed border border-slate-200">
                <b>主考官评语：</b>{{ msg.evaluation.feedback }}
              </p>
            </div>
          </div>
        </div>

        <!-- Skeleton loading on waiting -->
        <div v-if="isLoading" class="flex gap-3 text-left">
          <div class="w-8 h-8 rounded-full bg-indigo-50 text-indigo-600 border border-indigo-200 flex items-center justify-center animate-pulse">
            🤖
          </div>
          <div class="space-y-2 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 max-w-sm">
            <p class="text-xs text-indigo-700 font-semibold flex items-center gap-1.5 animate-pulse">
              <RefreshCw class="w-3 h-3 animate-spin text-indigo-600" />
              评估专家与面试官 Agent 协同诊断中...
            </p>
            <div class="w-48 h-2 bg-slate-200 rounded animate-pulse"></div>
            <div class="w-32 h-2 bg-slate-200 rounded animate-pulse"></div>
          </div>
        </div>

        <div ref="chatEndRef" />
      </div>

      <!-- Input area -->
      <div class="p-4 bg-slate-50 border-t border-slate-200 space-y-2">
        <div v-if="isInterviewFinished" class="bg-emerald-50 border border-emerald-200 p-4 rounded-xl flex items-center justify-between shadow-sm">
          <div class="text-left space-y-1">
            <span class="text-sm font-bold text-emerald-700 block">模拟面试问答圆满结束！</span>
            <span class="text-xs text-slate-500">Agent 集群正在为您生成高保真的深度总监技术诊断书。</span>
          </div>
          <button
            @click="$emit('finish-interview')"
            class="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold py-2.5 px-4 rounded shadow flex items-center gap-1 cursor-pointer transition-colors"
          >
            生成大厂技术诊断书
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>

        <div v-else class="space-y-2">
          <div v-if="currentQuestion" class="flex justify-between items-center px-1 text-[10px] text-slate-500">
            <span class="flex items-center gap-1 text-left">
              <AlertCircle class="w-3.5 h-3.5 text-indigo-600 flex-shrink-0" />
              建议回答方向：涵盖 {{ currentQuestion.category }} 经典高频临界原理与架构方案。
            </span>
            <span class="flex-shrink-0">难度等级: {{ '⭐'.repeat(Math.round(currentQuestion.difficulty / 2) || 3) }}</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="relative flex items-center flex-1">
              <textarea
                v-model="inputValue"
                @keydown.enter.prevent="handleEnterKey"
                :disabled="isLoading"
                :placeholder="isLoading ? '请稍等，AI 正在分析处理中...' : '在此输入您的技术回答（按 Enter 发送，Shift+Enter 换行）...'"
                class="w-full bg-white border border-slate-200 rounded-lg pl-4 pr-12 py-3 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-indigo-500 transition-colors resize-none h-[56px] min-h-[56px] max-h-[120px]"
              />
              <button
                @click="handleSubmit"
                :disabled="isLoading || !inputValue.trim()"
                :class="[
                  'absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-md transition-all cursor-pointer',
                  inputValue.trim() && !isLoading
                    ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow'
                    : 'bg-slate-100 text-slate-400'
                ]"
              >
                <Send class="w-4 h-4" />
              </button>
            </div>
            <button
              @click="handleSkip"
              :disabled="isLoading"
              class="flex-shrink-0 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-500 hover:text-slate-700 text-xs font-medium transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              title="跳过当前问题，直接进入下一题"
            >
              <SkipForward class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import type { Interview, Question, Evaluation } from '../types';
import { Send, Clock, User, Award, Compass, AlertCircle, RefreshCw, LogOut, ChevronRight, SkipForward } from 'lucide-vue-next';
import RadarChart from './RadarChart.vue';
import { ApiError } from '../api/client';
import { streamPreviewFeedback } from '../api/client';

interface InterviewViewProps {
  interview: Interview;
  onSubmitAnswer: (questionId: string, answer: string) => Promise<{
    nextAction: string;
    nextMessage: string;
    evaluation: Evaluation | null;
    isFinished: boolean;
  }>;
  onSkipQuestion: () => Promise<{
    nextAction: string;
    nextMessage: string;
    evaluation: Evaluation | null;
    isFinished: boolean;
  }>;
}

const props = defineProps<InterviewViewProps>();

defineEmits<{
  (e: 'finish-interview'): void;
}>();

interface Message {
  id: string;
  sender: 'ai' | 'user';
  text: string;
  isFollowUp?: boolean;
  evaluation?: Evaluation | null;
}

const messages = ref<Message[]>([]);
const inputValue = ref('');
const isLoading = ref(false);
const currentQuestionIndex = ref(0);
const elapsedSeconds = ref(0);

const chatEndRef = ref<HTMLDivElement | null>(null);

const questions = computed(() => props.interview.questions || []);
const currentQuestion = computed(() => questions.value[currentQuestionIndex.value]);

// Elapsed-time counter shown in the sidebar; purely local, not synced with the backend.
let timer: ReturnType<typeof setInterval> | null = null;
onMounted(() => {
  timer = setInterval(() => {
    elapsedSeconds.value++;
  }, 1000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});

const formatTime = (secs: number) => {
  const m = Math.floor(secs / 60).toString().padStart(2, '0');
  const s = (secs % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
};

// 面试题目可能在组件挂载后才异步返回（App.vue 先切 tab 再调 start API），
// 因此用 watch 而非 onMounted 来兜底：一旦 questions 从空变为非空且还没渲染开幕消息，立刻补上。
let openingRendered = false;

function tryRenderOpening() {
  if (openingRendered) return;
  if (questions.value.length === 0) return;
  openingRendered = true;
  messages.value = [
    {
      id: 'msg-start',
      sender: 'ai',
      text: `你好！我是您的面试官。本次 ${props.interview.targetCompany} 的 ${props.interview.targetPosition} 模拟面试现在开始。\n\n我们将重点考察您在 ${props.interview.techStack.join('、')} 领域的深入理解。下面请听第一题：\n\n**${questions.value[0].questionText}**`
    }
  ];
}

onMounted(() => tryRenderOpening());
watch(() => props.interview.questions, () => tryRenderOpening(), { deep: true });

// Scroll to bottom when messages list updates
watch(messages, () => {
  nextTick(() => {
    chatEndRef.value?.scrollIntoView({ behavior: 'smooth' });
  });
}, { deep: true, immediate: true });

watch(isLoading, () => {
  nextTick(() => {
    chatEndRef.value?.scrollIntoView({ behavior: 'smooth' });
  });
});

const handleSkip = async () => {
  if (isLoading.value) return;
  isLoading.value = true;
  try {
    const response = await props.onSkipQuestion();

    if (response.nextAction === 'next_question' || response.nextAction === 'answer') {
      currentQuestionIndex.value++;
      messages.value.push({
        id: `ai-next-${Date.now()}`,
        sender: 'ai',
        text: `已跳过本题。下面进入第 ${currentQuestionIndex.value + 1} 题：\n\n**${response.nextMessage}**`
      });
    } else if (response.nextAction === 'end') {
      currentQuestionIndex.value = questions.value.length;
      messages.value.push({
        id: `ai-end-${Date.now()}`,
        sender: 'ai',
        text: response.nextMessage
      });
    }
  } catch (e) {
    console.error('Skip failed:', e);
    messages.value.push({
      id: `ai-err-${Date.now()}`,
      sender: 'ai',
      text: '跳过失败，请重试。'
    });
  } finally {
    isLoading.value = false;
  }
};

const handleEnterKey = (e: KeyboardEvent) => {
  if (!e.shiftKey) {
    handleSubmit();
  }
};

const handleSubmit = async () => {
  if (!inputValue.value.trim() || isLoading.value || !currentQuestion.value) return;

  const userAnswer = inputValue.value;
  inputValue.value = '';
  isLoading.value = true;

  // Append user's answer to conversation
  messages.value.push({
    id: `user-${Date.now()}`,
    sender: 'user',
    text: userAnswer
  });

  try {
    const response = await props.onSubmitAnswer(currentQuestion.value.id, userAnswer);
    
    // If there was an evaluation returned (meaning this major question is fully answered)
    if (response.evaluation) {
      // 先用真实分数/维度渲染面板，feedback先留空，交给流式接口逐字填充
      const evalMsgId = `ai-eval-${Date.now()}`;
      messages.value.push({
        id: evalMsgId,
        sender: 'ai',
        text: `评估专家 Agent 已对第 ${currentQuestionIndex.value + 1} 题作出了全维度诊断打分：`,
        evaluation: { ...response.evaluation, feedback: '' }
      });

      // 后台异步流式追加点评文字，不阻塞后续追问/下一题逻辑
      streamPreviewFeedback(
        props.interview.id,
        currentQuestion.value.id,
        userAnswer,
        () => { /* 已有真实分数，这里的score事件不需要处理 */ },
        (piece) => {
          const target = messages.value.find(m => m.id === evalMsgId);
          if (target && target.evaluation) {
            target.evaluation.feedback += piece;
          }
        },
        () => { /* 流结束，无需额外处理 */ },
        (errMsg) => {
          const target = messages.value.find(m => m.id === evalMsgId);
          if (target && target.evaluation && !target.evaluation.feedback) {
            target.evaluation.feedback = response.evaluation.feedback; // 流式失败则回退到原始feedback
          }
        }
      );
    }

    // Handle next action
    if (response.nextAction === 'followup') {
      messages.value.push({
        id: `ai-followup-${Date.now()}`,
        sender: 'ai',
        text: `【深度追问】\n\n${response.nextMessage}`,
        isFollowUp: true
      });
    } else if (response.nextAction === 'next_question' || response.nextAction === 'end') {
      if (response.nextAction === 'next_question') {
        currentQuestionIndex.value++;
        messages.value.push({
          id: `ai-next-${Date.now()}`,
          sender: 'ai',
          text: `下面我们进入第 ${currentQuestionIndex.value + 1} 题：\n\n**${response.nextMessage}**`
        });
      } else {
        // Finished entire interview
        currentQuestionIndex.value = questions.value.length; // ensures completion status
        messages.value.push({
          id: `ai-end-${Date.now()}`,
          sender: 'ai',
          text: response.nextMessage
        });
      }
    }
  } catch (e) {
    console.error(e);
    const hint = e instanceof ApiError && e.kind === 'network'
      ? '⚠️ 连不上后端服务，请确认服务是否已启动，再重新提交这条回答。'
      : '⚠️ 评估 Agent 调用异常，请重试提交这条回答。';
    messages.value.push({
      id: `ai-err-${Date.now()}`,
      sender: 'ai',
      text: hint
    });
    // Put the answer back in the input box so the user doesn't have to retype it
    inputValue.value = userAnswer;
  } finally {
    isLoading.value = false;
  }
};

const getDimensionLabel = (key: string | number) => {
  const labels: Record<string, string> = {
    accuracy: '准确性',
    completeness: '要点完整',
    logic: '逻辑清晰',
    expression: '语言表达'
  };
  return labels[String(key)] || String(key);
};

const getLiveRadarData = () => {
  const answered = questions.value.filter(q => q.evaluation);
  const base = [
    { name: '技术准确性', score: 60, fullMark: 100 },
    { name: '要点完整性', score: 60, fullMark: 100 },
    { name: '思维逻辑性', score: 60, fullMark: 100 },
    { name: '沟通表达力', score: 60, fullMark: 100 }
  ];
  if (answered.length === 0) {
    return base;
  }
  const sums = { accuracy: 0, completeness: 0, logic: 0, expression: 0 };
  answered.forEach(q => {
    const d = q.evaluation!.dimensions;
    sums.accuracy += d.accuracy;
    sums.completeness += d.completeness;
    sums.logic += d.logic;
    sums.expression += d.expression;
  });
  const len = answered.length;
  return [
    { name: '技术准确性', score: Math.round(sums.accuracy / len), fullMark: 100 },
    { name: '要点完整性', score: Math.round(sums.completeness / len), fullMark: 100 },
    { name: '思维逻辑性', score: Math.round(sums.logic / len), fullMark: 100 },
    { name: '沟通表达力', score: Math.round(sums.expression / len), fullMark: 100 }
  ];
};

const isInterviewFinished = computed(() => {
  return currentQuestionIndex.value >= questions.value.length && !isLoading.value;
});
</script>
