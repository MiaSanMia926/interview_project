<template>
  <div class="space-y-10">
    <!-- Hero Welcome -->
    <div class="relative overflow-hidden bg-gradient-to-r from-indigo-50/70 via-slate-50 to-indigo-50/70 border border-indigo-100 rounded-2xl p-6 lg:p-8 flex flex-col md:flex-row items-center justify-between gap-6">
      <div class="space-y-3 max-w-xl text-left">
        <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-semibold">
          <Sparkles class="w-3.5 h-3.5 text-indigo-600" />
          AI 多 Agent 模拟面试 4.0
        </div>
        <h2 class="text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight">
          面试突破助手：大厂智能直通车
        </h2>
        <p class="text-sm text-slate-600 leading-relaxed">
          本项目基于 RAG 面试真题库与 Multi-Agent 协作，由<b>面试官 Agent </b>为您进行多轮细节追问，并由<b>评估专家 Agent </b>为您产生高客观度、多维度的可复现评分与个性化知识图谱。
        </p>
      </div>
      <div class="flex-shrink-0 grid grid-cols-2 gap-3 w-full md:w-auto">
        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center text-center">
          <Shield class="w-5 h-5 text-emerald-600 mb-1" />
          <span class="text-[10px] text-slate-500">评估维度</span>
          <span class="text-sm font-bold text-slate-800">4 维量化</span>
        </div>
        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center text-center">
          <Compass class="w-5 h-5 text-indigo-600 mb-1" />
          <span class="text-[10px] text-slate-500">核心架构</span>
          <span class="text-sm font-bold text-slate-800">GMP / B+ 树</span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Left Column: Config Panel -->
      <div class="lg:col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
        <h3 class="text-lg font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
          <Clipboard class="w-5 h-5 text-indigo-600" />
          新建模拟面试配置
        </h3>

        <div class="space-y-5">
          <!-- Target Company -->
          <div class="space-y-2">
            <label class="text-xs font-semibold text-slate-500 block text-left">目标公司：</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="company in DEFAULT_COMPANIES"
                :key="company"
                @click="selectedCompany = company; customCompany = ''"
                :class="[
                  'px-3 py-1 rounded text-xs transition-all border cursor-pointer',
                  selectedCompany === company && !customCompany
                    ? 'bg-indigo-600 text-white font-medium border-indigo-600 shadow-sm'
                    : 'bg-slate-50 hover:bg-slate-100 text-slate-600 border-slate-200'
                ]"
              >
                {{ company }}
              </button>
            </div>
            <input
              type="text"
              placeholder="不在列表？手动输入目标公司"
              v-model="customCompany"
              class="w-full bg-slate-50 border border-slate-200 rounded px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 focus:bg-white transition-all placeholder:text-slate-400"
            />
          </div>

          <!-- Target Position -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <label class="text-xs font-semibold text-slate-500 block text-left">目标职位：</label>
              <span v-if="positionsLoading" class="text-[10px] text-indigo-500 flex items-center gap-1">
                <Sparkles class="w-3 h-3 animate-pulse" />
                AI 正在根据「{{ customCompany.trim() || selectedCompany }}」推荐职位…
              </span>
              <span v-else-if="positionsError" class="text-[10px] text-slate-400">
                AI 推荐暂不可用，已使用默认职位列表
              </span>
              <span v-else-if="aiPositions.length" class="text-[10px] text-emerald-600">
                含 {{ aiPositions.length }} 个 AI 推荐职位
              </span>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <button
                v-for="pos in positionOptions"
                :key="pos"
                @click="selectedPosition = pos; customPosition = ''"
                :class="[
                  'px-3 py-1.5 rounded text-xs transition-all border text-left flex items-center gap-1.5 cursor-pointer',
                  selectedPosition === pos && !customPosition
                    ? 'bg-indigo-600 text-white font-medium border-indigo-600 shadow-sm'
                    : aiPositions.includes(pos)
                      ? 'bg-emerald-50/60 hover:bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-slate-50 hover:bg-slate-100 text-slate-600 border-slate-200'
                ]"
              >
                <User class="w-3.5 h-3.5 flex-shrink-0 opacity-75" />
                <span class="truncate">{{ pos }}</span>
              </button>
            </div>
            <input
              type="text"
              placeholder="不在列表？手动输入目标职位"
              v-model="customPosition"
              class="w-full bg-slate-50 border border-slate-200 rounded px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-indigo-500 focus:bg-white transition-all placeholder:text-slate-400"
            />
          </div>

          <!-- Tech Stacks -->
          <div class="space-y-2">
            <label class="text-xs font-semibold text-slate-500 block text-left">
              涵盖专业能力与考点：<span class="text-slate-400 font-normal">（可多选，生成考点深度融合）</span>
            </label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="tech in DEFAULT_TECH_STACKS"
                :key="tech"
                @click="handleTechClick(tech)"
                :class="[
                  'px-2.5 py-1 rounded-full text-xs transition-all border cursor-pointer',
                  selectedTechs.includes(tech)
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-300 font-medium'
                    : 'bg-slate-50 hover:bg-slate-100 text-slate-600 border-slate-200'
                ]"
              >
                {{ tech }}
              </button>
            </div>
          </div>

          <!-- Mode selection -->
          <div class="space-y-2">
            <label class="text-xs font-semibold text-slate-500 block text-left">面试模式：</label>
            <div class="grid grid-cols-3 gap-3">
              <button
                @click="mode = 'technical'"
                :class="[
                  'p-3 rounded-lg border text-left space-y-1 transition-all cursor-pointer',
                  mode === 'technical'
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-900 font-semibold'
                    : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-600'
                ]"
              >
                <p class="text-xs font-bold">专业核心问答</p>
                <p class="text-[10px] opacity-75">针对性覆盖核心岗位原理与业务解析</p>
              </button>
              <button
                @click="mode = 'behavioral'"
                :class="[
                  'p-3 rounded-lg border text-left space-y-1 transition-all cursor-pointer',
                  mode === 'behavioral'
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-900 font-semibold'
                    : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-600'
                ]"
              >
                <p class="text-xs font-bold">深度追问剖析</p>
                <p class="text-[10px] opacity-75">一问一追，深挖回答中的细节与盲区</p>
              </button>
              <button
                @click="mode = 'stress'"
                :class="[
                  'p-3 rounded-lg border text-left space-y-1 transition-all cursor-pointer',
                  mode === 'stress'
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-900 font-semibold'
                    : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-600'
                ]"
              >
                <p class="text-xs font-bold">高压实战演练</p>
                <p class="text-[10px] opacity-75">挑战复杂危机情景推演与应变决策力</p>
              </button>
            </div>
          </div>

          <button
            @click="handleSubmit"
            class="w-full bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white text-sm font-bold py-3 px-4 rounded-lg shadow-md flex items-center justify-center gap-2 cursor-pointer group transition-all"
          >
            <Play class="w-4 h-4 fill-current group-hover:scale-110 transition-transform" />
            开启模拟面试实战
          </button>
        </div>
      </div>

      <!-- Right Column: History & Profile Overview -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between h-full">
        <div class="space-y-6 w-full">
          <h3 class="text-lg font-bold text-slate-800 flex items-center gap-2 border-b border-slate-100 pb-3">
            <Award class="w-5 h-5 text-emerald-600" />
            历史演练报告存档
          </h3>

          <div v-if="historyInterviews.length === 0" class="text-center py-12 text-slate-400 space-y-2">
            <Clock class="w-8 h-8 mx-auto stroke-1 text-slate-300" />
            <p class="text-xs">暂无历史模拟记录</p>
          </div>
          <div v-else class="space-y-3 max-h-[360px] overflow-y-auto pr-1">
            <div
              v-for="interview in historyInterviews"
              :key="interview.id"
              @click="$emit('select-historic-report', interview.id)"
              class="group bg-slate-50 hover:bg-slate-100/70 border border-slate-200 hover:border-indigo-500/50 p-3 rounded-lg cursor-pointer transition-all flex items-center justify-between shadow-sm"
            >
              <div class="space-y-1 text-left">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-bold text-slate-700 group-hover:text-indigo-600 transition-colors">
                    {{ interview.targetCompany }}
                  </span>
                  <span class="text-[9px] text-slate-400">
                    {{ interview.createdAt.substring(5, 10) }}
                  </span>
                </div>
                <p class="text-[10px] text-slate-500 truncate max-w-[150px]">
                  {{ interview.targetPosition }}
                </p>
                <div class="flex gap-1 flex-wrap">
                  <span v-for="t in interview.techStack.slice(0, 3)" :key="t" class="text-[8px] bg-slate-200/60 text-slate-600 px-1.5 py-0.5 rounded">
                    {{ t }}
                  </span>
                </div>
              </div>
              
              <div class="text-right flex-shrink-0">
                <div v-if="interview.status === 'completed' && interview.overallScore" class="bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded text-center">
                  <span class="text-xs font-bold text-emerald-700 block">{{ interview.overallScore}}</span>
                  <span class="text-[7px] text-emerald-600 block leading-none">综合分</span>
                </div>
                <span v-else class="text-[9px] bg-amber-50 border border-amber-200 text-amber-700 px-2 py-0.5 rounded">
                  进行中
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="border-t border-slate-200 pt-5 mt-6 w-full">
          <p class="text-[10px] text-slate-500 leading-relaxed text-left">
            <b>💡 学习提示：</b>
            系统已为您预置了覆盖程序员及非程序员的极高质量模拟档案（如<b>“小红书 - 产品经理 (PM)”</b>和<b>“字节跳动 - 后端开发工程师”</b>）。推荐您点击右侧历史列表，一键体验极具视觉冲击力的多维度诊断书！
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { DEFAULT_COMPANIES, DEFAULT_POSITIONS, DEFAULT_TECH_STACKS } from '../data';
import type { Interview } from '../types';
import { api } from '../api/client';
import { Play, Clipboard, Compass, Award, Shield, User, Sparkles, Clock } from 'lucide-vue-next';

interface HomeViewProps {
  historyInterviews: Interview[];
}

defineProps<HomeViewProps>();

const emit = defineEmits<{
  (e: 'start-interview', config: {
    targetCompany: string;
    targetPosition: string;
    techStack: string[];
    interviewMode: 'technical' | 'behavioral' | 'stress';
  }): void;
  (e: 'select-historic-report', interviewId: string): void;
}>();

const selectedCompany = ref('字节跳动');
const customCompany = ref('');
const selectedPosition = ref('产品经理 (PM)');
const customPosition = ref('');
const selectedTechs = ref<string[]>(['产品规划与全生命周期', '用户需求深挖与体验']);
const mode = ref<'technical' | 'behavioral' | 'stress'>('technical');

// AI 职位推荐：根据目标公司异步补充职位选项，不阻塞主流程，失败静默回退到默认列表
const aiPositions = ref<string[]>([]);
const positionsLoading = ref(false);
const positionsError = ref(false);
let positionsRequestSeq = 0;
let debounceTimer: ReturnType<typeof setTimeout> | undefined;

const positionOptions = computed(() => {
  // AI 推荐职位排在前面，去重后再拼默认列表，避免选项跳动导致误触
  const merged = [...aiPositions.value, ...DEFAULT_POSITIONS];
  return Array.from(new Set(merged));
});

const fetchAiPositions = async (company: string) => {
  const seq = ++positionsRequestSeq;
  positionsLoading.value = true;
  positionsError.value = false;
  try {
    const result = await api.suggestPositions(company);
    if (seq !== positionsRequestSeq) return; // 已有更新的请求，丢弃过期结果
    aiPositions.value = (result.positions || []).filter(p => p && p.trim());
  } catch {
    if (seq !== positionsRequestSeq) return;
    aiPositions.value = [];
    positionsError.value = true;
  } finally {
    if (seq === positionsRequestSeq) positionsLoading.value = false;
  }
};

watch(
  () => customCompany.value.trim() || selectedCompany.value,
  (company) => {
    if (!company) return;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => fetchAiPositions(company), 500);
  },
  { immediate: true }
);

const handleTechClick = (tech: string) => {
  if (selectedTechs.value.includes(tech)) {
    if (selectedTechs.value.length > 1) {
      selectedTechs.value = selectedTechs.value.filter(t => t !== tech);
    }
  } else {
    selectedTechs.value = [...selectedTechs.value, tech];
  }
};

const handleSubmit = () => {
  emit('start-interview', {
    targetCompany: customCompany.value.trim() || selectedCompany.value,
    targetPosition: customPosition.value.trim() || selectedPosition.value,
    techStack: selectedTechs.value,
    interviewMode: mode.value
  });
};
</script>
