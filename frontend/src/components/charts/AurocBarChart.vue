<template>
  <div class="relative" style="height: 220px;">
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
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const props = defineProps({
  data: {
    type: Object,
    required: true
    // { labels: string[], values: number[] }
  },
  horizontal: {
    type: Boolean,
    default: false
  }
})

const chartData = computed(() => ({
  labels: props.data.labels,
  datasets: [
    {
      label: 'AUROC',
      data: props.data.values,
      backgroundColor: props.data.values.map((_, i) =>
        i === 0 ? 'rgba(220, 38, 38, 0.8)' : 'rgba(61, 80, 106, 0.8)'
      ),
      borderColor: props.data.values.map((_, i) =>
        i === 0 ? '#dc2626' : '#3d506a'
      ),
      borderWidth: 1,
      borderRadius: 4
    }
  ]
}))

const chartOptions = computed(() => ({
  indexAxis: props.horizontal ? 'y' : 'x',
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx) => ` AUROC: ${ctx.parsed[props.horizontal ? 'x' : 'y'].toFixed(4)}`
      },
      backgroundColor: '#1e293b',
      borderColor: '#3d506a',
      borderWidth: 1
    }
  },
  scales: {
    x: {
      grid: { color: 'rgba(61,80,106,0.3)' },
      ticks: { color: '#94a3b8', font: { family: 'DM Sans', size: 11 } },
      min: props.horizontal ? 0.60 : undefined,
      max: props.horizontal ? 0.70 : undefined
    },
    y: {
      grid: { color: 'rgba(61,80,106,0.3)' },
      ticks: { color: '#94a3b8', font: { family: 'DM Sans', size: 11 } },
      min: props.horizontal ? undefined : 0.60,
      max: props.horizontal ? undefined : 0.70
    }
  }
}))
</script>
