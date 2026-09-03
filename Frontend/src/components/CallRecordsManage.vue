<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApiRecords, type CallRecordItem } from '../api/index'

const items = ref<CallRecordItem[]>([])
const total = ref(0)
const page = ref(1)
const PAGE_SIZE = 20
const loading = ref(false)
const errorMsg = ref('')

// 筛选条件
const filter = ref({
  service_code: '',
  username: '',
  start: '',
  end: '',
})

const SERVICE_OPTIONS = [
  { value: '', label: '全部类型' },
  { value: 'chat', label: '对话' },
  { value: 'image_generate', label: '图片生成' },
  { value: 'video_generate', label: '视频生成' },
  { value: 'audio', label: '语音生成' },
]

function fmtTime(iso: string) {
  if (!iso) return '—'
  const d = new Date(iso)
  return isNaN(d.getTime()) ? iso : d.toLocaleString()
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '排队中',
    running: '生成中',
    success: '成功',
    failed: '失败',
  }
  return map[status] || status
}

function statusClass(status: string) {
  if (status === 'success') return 'ok'
  if (status === 'failed') return 'bad'
  if (status === 'running') return 'run'
  return 'pend'
}

function serviceLabel(code: string) {
  const opt = SERVICE_OPTIONS.find((o) => o.value === code)
  return opt ? opt.label : code
}

async function load(pageNo: number) {
  loading.value = true
  errorMsg.value = ''
  page.value = pageNo
  try {
    const res = await adminApiRecords.list({
      service_code: filter.value.service_code || undefined,
      username: filter.value.username.trim() || undefined,
      start: filter.value.start || undefined,
      end: filter.value.end || undefined,
      page: pageNo,
      page_size: PAGE_SIZE,
    })
    items.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e: any) {
    errorMsg.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function apply() {
  load(1)
}

onMounted(() => load(1))
</script>

<template>
  <div class="records-manage">
    <div class="rm-header">
      <h2 class="rm-title">用户调用记录</h2>
      <span class="rm-sub">展示所有用户的调用任务（对话/图片/视频/语音），无论是否消耗积分</span>
    </div>

    <div class="rm-filter">
      <label>类型
        <select v-model="filter.service_code" class="rm-input" @change="apply">
          <option v-for="o in SERVICE_OPTIONS" :key="o.value" :value="o.value">{{ o.label }}</option>
        </select>
      </label>
      <label>用户名
        <input v-model="filter.username" class="rm-input" placeholder="模糊搜索用户名" @keyup.enter="apply" />
      </label>
      <label>开始日期
        <input v-model="filter.start" type="date" class="rm-input" />
      </label>
      <label>结束日期
        <input v-model="filter.end" type="date" class="rm-input" />
      </label>
      <button class="btn primary" @click="apply">查询</button>
    </div>

    <div v-if="errorMsg" class="rm-error">{{ errorMsg }}</div>

    <table class="rm-table">
      <thead>
        <tr>
          <th>类型</th>
          <th>用户</th>
          <th>模型</th>
          <th>内容/标题</th>
          <th>状态</th>
          <th>条数</th>
          <th>时间</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in items" :key="r.kind + ':' + r.ref_id">
          <td><span class="rm-tag">{{ serviceLabel(r.service_code) }}</span></td>
          <td>{{ r.username }} <span class="rm-uid">#{{ r.user_id }}</span></td>
          <td class="rm-model">{{ r.model_name || '—' }}</td>
          <td class="rm-title-cell">{{ r.title || '—' }}</td>
          <td><span class="rm-status" :class="statusClass(r.status)">{{ statusLabel(r.status) }}</span></td>
          <td>{{ r.kind === 'chat' ? (r.message_count ?? '—') : '—' }}</td>
          <td class="rm-time">{{ fmtTime(r.create_time) }}</td>
        </tr>
        <tr v-if="items.length === 0">
          <td colspan="7" class="rm-empty">{{ loading ? '加载中...' : '暂无调用记录' }}</td>
        </tr>
      </tbody>
    </table>

    <div class="rm-pager">
      <button class="btn" :disabled="page <= 1" @click="load(page - 1)">上一页</button>
      <span>第 {{ page }} 页 / 共 {{ Math.max(1, Math.ceil(total / PAGE_SIZE)) }} 页（{{ total }} 条）</span>
      <button class="btn" :disabled="page >= Math.ceil(total / PAGE_SIZE)" @click="load(page + 1)">下一页</button>
    </div>
  </div>
</template>

<style scoped>
.records-manage {
  font-family: var(--font-sans);
}
.rm-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
}
.rm-title {
  font-size: 20px;
  font-weight: 600;
}
.rm-sub {
  font-size: 13px;
  color: var(--color-text-secondary);
}
.rm-filter {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px;
  padding: 14px 16px;
  background: var(--color-bg-card, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 10px;
  margin-bottom: 16px;
}
.rm-filter label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.rm-input {
  padding: 8px 10px;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  font-size: 13px;
  min-width: 130px;
}
.rm-error {
  color: #dc2626;
  padding: 8px 0;
}
.rm-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--color-bg-card, #fff);
  border-radius: 10px;
  overflow: hidden;
  font-size: 13px;
}
.rm-table th,
.rm-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border, #f0f0f0);
  text-align: left;
  vertical-align: top;
}
.rm-table th {
  background: var(--color-bg-hover, #f8f9fa);
  font-weight: 600;
}
.rm-table td.rm-title-cell {
  max-width: 320px;
  word-break: break-all;
}
.rm-uid {
  color: var(--color-text-secondary);
  font-size: 12px;
}
.rm-model {
  color: var(--color-text-secondary);
}
.rm-time {
  color: var(--color-text-secondary);
  white-space: nowrap;
}
.rm-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
  font-size: 12px;
}
.rm-status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
}
.rm-status.ok { background: rgba(5, 150, 105, 0.12); color: #059669; }
.rm-status.bad { background: rgba(220, 38, 38, 0.12); color: #dc2626; }
.rm-status.run { background: rgba(217, 119, 6, 0.12); color: #d97706; }
.rm-status.pend { background: rgba(107, 114, 128, 0.12); color: #6b7280; }
.rm-empty {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 24px 0;
}
.rm-pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding-top: 16px;
  font-size: 13px;
}
</style>