<template>
  <div v-if="isLoading" class="flex flex-col items-center justify-center h-[400px] text-center space-y-3">
    <div class="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
    <p class="text-sm font-medium text-slate-500">正在提炼智能能力画像...</p>
  </div>

  <div v-else-if="!profile" class="text-center py-12 space-y-3">
    <p class="text-sm text-red-500">⚠️ {{ loadError ?? '提炼画像失败，请重试。' }}</p>
    <button
      @click="loadProfile"
      class="bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold py-2 px-4 rounded transition-colors cursor-pointer"
    >
      重新加载
    </button>
  </div>

  <div v-else class="space-y-10 text-left">
    <!-- Upper banner: User header with stats card -->
    <div class="bg-gradient-to-r from-indigo-50/70 via-slate-50 to-indigo-50/70 border border-indigo-100 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-6">
      <div class="flex items-center gap-4 text-left">
        <div class="w-14 h-14 rounded-full bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center text-white font-extrabold text-2xl shadow-xl shadow-indigo-500/15">
          {{ profile.username.charAt(0) }}
        </div>
        <div class="space-y-1">
          <h3 class="text-xl font-bold text-slate-800 flex items-center gap-2">
            {{ profile.username }}
            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-amber-700 text-[10px] font-semibold">
              <Flame class="w-3 h-3 fill-current" />
              大厂攻坚 3 天连刷
            </span>
          </h3>
          <p class="text-xs text-slate-600">{{ userSubtitle }} · 候选人</p>
        </div>
      </div>

      <!-- Global summary count -->
      <div class="flex items-center gap-6 w-full md:w-auto border-t md:border-t-0 border-slate-200 pt-4 md:pt-0">
        <div class="space-y-1">
          <span class="text-[10px] text-slate-400 font-bold block uppercase">总模拟面试数</span>
          <span class="text-2xl font-black text-indigo-700 block">{{ profile.totalInterviews }} 次</span>
        </div>
        <div class="w-px h-10 bg-slate-200"></div>
        <div class="space-y-1">
          <span class="text-[10px] text-slate-400 font-bold block uppercase">全链路平均分</span>
          <span class="text-2xl font-black text-emerald-700 block">{{ profile.averageScore }}</span>
        </div>
      </div>
    </div>

    <!-- Grid: Trend Line and Challenges -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Trend line -->
      <div class="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div>
          <h4 class="text-sm font-bold text-slate-800 flex items-center gap-2">
            <TrendingUp class="w-4 h-4 text-indigo-600" />
            历史演进分数趋势图
          </h4>
          <p class="text-[11px] text-slate-500 mt-1">展示您在近几次大厂演练中的进阶幅度。多维持续练习可以大幅平稳分数。</p>
        </div>
        <TrendLineChart :data="profile.trendData" />
      </div>

      <!-- Challenge list checklist -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4 flex flex-col justify-between">
        <div>
          <h4 class="text-sm font-bold text-slate-800 flex items-center gap-2">
            <CheckSquare class="w-4 h-4 text-indigo-600" />
            当前『黄金破局』打卡挑战
          </h4>
          <p class="text-[11px] text-slate-500 mt-1">评估专家为您当前弱项定制的技术难关。攻破即可解锁大厂入场券。</p>
        </div>

        <div class="space-y-2.5 my-4">
          <div 
            v-for="item in challenges"
            :key="item.id" 
            @click="toggleChallenge(item.id)"
            :class="[
              'flex gap-3 p-2.5 rounded-lg border transition-all cursor-pointer',
              item.done 
                ? 'bg-emerald-50/40 border-emerald-200 text-slate-500 shadow-sm' 
                : 'bg-slate-50 border-slate-200 hover:border-slate-300 hover:bg-slate-100/70 text-slate-700 shadow-sm'
            ]"
          >
            <div :class="[
              'w-4 h-4 rounded mt-0.5 flex-shrink-0 flex items-center justify-center border transition-all',
              item.done 
                ? 'bg-emerald-600 border-emerald-500 text-white font-black text-[10px]' 
                : 'border-slate-300'
            ]">
              {{ item.done ? '✓' : '' }}
            </div>
            <span :class="['text-[10px] leading-tight text-left', item.done ? 'line-through' : '']">{{ item.text }}</span>
          </div>
        </div>

        <div class="border-t border-slate-100 pt-3">
          <span class="text-[9px] text-slate-500 flex items-center gap-1">
            <Sparkles class="w-3.5 h-3.5 text-indigo-600" />
            完成后系统会自动刷新关联图谱的加分评级
          </span>
        </div>
      </div>
    </div>

    <!-- Radar Chart: 四维度能力分布 -->
    <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
      <div>
        <h4 class="text-sm font-bold text-slate-800 flex items-center gap-2">
          <Award class="w-4 h-4 text-indigo-600" />
          四维度能力雷达图
        </h4>
        <p class="text-[11px] text-slate-500 mt-1">基于历次面试评估的准确性、完整性、逻辑性、表达能力四个维度的平均得分。</p>
      </div>
      <RadarChart :data="profile.radarData" />
    </div>

    <!-- Grid Knowledge Graph -->
    <div class="space-y-4">
      <div>
        <h4 class="text-sm font-bold text-slate-800 flex items-center gap-2">
          <Compass class="w-4 h-4 text-indigo-600" />
          技术缺陷链传导拓扑图
        </h4>
        <p class="text-[11px] text-slate-500 mt-1">此视图直观展现由评估专家 Agent 归纳出的底层弱项缺陷，如何通过链路向其他关联节点传导发生故障演进。</p>
      </div>
      <KnowledgeGraph :data="profile.knowledgeGraph" />
    </div>

    <!-- Global Recommendations lists -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div class="bg-emerald-50/25 rounded-xl border border-emerald-200 p-6 space-y-3.5 text-left shadow-sm">
        <h4 class="text-sm font-bold text-emerald-800 flex items-center gap-2">
          📊 本阶段全维度技术底子优势
        </h4>
        <div class="space-y-3 pt-1">
          <p v-for="(s, i) in profile.strengths" :key="i" class="text-xs text-slate-700 leading-relaxed">• {{ s }}</p>
        </div>
      </div>

      <div class="bg-red-50/25 rounded-xl border border-red-200 p-6 space-y-3.5 text-left shadow-sm">
        <h4 class="text-sm font-bold text-red-800 flex items-center gap-2">
          🚨 必须要破除的重大隐患点
        </h4>
        <div class="space-y-3 pt-1">
          <p v-for="(w, i) in profile.weaknesses" :key="i" class="text-xs text-slate-700 leading-relaxed">• {{ w }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import type { UserProfile } from '../types';
import { Award, Flame, CheckSquare, Sparkles, TrendingUp, Compass } from 'lucide-vue-next';
import TrendLineChart from './TrendLineChart.vue';
import RadarChart from './RadarChart.vue';
import KnowledgeGraph from './KnowledgeGraph.vue';
import { ApiError } from '../api/client';

interface ProfileViewProps {
  userId: string;
  getProfileApi: (id: string) => Promise<UserProfile>;
}

const props = defineProps<ProfileViewProps>();

const profile = ref<UserProfile | null>(null);
const isLoading = ref(true);
const loadError = ref<string | null>(null);

// 打卡挑战来自后端 PlannerAgent 生成的学习计划（用 ref 以支持 toggle 交互）
const challenges = ref<{ id: number; text: string; done: boolean; priority: string }[]>([]);

// 勾选状态只存在于本组件的内存里；一旦用户切换到别的顶部 Tab，App.vue 会把
// ProfileView 整个卸载重建（v-else-if 路由），onMounted 重新拉取 profile 会让
// 所有勾选被清空成 done:false，看起来像是"打卡"丢失了。这里用 sessionStorage
// 按 userId 持久化已勾选的挑战 id，恢复时把它们重新标记为完成。
const CHALLENGES_DONE_KEY = (userId: string) => `interview-coach-challenges-done:${userId}`;

function loadDoneIds(userId: string): Set<number> {
  try {
    const raw = sessionStorage.getItem(CHALLENGES_DONE_KEY(userId));
    if (!raw) return new Set();
    return new Set(JSON.parse(raw));
  } catch {
    return new Set();
  }
}

function saveDoneIds(userId: string, ids: Set<number>) {
  try {
    sessionStorage.setItem(CHALLENGES_DONE_KEY(userId), JSON.stringify(Array.from(ids)));
  } catch {
    // sessionStorage 不可用时，勾选状态退化为仅当前会话内存有效，不影响主流程
  }
}

watch(profile, (p) => {
  const doneIds = loadDoneIds(props.userId);
  if (p?.challenges?.length) {
    challenges.value = p.challenges.map(c => ({
      id: c.id,
      text: c.text,
      done: doneIds.has(c.id),
      priority: c.priority || 'medium',
    }));
  } else {
    // 兜底：后端尚未返回挑战时显示占位
    challenges.value = [
      { id: 1, text: '完成一次完整的模拟面试获取 AI 个性化挑战', done: doneIds.has(1), priority: 'high' },
      { id: 2, text: '回顾评估报告中的改进建议并做专项练习', done: doneIds.has(2), priority: 'medium' },
    ];
  }
}, { immediate: true });

// 动态副标题：取最近一次面试的目标职位
const userSubtitle = computed(() => {
  if (profile.value?.trendData?.length) {
    // trendData[0] 是最近一次面试，title 格式为 "公司 职位" 或 "面试"
    const title = profile.value.trendData[0].title;
    if (title && title !== '面试') return title;
  }
  return '技术候选人';
});

const loadProfile = async () => {
  isLoading.value = true;
  loadError.value = null;
  try {
    profile.value = await props.getProfileApi(props.userId);
  } catch (err) {
    console.error('Failed to load profile:', err);
    profile.value = null;
    loadError.value = err instanceof ApiError && err.kind === 'network'
      ? '连不上后端服务，请确认服务是否已启动。'
      : '提炼画像失败，请重试。';
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  loadProfile();
});

watch(() => props.userId, () => {
  loadProfile();
});

const toggleChallenge = (id: number) => {
  challenges.value = challenges.value.map(c => c.id === id ? { ...c, done: !c.done } : c);
  const doneIds = new Set(challenges.value.filter(c => c.done).map(c => c.id));
  saveDoneIds(props.userId, doneIds);
};
</script>
