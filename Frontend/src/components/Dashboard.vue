<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'
import { adminApiAnalytics } from '../api'

const overview = ref({ total_users: 0, today_active_users: 0, cumulative_points_consumed: 0, weekly_success_rate: 0 })
const loading = ref(true)
const errorMsg = ref('')
const days = ref(30)

const balanceRef = ref<HTMLElement | null>(null)
const usageRef = ref<HTMLElement | null>(null)
const pointsRef = ref<HTMLElement | null>(null)
const perfRef = ref<HTMLElement | null>(null)
const servicesRef = ref<HTMLElement | null>(null)

let charts: echarts.ECharts[] = []
let toastRef: ReturnType<typeof setTimeout> | null = null

function disposes() {
  charts.forEach((c) => c.dispose())
  charts = []
}

function renderUsers(dates: string[], s: { new_users: number[]; dau: number[] }) {
  if (!balanceRef.value) return
  const ch = echarts.init(balanceRef.value)
  ch.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['新增用户', 'DAU'] },
    grid: { left: 40, right: 16, top: 36, bottom: 24 },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '新增用户', type: 'line', smooth: true, areaStyle: { opacity: 0.15 }, data: s.new_users },
      { name: 'DAU', type: 'line', smooth: true, data: s.dau },
    ],
  })
  charts.push(ch)
}

function renderUsage(s: { chat_messages: number; chat_tokens: number; image_tasks: number; video_tasks: number }) {
  if (!usageRef.value) return
  const ch = echarts.init(usageRef.value)
  ch.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      label: { formatter: '{b}: {c}' },
      data: [
        { name: '聊天消息', value: s.chat_messages },
        { name: '图片任务', value: s.image_tasks },
        { name: '视频任务', value: s.video_tasks },
      ],
    }],
  })
  charts.push(ch)
}

function renderPoints(dates: string[], s: { points_consumed: number[] }) {
  if (!pointsRef.value) return
  const ch = echarts.init(pointsRef.value)
  ch.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 16, top: 30, bottom: 24 },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ name: '积分消耗', type: 'bar', data: s.points_consumed, itemStyle: { color: '#f97316' } }],
  })
  charts.push(ch)
}

function renderPerf(dates: string[], s: { task_success: number[]; task_failed: number[]; avg_latency_ms: number }) {
  if (!perfRef.value) return
  const ch = echarts.init(perfRef.value)
  ch.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['成功任务', '失败任务'] },
    grid: { left: 40, right: 16, top: 36, bottom: 24 },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '成功任务', type: 'line', smooth: true, areaStyle: { opacity: 0.12 }, data: s.task_success },
      { name: '失败任务', type: 'line', smooth: true, data: s.task_failed },
    ],
  })
  charts.push(ch)
}

function renderServices(list: Array<{ provider: string; model: string; success_rate: number; deploy_status: string }>) {
  if (!servicesRef.value) return
  const ch = echarts.init(servicesRef.value)
  ch.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
    series: [{
      type: 'pie',
      radius: '72%',
      label: { formatter: '{b}: {c}%' },
      data: (list || []).slice(0, 10).map((s) => ({ name: `${s.provider}/${s.model}`, value: s.success_rate })),
    }],
  })
  charts.push(ch)
}

function toast(msg: string) {
  errorMsg.value = msg
  if (toastRef) clearTimeout(toastRef)
  toastRef = setTimeout(() => (errorMsg.value = ''), 4000)
}

async function load() {
  loading.value = true
  disposes()
  try {
    const [ov, users, usage, points, perf, services] = await Promise.all([
      adminApiAnalytics.overview(),
      adminApiAnalytics.users(days.value),
      adminApiAnalytics.usage(),
      adminApiAnalytics.points(days.value),
      adminApiAnalytics.performance(),
      adminApiAnalytics.services(),
    ])
    overview.value = ov.data
    renderUsers(users.data.dates, users.data.series)
    renderUsage(usage.data.series)
    renderPoints(points.data.dates, points.data.series)
    renderPerf(perf.data.dates, perf.data.series)
    renderServices(services.data.series.services)
  } catch (e: any) {
    toast(e?.message || '加载报表失败')
  } finally {
    loading.value = false
  }
}

function onResize() {
  charts.forEach((c) => c.resize())
}

watch(days, () => load())

onMounted(() => {
  load()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  disposes()
})
</script>

<template>
  <div class="dash">
    <div class="dash-head">
      <h2 class="dash-title">仪表盘</h2>
      <select v-model.number="days" class="dash-days">
        <option :value="7">近 7 天</option>
        <option :value="30">近 30 天</option>
        <option :value="90">近 90 天</option>
      </select>
    </div>

    <div v-if="errorMsg" class="dash-toast">{{ errorMsg }}</div>

    <div class="kpi">
      <div class="kpi-card">
        <div class="kpi-label">总用户</div>
        <div class="kpi-value">{{ overview.total_users }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">今日活跃</div>
        <div class="kpi-value">{{ overview.today_active_users }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">累计积分消耗</div>
        <div class="kpi-value">{{ overview.cumulative_points_consumed }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">7 日任务成功率</div>
        <div class="kpi-value">{{ overview.weekly_success_rate }}%</div>
      </div>
    </div>

    <div class="grid">
      <div class="panel half">
        <div class="panel-title">活跃用户趋势</div>
        <div ref="balanceRef" class="chart tall" />
      </div>
      <div class="panel half">
        <div class="panel-title">功能用量占比</div>
        <div ref="usageRef" class="chart tall" />
      </div>
      <div class="panel half">
        <div class="panel-title">积分消耗趋势</div>
        <div ref="pointsRef" class="chart tall" />
      </div>
      <div class="panel half">
        <div class="panel-title">系统性能 · 7 日任务</div>
        <div ref="perfRef" class="chart tall" />
      </div>
      <div class="panel full">
        <div class="panel-title">各模型成功率</div>
        <div ref="servicesRef" class="chart flat" />
      </div>
    </div>

    <div v-if="loading" class="dash-mask">加载中…</div>
  </div>
</template>

<style scoped>
.dash {
  position: relative;
}
.dash-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.dash-title {
  font-size: 20px;
  font-weight: 700;
}
.dash-days {
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-white);
}
.dash-toast {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 5000;
  background: #b91c1c;
  color: #fff;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
}
.kpi {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}
.kpi-card {
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 18px;
}
.kpi-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}
.kpi-value {
  font-size: 26px;
  font-weight: 700;
  margin-top: 8px;
  color: var(--color-text-primary);
}
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.panel {
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 14px;
}
.panel.half {
  grid-column: span 1;
}
.panel.full {
  grid-column: span 2;
}
.panel-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
}
.chart.tall {
  height: 280px;
}
.chart.flat {
  height: 320px;
}
.dash-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.55);
  color: var(--color-text-secondary);
  font-size: 14px;
}
@media (max-width: 900px) {
  .kpi {
    grid-template-columns: repeat(2, 1fr);
  }
  .grid {
    grid-template-columns: 1fr;
  }
  .panel.half,
  .panel.full {
    grid-column: span 1;
  }
}
</style>