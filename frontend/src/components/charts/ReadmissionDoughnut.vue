<template>
  <div class="relative flex items-center justify-center" style="height: 220px;">
    <Doughnut :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps({
  data: {
    type: Object,
    required: true
    // { labels: string[], values: number[] }
  }
})

const chartData = computed(() => ({
  labels: props.data.labels,
  datasets: [
    {
      data: props.data.values,
      backgroundColor: ['rgba(220,38,38,0.8)', 'rgba(61,80,106,0.8)'],
      borderColor: ['#dc2626', '#3d506a'],
      borderWidth: 1,
      hoverOffset: 6
    }
  ]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '65%',
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: '#94a3b8',
        font: { family: 'DM Sans', size: 11 },
        padding: 16,
        usePointStyle: true
      }
    },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const total = ctx.dataset.data.reduce((a, b) => a + b, 0)
          const pct = ((ctx.parsed / total) * 100).toFixed(1)
          return ` ${ctx.label}: ${ctx.parsed.toLocaleString()} (${pct}%)`
        }
      },
      backgroundColor: '#1e293b',
      borderColor: '#3d506a',
      borderWidth: 1
    }
  }
}
</script>
