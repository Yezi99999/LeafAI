<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { api, type PointsRecord } from '../api'

const props = defineProps<{
  title: string
  direction: 'out' | 'in'
  emptyText?: string
}>()

const rows = ref<PointsRecord[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const error = ref('')
const PAGE_SIZE = 20

const TX_LABEL: Record<string, string> = {
  recharge: '充值',
  consume: '消费',
  refund: '返还',
  admin_adjust: '人工调整',
}
const SERVICE_LABEL: Record<string, string> = {
  image_generate: '图片生成',
  chat: '对话',
  video_generate: '视频生成',
  audio: '语音',
}

async function load(p: number) {
  loading.value = true
  error.value = ''
  page.value = p
  try {
    const res = await api.myPointsRecords({ direction: props.direction, page: p, page_size: PAGE_SIZE })
    rows.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e: any) {
    error.value = e.message || '加载失败'
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

watch(() => props.direction, () => load(1))
onMounted(() => load(1))

function fmt(d: number) {
  return (d > 0 ? '+' : '') + d
}
</script>

<template>
  <main class="record-view">
    <header class="rv-header">
      <h2 class="rv-title">{{ props.title }}</h2>
      <p class="rv-sub">共 {{ total }} 条记录</p>
    </header>

    <div class="rv-panel">
      <div v-if="loading && rows.length === 0" class="rv-empty">加载中...</div>
      <div v-else-if="error" class="rv-empty rv-error">{{ error }}</div>
      <table v-else-if="rows.length > 0" class="rv-table">
        <thead>
          <tr>
            <th>单号</th>
            <th>类型</th>
            <th>变动(积分)</th>
            <th>余额</th>
            <th>服务</th>
            <th>备注</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.id">
            <td class="mono">#{{ r.id }}</td>
            <td>{{ TX_LABEL[r.tx_type] || r.tx_type }}</td>
            <td :class="r.points_delta < 0 ? 'neg' : 'pos'">{{ fmt(r.points_delta) }}</td>
            <td>{{ r.balance_after }}</td>
            <td>{{ SERVICE_LABEL[r.service_code || ''] || r.service_code || '-' }}</td>
            <td>{{ r.remark || '-' }}</td>
            <td>{{ new Date(r.create_time).toLocaleString() }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="rv-empty">{{ props.emptyText || '暂无记录' }}</div>

      <div v-if="total > 0" class="rv-pager">
        <button class="btn" :disabled="page <= 1" @click="load(page - 1)">上一页</button>
        <span>第 {{ page }} 页 / 共 {{ Math.ceil(total / PAGE_SIZE) || 1 }} 页</span>
        <button class="btn" :disabled="page * PAGE_SIZE >= total" @click="load(page + 1)">下一页</button>
      </div>
    </div>
  </main>
</template>

<style scoped>
.record-view {
  flex: 1;
  overflow-y: auto;
  padding: 56px 40px 40px;
  background: var(--color-bg-page);
}
.rv-header {
  max-width: 820px;
  margin: 0 auto 20px;
}
.rv-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
}
.rv-sub {
  margin-top: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.rv-panel {
  max-width: 820px;
  margin: 0 auto;
  padding: 20px 24px;
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: 14px;
}
.rv-empty {
  text-align: center;
  padding: 40px 0;
  color: var(--color-text-secondary);
}
.rv-error {
  color: #dc2626;
}
.rv-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.rv-table th,
.rv-table td {
  text-align: left;
  padding: 10px 8px;
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}
.rv-table th {
  color: var(--color-text-secondary);
  font-weight: 500;
}
.mono {
  font-family: monospace;
}
.pos {
  color: #15803d;
}
.neg {
  color: #b91c1c;
}
.rv-pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
}
.btn {
  padding: 7px 14px;
  border-radius: 8px;
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  cursor: pointer;
  font-size: 13px;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>