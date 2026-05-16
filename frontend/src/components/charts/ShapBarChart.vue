<template>
  <div class="relative" style="height: 260px;">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const props = defineProps({
  /**
   * shap: Array of { feature: string, value: number }
   * Sorted by |value| descending, top 10
   */
  shap: {
    type: Array,
    required: true
  }
})

// Sort by absolute value, take top 10
const top10 = computed(() =>
  [...props.shap]
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 10)
)

const chartData = computed(() => ({
  labels: top10.value.map(s => s.feature.replace(/_/g, ' ').slice(0, 24)),
  datasets: [
    {
      label: 'SHAP Value',
      data: top10.value.map(s => s.value),
      backgroundColor: top10.value.map(s =>
        s.value >= 0 ? 'rgba(220,38,38,0.75)' : 'rgba(16,185,129,0.75)'
      ),
      borderColor: top10.value.map(s =>
        s.value >= 0 ? '#dc2626' : '#10b981'
      ),
      borderWidth: 1,
      borderRadius: 3
    }
  ]
}))

const chartOptions = {
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx) => ` SHAP: ${ctx.parsed.x.toFixed(4)}`
      },
      backgroundColor: '#1e293b',
      borderColor: '#3d506a',
      borderWidth: 1
    }
  },
  scales: {
    x: {
      grid: { color: 'rgba(61,80,106,0.3)' },
      ticks: { color: '#94a3b8', font: { family: 'DM Sans', size: 10 } }
    },
    y: {
      grid: { display: false },
      ticks: { color: '#cbd5e1', font: { family: 'DM Sans', size: 10 } }
    }
  }
}
</script>
