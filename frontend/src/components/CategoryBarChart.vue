<template>
  <div class="space-y-4 py-2">
    <div 
      v-for="(item, index) in data" 
      :key="item.category" 
      class="space-y-1.5"
    >
      <div class="flex justify-between items-center text-xs font-bold">
        <span class="text-slate-700 flex items-center gap-2">
          <!-- Color Dot Indicator -->
          <span 
            class="w-2.5 h-2.5 rounded-full flex-shrink-0" 
            :style="{ backgroundColor: getColor(index) }"
          ></span>
          {{ item.category }}
        </span>
        <div class="flex items-center gap-2">
          <!-- Grade badge -->
          <span 
            :class="[
              'text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wide',
              item.score >= 85 
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : item.score >= 70 
                  ? 'bg-indigo-50 text-indigo-700 border border-indigo-100'
                  : 'bg-amber-50 text-amber-700 border border-amber-200'
            ]"
          >
            {{ getGradeLabel(item.score) }}
          </span>
          <span class="text-slate-950 font-mono">{{ item.score }}分</span>
        </div>
      </div>
      
      <!-- Progress Bar Track -->
      <div class="w-full bg-slate-100 h-3.5 rounded-lg overflow-hidden border border-slate-200/50 flex items-center p-[2px]">
        <div 
          class="h-full rounded-md transition-all duration-1000 ease-out"
          :style="{ 
            width: `${item.score}%`, 
            backgroundColor: getColor(index),
            boxShadow: 'inset 0 1px 1px rgba(255,255,255,0.25)' 
          }"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface BarDataPoint {
  category: string;
  score: number;
}

interface CategoryBarChartProps {
  data: BarDataPoint[];
}

defineProps<CategoryBarChartProps>();

const COLORS = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EC4899', '#6366F1'];

const getColor = (index: number) => {
  return COLORS[index % COLORS.length];
};

const getGradeLabel = (score: number) => {
  if (score >= 85) return '精通 (Expert)';
  if (score >= 70) return '掌握 (Advanced)';
  if (score >= 55) return '熟悉 (Intermediate)';
  return '需提升 (Need Work)';
};
</script>
