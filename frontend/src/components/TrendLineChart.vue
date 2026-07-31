<template>
  <div class="relative w-full h-[220px] flex flex-col justify-end select-none" ref="containerRef">
    <!-- SVG Chart Container -->
    <svg 
      viewBox="0 0 500 220" 
      class="w-full h-full"
    >
      <!-- Grid Lines and Labels -->
      <g v-for="gridVal in [0, 20, 40, 60, 80, 100]" :key="gridVal">
        <line
          :x1="margin.left"
          :y1="getY(gridVal)"
          :x2="500 - margin.right"
          :y2="getY(gridVal)"
          stroke="#E2E8F0"
          :stroke-width="gridVal === 60 || gridVal === 80 ? '1.5' : '1'"
          :stroke-dasharray="gridVal === 60 || gridVal === 80 ? '4 4' : 'none'"
        />
        <!-- Left Y-Axis Label -->
        <text
          :x="margin.left - 8"
          :y="getY(gridVal) + 3"
          fill="#94A3B8"
          font-size="9"
          font-family="monospace"
          text-anchor="end"
        >
          {{ gridVal }}
        </text>
      </g>

      <!-- Benchmark indicator texts -->
      <text
        :x="500 - margin.right"
        :y="getY(60) - 5"
        fill="#EF4444"
        font-size="8"
        font-weight="bold"
        text-anchor="end"
      >
        及格线 (60分)
      </text>
      <text
        :x="500 - margin.right"
        :y="getY(80) - 5"
        fill="#10B981"
        font-size="8"
        font-weight="bold"
        text-anchor="end"
      >
        大厂线 (80分)
      </text>

      <!-- Connecting Polyline -->
      <polyline
        v-if="points.length > 0"
        :points="pointsString"
        fill="none"
        stroke="#3B82F6"
        stroke-width="3"
        stroke-linecap="round"
        stroke-linejoin="round"
      />

      <!-- Dots on hover nodes -->
      <g v-for="(p, idx) in points" :key="idx">
        <!-- Interactive Invisible Large Hover Circles -->
        <circle
          :cx="p.x"
          :cy="p.y"
          r="14"
          fill="transparent"
          class="cursor-pointer"
          @mouseenter="hoveredIndex = idx"
          @mouseleave="hoveredIndex = null"
        />
        <!-- Visual Inner Dots -->
        <circle
          :cx="p.x"
          :cy="p.y"
          :r="hoveredIndex === idx ? 7 : 4.5"
          :fill="hoveredIndex === idx ? '#1D4ED8' : '#3B82F6'"
          stroke="#FFFFFF"
          stroke-width="1.5"
          class="transition-all duration-150"
        />
      </g>

      <!-- Bottom X-Axis Labels (Dates) -->
      <text
        v-for="(item, idx) in data"
        :key="'date-' + idx"
        :x="getX(idx)"
        :y="220 - 6"
        fill="#64748B"
        font-size="9"
        font-weight="500"
        text-anchor="middle"
      >
        {{ item.date }}
      </text>
    </svg>

    <!-- Custom Floating Tooltip HTML Overlay -->
    <div 
      v-if="hoveredIndex !== null && data[hoveredIndex]"
      class="absolute bg-slate-900 text-white text-left p-3 rounded-lg shadow-xl border border-slate-800 pointer-events-none transition-all duration-150 z-20 text-xs w-[180px]"
      :style="{
        left: `${(getX(hoveredIndex) / 500) * 100}%`,
        bottom: `${((220 - getY(data[hoveredIndex].score)) / 220) * 100 + 4}%`,
        transform: 'translateX(-50%)'
      }"
    >
      <p class="text-slate-400 text-[10px] mb-1 font-mono">
        {{ data[hoveredIndex].date }} · {{ data[hoveredIndex].title }}
      </p>
      <p class="font-extrabold text-emerald-400">
        综合得分：{{ data[hoveredIndex].score }} 分
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface TrendPoint {
  date: string;
  score: number;
  title: string;
}

interface TrendLineChartProps {
  data: TrendPoint[];
}

const props = withDefaults(defineProps<TrendLineChartProps>(), {
  data: () => []
});

const containerRef = ref<HTMLDivElement | null>(null);
const hoveredIndex = ref<number | null>(null);

const margin = { top: 20, right: 35, bottom: 25, left: 25 };
const chartWidth = 500;
const chartHeight = 220;

const getX = (idx: number) => {
  const L = props.data.length;
  if (L <= 1) return margin.left + (chartWidth - margin.left - margin.right) / 2;
  const step = (chartWidth - margin.left - margin.right) / (L - 1);
  return margin.left + idx * step;
};

const getY = (score: number) => {
  const minScore = 0;
  const maxScore = 100;
  const usableHeight = chartHeight - margin.top - margin.bottom;
  const ratio = (score - minScore) / (maxScore - minScore);
  return margin.top + usableHeight - ratio * usableHeight;
};

const points = computed(() => {
  return props.data.map((item, idx) => ({
    x: getX(idx),
    y: getY(item.score)
  }));
});

const pointsString = computed(() => {
  return points.value.map(p => `${p.x},${p.y}`).join(' ');
});
</script>
