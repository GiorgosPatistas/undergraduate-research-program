<template>
  <div class="flex flex-col items-center gap-4 w-full">
    <!-- Gauge Arc (SVG) -->
    <div class="relative w-48 h-28">
      <svg viewBox="0 0 200 110" class="w-full h-full">
        <!-- Background arc -->
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="#1e293b"
          stroke-width="16"
          stroke-linecap="round"
        />
        <!-- Green zone (0 → threshold) -->
        <path
          d="M 20 100 A 80 80 0 0 1 100 20"
          fill="none"
          stroke="rgba(16,185,129,0.35)"
          stroke-width="16"
          stroke-linecap="round"
        />
        <!-- Red zone (threshold → max) -->
        <path
          d="M 100 20 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="rgba(220,38,38,0.35)"
          stroke-width="16"
          stroke-linecap="round"
        />
        <!-- Needle -->
        <line
          :x1="100"
          :y1="100"
          :x2="needleX"
          :y2="needleY"
          :stroke="needleColor"
          stroke-width="3"
          stroke-linecap="round"
        />
        <!-- Center dot -->
        <circle cx="100" cy="100" r="5" :fill="needleColor" />
      </svg>

      <!-- Percentage label in center -->
      <div class="absolute inset-0 flex items-end justify-center pb-1">
        <span class="text-2xl font-display font-bold" :class="isHighRisk ? 'text-crimson-400' : 'text-emerald-400'">
          {{ (probability * 100).toFixed(1) }}%
        </span>
      </div>
    </div>

    <!-- Scale labels -->
    <div class="flex justify-between w-40 text-xs text-slate-500">
      <span>0%</span>
      <span class="text-slate-400">50%</span>
      <span>100%</span>
    </div>

    <!-- Risk label -->
    <div
      class="px-4 py-1.5 rounded-full text-sm font-medium"
      :class="isHighRisk ? 'bg-crimson-500/20 text-crimson-300' : 'bg-emerald-500/20 text-emerald-300'"
    >
      {{ isHighRisk ? 'High Risk' : 'Low Risk' }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  probability: { type: Number, required: true } // 0.0 – 1.0
})

const isHighRisk = computed(() => props.probability >= 0.5)

// Map 0–1 probability to angle -180deg → 0deg (left → right semicircle)
const needleAngleDeg = computed(() => -180 + props.probability * 180)

// Convert angle to SVG coordinates (center: 100,100, radius: 75)
const RAD = Math.PI / 180
const needleX = computed(() => 100 + 72 * Math.cos(needleAngleDeg.value * RAD))
const needleY = computed(() => 100 + 72 * Math.sin(needleAngleDeg.value * RAD))
const needleColor = computed(() => isHighRisk.value ? '#dc2626' : '#10b981')
</script>
