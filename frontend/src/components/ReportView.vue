<template>
  <div v-if="isLoading" class="flex flex-col items-center justify-center h-[400px] text-center space-y-3">
    <div class="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
    <p class="text-sm font-medium text-slate-600">正在生成深度技术诊断书...</p>
    <p class="text-xs text-slate-400">评估专家 Agent 正在梳理各维度得分并进行文字总结</p>
  </div>

  <div v-else-if="!summary" class="text-center py-12 space-y-4">
    <p class="text-sm text-red-500">⚠️ {{ loadError ?? '诊断书生成失败或面试报告不存在。' }}</p>
    <div class="flex items-center justify-center gap-3">
      <button
        @click="loadSummary"
        class="bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold py-2 px-4 rounded transition-colors cursor-pointer"
      >
        重新加载
      </button>
      <button
        @click="$emit('back-to-home')"
        class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold py-2 px-4 rounded transition-colors cursor-pointer"
      >
        返回首页
      </button>
    </div>
  </div>

  <div v-else class="space-y-8 text-left">
    <!-- Header Back controls -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
      <div class="flex items-center gap-3">
        <button
          @click="$emit('back-to-home')"
          class="p-1.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition-colors cursor-pointer"
        >
          <ArrowLeft class="w-4 h-4" />
        </button>
        <div>
          <h2 class="text-xl font-extrabold text-slate-800">大厂技术总监诊断书</h2>
          <p class="text-xs text-slate-400 mt-1">诊断流水号：{{ summary.interviewId.substring(0, 15) }}...</p>
        </div>
      </div>

      <!-- Buttons Group -->
      <div class="flex items-center gap-2">
        <button
          @click="handleCopy"
          class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded text-xs font-bold text-slate-700 flex items-center gap-1.5 transition-colors cursor-pointer"
        >
          <Copy class="w-3.5 h-3.5" />
          {{ copied ? '已复制！' : '复制结果' }}
        </button>
        <button
          @click="printWindow"
          class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded text-xs font-bold text-white flex items-center gap-1.5 transition-colors cursor-pointer shadow-sm shadow-indigo-100"
        >
          <Download class="w-3.5 h-3.5" />
          打印 / 导出 PDF
        </button>
      </div>
    </div>

    <!-- Grid: 3 Numeric score indicators -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
      <div class="bg-white rounded-xl border border-slate-200 p-5 flex items-center justify-between shadow-sm">
        <div class="space-y-1">
          <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">综合面试打分</span>
          <span class="text-3xl font-extrabold text-emerald-600 block">{{ summary.overallScore }}</span>
          <span class="text-[10px] text-slate-500">超越同期 86.4% 候选人</span>
        </div>
        <div class="w-14 h-14 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700 font-extrabold text-lg">
          {{ summary.overallScore >= 80 ? 'A+' : summary.overallScore >= 70 ? 'B+' : 'C' }}
        </div>
      </div>

      <div class="bg-white rounded-xl border border-slate-200 p-5 flex items-center justify-between shadow-sm">
        <div class="space-y-1">
          <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">已回答问题</span>
          <span class="text-3xl font-extrabold text-indigo-600 block">{{ summary.answeredQuestions }} 道</span>
          <span class="text-[10px] text-slate-500">总题目数：{{ summary.totalQuestions }} 题</span>
        </div>
        <div class="w-14 h-14 rounded-full bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-700">
          <BookOpen class="w-6 h-6" />
        </div>
      </div>

      <div class="bg-white rounded-xl border border-slate-200 p-5 flex items-center justify-between shadow-sm">
        <div class="space-y-1">
          <span class="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">面试总时长</span>
          <span class="text-3xl font-extrabold text-amber-600 block">{{ summary.durationMinutes }} 分钟</span>
          <span class="text-[10px] text-slate-500">平均答题：11.5分钟/大题</span>
        </div>
        <div class="w-14 h-14 rounded-full bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
          <Clock class="w-6 h-6" />
        </div>
      </div>
    </div>

    <!-- Grid Charts visualization -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Left chart: Radar -->
      <div class="bg-white rounded-xl border border-slate-200 p-5 space-y-4 shadow-sm">
        <div>
          <h4 class="text-sm font-bold text-slate-800">各维度得分细分（雷达图）</h4>
          <p class="text-[11px] text-slate-500 mt-1">系统从准确、完整、逻辑、表达四个核心方向评判的结果。</p>
        </div>
        <RadarChart :data="radarData" />
      </div>

      <!-- Right chart: Category Bars -->
      <div class="bg-white rounded-xl border border-slate-200 p-5 space-y-4 shadow-sm">
        <div>
          <h4 class="text-sm font-bold text-slate-800">核心知识分类掌握得分（柱状图）</h4>
          <p class="text-[11px] text-slate-500 mt-1">您在此岗位面试的核心技术层级的量化分数指标。</p>
        </div>
        <div class="pt-6">
          <CategoryBarChart :data="barData" />
        </div>
      </div>
    </div>

    <!-- Strengths and Weaknesses text cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <!-- Strengths card -->
      <div class="bg-emerald-50/25 rounded-xl border border-emerald-200 p-6 space-y-4 relative overflow-hidden shadow-sm">
        <div class="absolute top-0 right-0 w-20 h-20 bg-emerald-500/5 rounded-full translate-x-4 -translate-y-4"></div>
        <h4 class="text-sm font-bold text-emerald-800 flex items-center gap-2 border-b border-emerald-100 pb-3">
          <CheckCircle class="w-5 h-5 text-emerald-600 flex-shrink-0" />
          技术总监肯定的三大核心优势
        </h4>
        <div class="space-y-3.5 pt-1">
          <div v-for="(str, idx) in summary.strengths" :key="idx" class="flex gap-2 text-xs leading-relaxed text-slate-700">
            <span class="text-emerald-600 font-bold flex-shrink-0">{{ idx + 1 }}.</span>
            <p>{{ str }}</p>
          </div>
        </div>
      </div>

      <!-- Weaknesses card -->
      <div class="bg-red-50/25 rounded-xl border border-red-200 p-6 space-y-4 relative overflow-hidden shadow-sm">
        <div class="absolute top-0 right-0 w-20 h-20 bg-red-500/5 rounded-full translate-x-4 -translate-y-4"></div>
        <h4 class="text-sm font-bold text-red-800 flex items-center gap-2 border-b border-red-100 pb-3">
          <XCircle class="w-5 h-5 text-red-600 flex-shrink-0" />
          当前在进阶大厂时的核心薄弱点
        </h4>
        <div class="space-y-3.5 pt-1">
          <div v-for="(weak, idx) in summary.weaknesses" :key="idx" class="flex gap-2 text-xs leading-relaxed text-slate-700">
            <span class="text-red-500 font-bold flex-shrink-0">{{ idx + 1 }}.</span>
            <p>{{ weak }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Recommendations Learning plan layout -->
    <div class="bg-white rounded-xl border border-slate-200 p-6 space-y-5 shadow-sm">
      <h4 class="text-sm font-bold text-slate-800 flex items-center gap-2 border-b border-slate-100 pb-3.5">
        <Award class="w-5 h-5 text-indigo-600" />
        个性化订制的专属提升与破局路径
      </h4>

      <div class="space-y-4">
        <div v-for="(rec, idx) in summary.recommendations" :key="idx" class="flex items-start gap-4 p-4 rounded-lg bg-slate-50 border border-slate-200 shadow-sm">
          <div class="w-6 h-6 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-extrabold flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
            {{ idx + 1 }}
          </div>
          <div class="space-y-1 text-left">
            <span class="text-xs font-bold text-slate-800 block">进阶建议阶段 {{ idx + 1 }}</span>
            <p class="text-xs text-slate-600 leading-relaxed text-left">{{ rec }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import type { InterviewSummary } from '../types';
import { Award, Clock, ArrowLeft, CheckCircle, XCircle, BookOpen, Download, Copy } from 'lucide-vue-next';
import RadarChart from './RadarChart.vue';
import CategoryBarChart from './CategoryBarChart.vue';
import { ApiError } from '../api/client';

interface ReportViewProps {
  interviewId: string;
  getSummaryApi: (id: string) => Promise<InterviewSummary>;
}

const props = defineProps<ReportViewProps>();

defineEmits<{
  (e: 'back-to-home'): void;
}>();

const summary = ref<InterviewSummary | null>(null);
const isLoading = ref(true);
const copied = ref(false);
const loadError = ref<string | null>(null);

const loadSummary = async () => {
  isLoading.value = true;
  loadError.value = null;
  try {
    summary.value = await props.getSummaryApi(props.interviewId);
  } catch (err) {
    console.error('Failed to load interview summary:', err);
    summary.value = null;
    loadError.value = err instanceof ApiError && err.kind === 'network'
      ? '连不上后端服务，请确认服务是否已启动。'
      : '诊断书生成失败或面试报告不存在。';
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  loadSummary();
});

watch(() => props.interviewId, () => {
  loadSummary();
});

const handleCopy = () => {
  if (!summary.value) return;
  const text = `🎯 面试突破助手 - 大厂诊断书\n综合得分：${summary.value.overallScore} 分\n\n核心优势：\n${summary.value.strengths.map((s, i) => `${i+1}. ${s}`).join('\n')}\n\n改进方向：\n${summary.value.weaknesses.map((w, i) => `${i+1}. ${w}`).join('\n')}\n\n个性化提升路径：\n${summary.value.recommendations.map((r, i) => `${i+1}. ${r}`).join('\n')}`;
  navigator.clipboard.writeText(text);
  copied.value = true;
  setTimeout(() => {
    copied.value = false;
  }, 2000);
};

const printWindow = () => {
  window.print();
};

const radarData = computed(() => {
  if (!summary.value) return [];
  return [
    { name: '技术准确性', score: summary.value.dimensionSummary.accuracy, fullMark: 100 },
    { name: '要点完整性', score: summary.value.dimensionSummary.completeness, fullMark: 100 },
    { name: '思维逻辑性', score: summary.value.dimensionSummary.logic, fullMark: 100 },
    { name: '沟通表达力', score: summary.value.dimensionSummary.expression, fullMark: 100 }
  ];
});

const barData = computed(() => {
  if (!summary.value) return [];
  return Object.entries(summary.value.categoryScores).map(([key, val]) => ({
    category: key,
    score: val as number
  }));
});
</script>
