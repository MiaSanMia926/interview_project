<template>
  <!-- 登录状态检查中：不显示任何内容，避免闪现登录页 -->
  <div v-if="isCheckingAuth"></div>

  <!-- 未登录：只显示登录/注册页面 -->
  <LoginView v-else-if="!isLoggedIn" @login-success="handleLoginSuccess" />

  <!-- 已登录：显示原有完整内容 -->
  <div v-else class="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans">
    <!-- 顶部导航Header -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 lg:px-8 h-16 flex items-center justify-between">
        <!-- Logo -->
        <div class="flex items-center gap-2.5">
          <div class="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-extrabold shadow-lg shadow-indigo-500/20">
            🎯
          </div>
          <div class="text-left">
            <span class="text-base font-extrabold tracking-tight text-slate-900 block">面试突破手</span>
            <span class="text-[9px] text-indigo-600 font-semibold uppercase leading-none block">AI-Powered Coach</span>
          </div>
        </div>

        <!-- Nav Tabs -->
        <nav class="hidden md:flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg border border-slate-200">
          <button
            @click="activeTab = 'home'; focusReportId = null"
            :class="[
              'px-3 py-1.5 rounded-md text-xs font-bold transition-all cursor-pointer flex items-center gap-1',
              activeTab === 'home' ? 'bg-indigo-600 text-white shadow' : 'text-slate-600 hover:text-slate-900'
            ]"
          >
            <Clipboard class="w-3.5 h-3.5" />
            首页配置
          </button>

          <button
            @click="currentInterview && (activeTab = 'interview')"
            :disabled="!currentInterview"
            :class="[
              'px-3 py-1.5 rounded-md text-xs font-bold transition-all flex items-center gap-1',
              activeTab === 'interview' 
                ? 'bg-indigo-600 text-white shadow' 
                : currentInterview
                  ? 'text-slate-600 hover:text-slate-900 cursor-pointer animate-pulse'
                  : 'text-slate-400 cursor-not-allowed'
            ]"
          >
            <MessageSquare class="w-3.5 h-3.5" />
            正在模拟
          </button>

          <button
            @click="focusReportId && (activeTab = 'report')"
            :disabled="!focusReportId"
            :class="[
              'px-3 py-1.5 rounded-md text-xs font-bold transition-all flex items-center gap-1',
              activeTab === 'report' 
                ? 'bg-indigo-600 text-white shadow' 
                : focusReportId
                  ? 'text-slate-600 hover:text-slate-900 cursor-pointer'
                  : 'text-slate-400 cursor-not-allowed'
            ]"
          >
            <Award class="w-3.5 h-3.5" />
            大厂诊断书
          </button>

          <button
            @click="activeTab = 'profile'"
            :class="[
              'px-3 py-1.5 rounded-md text-xs font-bold transition-all cursor-pointer flex items-center gap-1',
              activeTab === 'profile' ? 'bg-indigo-600 text-white shadow' : 'text-slate-600 hover:text-slate-900'
            ]"
          >
            <Compass class="w-3.5 h-3.5" />
            智能能力画像
          </button>
        </nav>

        <!-- API and Key Status indicator -->
        <div class="flex items-center gap-2">
          <span v-if="apiHealth.status === 'offline'" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-red-50 border border-red-200 text-red-600 text-[10px] font-semibold" :title="offlineReason ?? undefined">
            <Activity class="w-3 h-3" />
            {{ offlineReason ?? '离线自愈模式' }}
          </span>
          <span v-else-if="apiHealth.hasDeepseekKey" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-[10px] font-bold shadow-sm">
            <Sparkles class="w-3 h-3 text-emerald-600 fill-current" />
            ✨ DeepSeek 联机加速
          </span>
          <span v-else-if="apiHealth.hasGeminiKey" class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-[10px] font-bold shadow-sm">
            <Sparkles class="w-3 h-3 text-indigo-600 fill-current" />
            ✨ AI 深度增强 · 联机加速
          </span>
          <span v-else class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-700 text-[10px] font-semibold">
            <Flame class="w-3 h-3 text-amber-600" />
            高保真沙盒演练
          </span>
        </div>
        <!-- 当前用户信息 + 退出登录 -->
        <div class="flex items-center gap-2 text-xs text-slate-600">
          <span class="hidden sm:inline">{{ currentUsername }}</span>
          <button
            @click="handleLogout"
            class="px-2.5 py-1 rounded-md border border-slate-200 hover:bg-slate-50 text-slate-600 font-semibold"
          >
            退出登录
          </button>
        </div>
      </div>
    </header>

    <!-- Main viewport Container -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-8 md:py-10">
      <!-- Global error banner: shown when a request fails (network down / backend error) -->
      <div
        v-if="globalError"
        class="mb-6 flex items-center justify-between gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
      >
        <span class="flex items-center gap-2">
          <Activity class="w-4 h-4 flex-shrink-0" />
          {{ globalError }}
        </span>
        <button
          class="text-xs font-semibold text-red-600 hover:text-red-800 cursor-pointer"
          @click="globalError = null"
        >
          关闭
        </button>
      </div>

      <!-- Dynamic Mobile View Tabs Selector -->
      <div class="md:hidden flex bg-white border border-slate-200 p-1 rounded-lg mb-6 text-xs font-bold justify-between">
        <button
          @click="activeTab = 'home'; focusReportId = null"
          :class="['flex-1 py-2 rounded text-center', activeTab === 'home' ? 'bg-indigo-600 text-white' : 'text-slate-500']"
        >
          配置
        </button>
        <button
          v-if="currentInterview"
          @click="activeTab = 'interview'"
          :class="['flex-1 py-2 rounded text-center', activeTab === 'interview' ? 'bg-indigo-600 text-white' : 'text-slate-500']"
        >
          模拟
        </button>
        <button
          v-if="focusReportId"
          @click="activeTab = 'report'"
          :class="['flex-1 py-2 rounded text-center', activeTab === 'report' ? 'bg-indigo-600 text-white' : 'text-slate-500']"
        >
          诊断书
        </button>
        <button
          @click="activeTab = 'profile'"
          :class="['flex-1 py-2 rounded text-center', activeTab === 'profile' ? 'bg-indigo-600 text-white' : 'text-slate-500']"
        >
          画像
        </button>
      </div>

      <!-- View Switch router -->
      <div class="transition-all duration-300">
        <HomeView
          v-if="activeTab === 'home'"
          :history-interviews="historyInterviews"
          @start-interview="handleStartInterview"
          @select-historic-report="handleSelectHistoricReport"
        />

        <InterviewView
          v-else-if="activeTab === 'interview' && currentInterview"
          :interview="currentInterview"
          :on-submit-answer="handleSubmitAnswer"
          :on-skip-question="handleSkipQuestion"
          @finish-interview="handleFinishInterview"
        />

        <ReportView
          v-else-if="activeTab === 'report' && focusReportId"
          :interview-id="focusReportId"
          :get-summary-api="getSummaryApi"
          @back-to-home="activeTab = 'home'; focusReportId = null"
        />

        <ProfileView
          v-else-if="activeTab === 'profile'"
          :user-id="currentUserId"
          :get-profile-api="getProfileApi"
        />
      </div>
    </main>

    <!-- Footer credits and state indicator -->
    <footer class="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500 mt-12">
      <div class="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p class="text-left">© 2026 面试突破助手 Project.</p>
        <div class="flex gap-4 text-slate-600">
          <span>前哨Agent协作框架</span>
          <span>•</span>
          <span>RAG工业真实题库</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import type { Interview, InterviewSummary, UserProfile, Evaluation } from './types';
import { api, ApiError, getToken, clearToken } from './api/client';
import LoginView from './components/LoginView.vue';
import HomeView from './components/HomeView.vue';
import InterviewView from './components/InterviewView.vue';
import ReportView from './components/ReportView.vue';
import ProfileView from './components/ProfileView.vue';
import { 
  Sparkles, 
  Activity, 
  Compass, 
  Award, 
  Clipboard, 
  MessageSquare, 
  Flame 
} from 'lucide-vue-next';

const activeTab = ref<'home' | 'interview' | 'report' | 'profile'>('home');
const currentInterview = ref<Interview | null>(null);
const historyInterviews = ref<Interview[]>([]);
const focusReportId = ref<string | null>(null);
const currentUserId = ref<string>('');
const currentUsername = ref<string>('');
const isLoggedIn = ref(false);
const isCheckingAuth = ref(true); // 首次加载时先检查登录状态，避免闪现登录页
const apiHealth = ref<{ status: string; hasGeminiKey: boolean; hasDeepseekKey?: boolean }>({
  status: 'unknown',
  hasGeminiKey: false,
  hasDeepseekKey: false
});
// Short reason shown next to the offline pill (e.g. "无法连接后端服务"),
// separate from globalError which is for one-off action failures.
const offlineReason = ref<string | null>(null);
// One-off action failures (start interview / submit answer etc.) surface here
// instead of only going to console, so the user actually sees what happened.
const globalError = ref<string | null>(null);

// ---------------------------------------------------------------
// Nav-state persistence.
//
// Bug this fixes: activeTab / currentInterview / focusReportId used to live
// only in memory. Any full page reload (manual refresh, or a dev-server
// full-reload while editing files) silently reset them to their initial
// values, which looked like the app "randomly" bouncing back to the home
// tab even though nothing was actually wrong with the interview/report.
//
// Fix: mirror the minimal nav state (which tab + which interview/report id)
// into sessionStorage on every change, and on mount try to restore it by
// re-fetching the matching interview from history instead of trusting
// anything that isn't safe to re-derive from the backend.
// ---------------------------------------------------------------
const NAV_STORAGE_KEY = 'interview-coach-nav-state';

interface PersistedNavState {
  activeTab: 'home' | 'interview' | 'report' | 'profile';
  interviewId: string | null;
  reportId: string | null;
}

function persistNavState() {
  try {
    const state: PersistedNavState = {
      activeTab: activeTab.value,
      interviewId: currentInterview.value?.id ?? null,
      reportId: focusReportId.value
    };
    sessionStorage.setItem(NAV_STORAGE_KEY, JSON.stringify(state));
  } catch {
    // sessionStorage can throw in some embedded/private-browsing contexts;
    // losing nav-state persistence there is not worth surfacing an error for.
  }
}

async function restoreNavState() {
  let saved: PersistedNavState | null = null;
  try {
    const raw = sessionStorage.getItem(NAV_STORAGE_KEY);
    if (raw) saved = JSON.parse(raw);
  } catch {
    saved = null;
  }

  if (!saved || saved.activeTab === 'home') return;

  if (saved.activeTab === 'interview' && saved.interviewId) {
    const found = historyInterviews.value.find(i => i.id === saved!.interviewId);
    if (found && found.status !== 'completed') {
      currentInterview.value = found;
      activeTab.value = 'interview';
      return;
    }
    // The saved interview no longer exists or already finished — fall
    // through and land on home instead of showing a broken interview view.
    return;
  }

  if (saved.activeTab === 'report' && saved.reportId) {
    focusReportId.value = saved.reportId;
    activeTab.value = 'report';
    return;
  }

  if (saved.activeTab === 'profile') {
    activeTab.value = 'profile';
  }
}

function describeError(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.kind === 'network') return e.message;
    if (e.kind === 'http') return `请求失败：${e.message}`;
    return '后端返回了异常数据，请稍后重试';
  }
  return '发生未知错误，请稍后重试';
}

const fetchHealth = async () => {
  try {
    apiHealth.value = await api.getHealth();
    offlineReason.value = null;
  } catch (e) {
    apiHealth.value = { status: 'offline', hasGeminiKey: false, hasDeepseekKey: false };
    offlineReason.value = describeError(e);
  }
};

const checkAuth = async () => {
  const token = getToken();
  if (!token) {
    isCheckingAuth.value = false;
    return;
  }
  try {
    const me = await api.getMe();
    currentUserId.value = me.id;
    currentUsername.value = me.username;
    isLoggedIn.value = true;
  } catch {
    // 令牌失效（后端重启/过期），清掉重新登录
    clearToken();
  } finally {
    isCheckingAuth.value = false;
  }
};

const handleLoginSuccess = async (payload: { userId: string; username: string }) => {
  currentUserId.value = payload.userId;
  currentUsername.value = payload.username;
  isLoggedIn.value = true;
  await fetchHistory();
};

const handleLogout = async () => {
  try {
    await api.logout();
  } catch {
    // 退出登录接口失败也不阻塞前端登出，本地状态照样清空
  }
  clearToken();
  isLoggedIn.value = false;
  currentUserId.value = '';
  currentUsername.value = '';
  currentInterview.value = null;
  activeTab.value = 'home';
  historyInterviews.value = [];
};

const fetchHistory = async () => {
  try {
    historyInterviews.value = await api.getHistory();
  } catch (e) {
    globalError.value = `加载历史记录失败：${describeError(e)}`;
  }
};

// Keep sessionStorage in sync with navigation state. Runs after the initial
// restore too, but restoreNavState only ever sets values that persistNavState
// would write right back out, so this is a no-op in that case.
watch([activeTab, currentInterview, focusReportId], persistNavState);

onMounted(async () => {
  fetchHealth();
  await checkAuth();
  if (isLoggedIn.value) {
    await fetchHistory();
    await restoreNavState();
  }
});

const handleStartInterview = async (config: {
  targetCompany: string;
  targetPosition: string;
  techStack: string[];
  interviewMode: 'technical' | 'behavioral' | 'stress';
}) => {
  try {
    const interviewData = await api.createInterview({ userId: currentUserId.value, ...config });
    currentInterview.value = interviewData;
    activeTab.value = 'interview';

    // 启动面试：后端会调用 LLM 并行生成 3 道题，约需 20-60 秒
    // 前端已设 120s 超时，不需要重试
    const startedData = await api.startInterview(interviewData.id);
    currentInterview.value = startedData;
    fetchHistory();
  } catch (e) {
    globalError.value = `创建/开始面试失败：${describeError(e)}。可以返回首页重新点击"开始面试"。`;
    // Roll back the optimistic tab switch so the user isn't stuck on a blank interview view
    activeTab.value = 'home';
    currentInterview.value = null;
  }
};

const handleSubmitAnswer = async (questionId: string, answer: string) => {
  if (!currentInterview.value) throw new Error('No active interview session');

  const result = await api.submitAnswer(currentInterview.value.id, questionId, answer);

  if (result.evaluation && currentInterview.value) {
    const updatedQs = currentInterview.value.questions?.map(q => {
      if (q.id === questionId) {
        return { ...q, userAnswer: answer, evaluation: result.evaluation as Evaluation };
      }
      return q;
    });
    currentInterview.value = { ...currentInterview.value, questions: updatedQs };
  }

  return result;
};

const handleSkipQuestion = async () => {
  if (!currentInterview.value) return;
  try {
    const result = await api.skipQuestion(currentInterview.value.id);
    // 更新当前面试对象中的 questions 数组（如果有评估）
    return result;
  } catch (e) {
    globalError.value = `跳过题目失败：${describeError(e)}`;
    throw e;
  }
};

const handleFinishInterview = () => {
  if (currentInterview.value) {
    focusReportId.value = currentInterview.value.id;
    activeTab.value = 'report';
    currentInterview.value = null;
    fetchHistory();
  }
};

const handleSelectHistoricReport = (id: string) => {
  focusReportId.value = id;
  activeTab.value = 'report';
};

const getSummaryApi = (id: string): Promise<InterviewSummary> => api.getSummary(id);

const getProfileApi = (id: string): Promise<UserProfile> => api.getProfile(id);
</script>
