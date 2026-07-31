<template>
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Visual map -->
    <div class="lg:col-span-2 bg-slate-900 rounded-xl border border-slate-800 p-5 relative overflow-hidden flex flex-col justify-between min-h-[380px]">
      <div>
        <h4 class="text-sm font-semibold text-slate-300 flex items-center gap-2 mb-2">
          <BookOpen class="w-4 h-4 text-indigo-400" />
          核心知识点及关联链路拓扑
        </h4>
        <p class="text-xs text-slate-400 mb-6">
          系统根据您的答题情况自动梳理的核心技能网。<b>点击圆标</b>即可聚焦观察其生产演进与关联的弱项漏洞。
        </p>
      </div>

      <!-- Dynamic Nodes Mapping inside structured viewport -->
      <div class="relative w-full h-[240px] border border-slate-800 rounded-lg bg-slate-950 flex items-center justify-center overflow-hidden">
        <!-- getCoordinates() computes positions for a 320x240 canvas (centerX=160/centerY=120);
             this inner box is fixed at that same size and centered, so nodes always line up
             correctly regardless of how wide the outer (responsive) panel is. Without this,
             on wide desktop screens all nodes clump toward the left edge, and on very narrow
             phone screens the outer 'weak' nodes can get clipped by overflow-hidden. -->
        <div class="relative w-[320px] h-[240px] flex-shrink-0">
        <!-- Background SVG to draw connection lines -->
        <svg class="absolute inset-0 w-full h-full pointer-events-none z-0">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="15" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#374151" />
            </marker>
            <marker id="arrow-highlight" viewBox="0 0 10 10" refX="15" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#818CF8" />
            </marker>
          </defs>

          <!-- Static layout connections mapped cleanly -->
          <line
            v-for="(link, idx) in data.links"
            :key="`link-${idx}`"
            :x1="getCoordinates(link.source).x"
            :y1="getCoordinates(link.source).y"
            :x2="getCoordinates(link.target).x"
            :y2="getCoordinates(link.target).y"
            :stroke="selectedNodeId && (link.source === selectedNodeId || link.target === selectedNodeId) ? '#818CF8' : '#1F2937'"
            :stroke-width="selectedNodeId && (link.source === selectedNodeId || link.target === selectedNodeId) ? 2 : 1"
            :stroke-dasharray="link.label === '生产故障演进' ? '4 4' : undefined"
            :marker-end="selectedNodeId && (link.source === selectedNodeId || link.target === selectedNodeId) ? 'url(#arrow-highlight)' : 'url(#arrow)'"
            class="transition-all duration-300"
          />
        </svg>

        <!-- Interactive Nodes -->
        <button
          v-for="node in data.nodes"
          :key="node.id"
          @click="handleNodeClick(node.id)"
          :style="{ left: `${getCoordinates(node.id).x}px`, top: `${getCoordinates(node.id).y}px` }"
          :class="[
            'absolute -translate-x-1/2 -translate-y-1/2 px-2.5 py-1 rounded-full text-[10px] font-medium border shadow-lg z-10 cursor-pointer transition-all duration-300 scale-100',
            selectedNodeId === node.id 
              ? 'scale-110 ring-2 ring-indigo-400 ring-offset-2 ring-offset-slate-900' 
              : '',
            getNodeBgClass(node)
          ]"
        >
          {{ node.label }}
        </button>
        </div>
      </div>

      <!-- Legend -->
      <div class="flex justify-center gap-6 mt-2 text-[10px] text-slate-400">
        <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-indigo-950 border border-indigo-500 block"></span>核心基础层</span>
        <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-slate-800 border border-slate-700 block"></span>子技术维度</span>
        <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-red-950 border border-red-500 block"></span>潜在薄弱项</span>
      </div>
    </div>

    <!-- Detail panel on side -->
    <div class="bg-slate-900 rounded-xl border border-slate-800 p-5 flex flex-col justify-between text-left">
      <div v-if="!highlight" class="flex flex-col items-center justify-center h-full text-center py-8">
        <BookOpen class="w-10 h-10 text-slate-600 mb-3 animate-pulse" />
        <p class="text-sm font-medium text-slate-400">暂未选择观察节点</p>
        <p class="text-xs text-slate-500 max-w-[180px] mt-1 mx-auto">
          在左侧拓扑图中点击任意节点，查看其在面试链路上的进阶传导细节
        </p>
      </div>

      <div v-else class="space-y-4 flex-1">
        <div class="border-b border-slate-800 pb-3">
          <span :class="[
            'inline-block px-2 py-0.5 rounded text-[9px] font-semibold mb-1.5',
            highlight.node.group === 'core' ? 'bg-indigo-950 text-indigo-400' :
            highlight.node.group === 'weak' ? 'bg-red-950 text-red-400' : 'bg-slate-800 text-slate-400'
          ]">
            {{ highlight.node.group === 'core' ? '核心技术栈' : highlight.node.group === 'weak' ? '核心弱项' : '分支知识点' }}
          </span>
          <h4 class="text-base font-bold text-slate-100 flex items-center gap-2">
            <AlertTriangle v-if="highlight.node.group === 'weak'" class="w-5 h-5 text-red-400 flex-shrink-0" />
            <CheckCircle v-else class="w-5 h-5 text-emerald-400 flex-shrink-0" />
            {{ highlight.node.label }}
          </h4>
        </div>

        <div class="space-y-3">
          <h5 class="text-xs font-semibold text-slate-400">关联路径传导：</h5>
          <p v-if="highlight.connections.length === 0" class="text-xs text-slate-500">该独立模块尚未有复杂的分级传导记录</p>
          <div v-else class="space-y-2.5">
            <div 
              v-for="(conn, idx) in highlight.connections" 
              :key="idx" 
              class="flex items-start gap-2 bg-slate-950 p-2.5 rounded border border-slate-800"
            >
              <ArrowRight class="w-3.5 h-3.5 text-indigo-400 mt-0.5 flex-shrink-0" />
              <div>
                <div class="flex items-center gap-1.5">
                  <span class="text-xs font-medium text-slate-200">{{ conn.node?.label }}</span>
                  <span class="text-[9px] text-slate-500">({{ conn.relationship }})</span>
                </div>
                <p class="text-[10px] text-slate-400 mt-1">
                  {{ conn.node?.group === 'weak' 
                    ? '此节点在您的评估中表现较弱，会由于逻辑缺陷导致整体链式扣分。'
                    : '此节点属于您掌握较好的支撑底座，能够作为论证论据。' }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="highlight" class="border-t border-slate-800 pt-3 mt-4">
        <p class="text-[10px] text-slate-500 leading-relaxed bg-slate-950 p-2.5 rounded">
          <b>突破指引：</b> 
          {{ highlight.node.group === 'weak' 
            ? '建议在后续学习中，针对此节点的分布式失效、网络高负载瓶颈做专题查漏补缺，这是通往高级架构的必由之路。'
            : '技术底子良好，在后续解答中可将其作为底层支撑，由浅入深引导面试官切入此熟悉话题。' }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { BookOpen, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-vue-next';

interface GraphNode {
  id: string;
  label: string;
  group: 'core' | 'sub' | 'weak';
}

interface GraphLink {
  source: string;
  target: string;
  label?: string;
}

interface KnowledgeGraphProps {
  data: {
    nodes: GraphNode[];
    links: GraphLink[];
  };
}

const props = defineProps<KnowledgeGraphProps>();

const selectedNodeId = ref<string | null>(null);

const handleNodeClick = (nodeId: string) => {
  selectedNodeId.value = selectedNodeId.value === nodeId ? null : nodeId;
};

const highlight = computed(() => {
  if (!selectedNodeId.value) return null;
  const node = props.data.nodes.find(n => n.id === selectedNodeId.value);
  if (!node) return null;

  const connections = props.data.links
    .filter(l => l.source === selectedNodeId.value || l.target === selectedNodeId.value)
    .map(l => {
      const otherId = l.source === selectedNodeId.value ? l.target : l.source;
      const otherNode = props.data.nodes.find(n => n.id === otherId);
      return {
        node: otherNode,
        relationship: l.label,
        direction: l.source === selectedNodeId.value ? 'out' : 'in'
      };
    });

  return {
    node,
    connections
  };
});

// 动态布局：根据节点分组和索引计算坐标，适配后端任意生成的节点
const getCoordinates = (id: string): { x: number; y: number } => {
  const nodes = props.data.nodes;
  const centerX = 160;
  const centerY = 120;

  // core 节点放中心
  const node = nodes.find(n => n.id === id);
  if (!node) return { x: centerX, y: centerY };
  if (node.group === 'core' || id === 'core') return { x: centerX, y: centerY };

  // 按 group 分组，保持顺序稳定
  const subNodes = nodes.filter(n => n.group === 'sub' || (n.group === 'core' && n.id !== 'core'));
  const weakNodes = nodes.filter(n => n.group === 'weak');

  // sub 节点在内圈，weak 节点在外圈
  const isWeak = node.group === 'weak';
  const groupNodes = isWeak ? weakNodes : subNodes;
  const indexInGroup = groupNodes.findIndex(n => n.id === id);
  const count = groupNodes.length || 1;
  const radius = isWeak ? 100 : 60;

  // 均匀分布在圆环上，从顶部开始
  const angle = (2 * Math.PI * indexInGroup) / count - Math.PI / 2;
  return {
    x: centerX + radius * Math.cos(angle),
    y: centerY + radius * Math.sin(angle),
  };
};

const getNodeBgClass = (node: GraphNode) => {
  const isSelected = selectedNodeId.value === node.id;
  const isConnected = selectedNodeId.value && props.data.links.some(
    l => (l.source === selectedNodeId.value && l.target === node.id) || (l.target === selectedNodeId.value && l.source === node.id)
  );

  if (node.group === 'core') {
    return isSelected 
      ? 'bg-indigo-600 border-indigo-500 text-white' 
      : 'bg-indigo-950 border-indigo-500 text-indigo-300 hover:bg-indigo-900';
  } else if (node.group === 'weak') {
    return isSelected 
      ? 'bg-red-600 border-red-500 text-white' 
      : 'bg-red-950 border-red-500 text-red-300 hover:bg-red-900';
  } else if (isConnected) {
    return 'bg-slate-700 border-indigo-400 text-white';
  }
  return 'bg-slate-800 border-slate-700 hover:bg-slate-700 text-slate-300';
};
</script>
