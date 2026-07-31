<template>
  <div class="w-full h-[280px] flex items-center justify-center relative">
    <svg 
      viewBox="0 0 320 320" 
      class="w-full h-full max-w-[280px] max-h-[280px]"
    >
      <!-- Background Concentric Grid Lines -->
      <polygon
        v-for="level in [20, 40, 60, 80, 100]"
        :key="level"
        :points="getGridPoints(level)"
        fill="none"
        stroke="#E2E8F0"
        stroke-width="1"
        :stroke-dasharray="level === 100 ? 'none' : '2 2'"
      />

      <!-- Concentric circle labels -->
      <text
        v-for="level in [20, 60, 100]"
        :key="'lbl-' + level"
        :x="center.x"
        :y="center.y - (radius * level) / 100 + 4"
        fill="#94A3B8"
        font-size="8"
        font-family="monospace"
        text-anchor="middle"
        class="select-none"
      >
        {{ level }}
      </text>

      <!-- Axis lines from center to outer bounds -->
      <line
        v-for="(point, idx) in outerPoints"
        :key="'line-' + idx"
        :x1="center.x"
        :y1="center.y"
        :x2="point.x"
        :y2="point.y"
        stroke="#E2E8F0"
        stroke-width="1"
      />

      <!-- Filled Radar Area Polygon -->
      <polygon
        :points="radarPointsString"
        fill="#10B981"
        fill-opacity="0.2"
        stroke="#10B981"
        stroke-width="2"
      />

      <!-- Radar area corner dots -->
      <circle
        v-for="(point, idx) in radarPoints"
        :key="'dot-' + idx"
        :cx="point.x"
        :cy="point.y"
        r="4"
        fill="#10B981"
        stroke="#FFFFFF"
        stroke-width="1.5"
      />

      <!-- Axis text labels -->
      <text
        v-for="(item, idx) in data"
        :key="'text-' + idx"
        :x="getLabelPosition(idx).x"
        :y="getLabelPosition(idx).y"
        fill="#475569"
        font-size="11"
        font-weight="600"
        :text-anchor="getLabelPosition(idx).align"
        class="select-none font-sans"
      >
        {{ item.name }}
      </text>
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface RadarDataPoint {
  name: string;
  score: number;
  fullMark: number;
}

interface RadarChartProps {
  data: RadarDataPoint[];
}

const props = withDefaults(defineProps<RadarChartProps>(), {
  data: () => []
});

const center = { x: 160, y: 160 };
const radius = 100;

// Dimensions length
const N = computed(() => props.data.length || 4);

// Angles for each dimension (0-indexed, rotated -90 deg so the first axis goes straight up)
const angles = computed(() => {
  const result: number[] = [];
  const n = N.value;
  for (let i = 0; i < n; i++) {
    result.push((2 * Math.PI * i) / n - Math.PI / 2);
  }
  return result;
});

// Calculate background grid polygon points
const getGridPoints = (levelPercentage: number) => {
  const r = (radius * levelPercentage) / 100;
  return angles.value
    .map(angle => {
      const x = center.x + r * Math.cos(angle);
      const y = center.y + r * Math.sin(angle);
      return `${x},${y}`;
    })
    .join(' ');
};

// Points for the outer bound (100% score)
const outerPoints = computed(() => {
  return angles.value.map(angle => ({
    x: center.x + radius * Math.cos(angle),
    y: center.y + radius * Math.sin(angle)
  }));
});

// Points for actual scores
const radarPoints = computed(() => {
  return angles.value.map((angle, idx) => {
    const score = props.data[idx]?.score ?? 0;
    const r = (radius * Math.min(score, 100)) / 100;
    return {
      x: center.x + r * Math.cos(angle),
      y: center.y + r * Math.sin(angle)
    };
  });
});

const radarPointsString = computed(() => {
  return radarPoints.value.map(p => `${p.x},${p.y}`).join(' ');
});

// Positioning of outer text labels with smart alignment offsets
const getLabelPosition = (idx: number) => {
  const angle = angles.value[idx];
  const labelRadius = radius + 20;
  const x = center.x + labelRadius * Math.cos(angle);
  const y = center.y + labelRadius * Math.sin(angle);

  // Determine text-anchor alignment based on quadrant
  let align = 'middle';
  const cos = Math.cos(angle);
  if (cos > 0.1) {
    align = 'start';
  } else if (cos < -0.1) {
    align = 'end';
  }

  // Vertical offsets
  let yOffset = 4;
  const sin = Math.sin(angle);
  if (sin < -0.9) {
    yOffset = -4; // top label
  } else if (sin > 0.9) {
    yOffset = 12; // bottom label
  }

  return { x, y: y + yOffset, align };
};
</script>
