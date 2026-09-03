<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { adminApiAudit, type AuditLogItem } from '../api'

const items = ref<AuditLogItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const errorMsg = ref('')

const moduleFilter = ref('')
const operatorFilter = ref('')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const moduleOptions = ['users', 'models', 'features', 'points', 'notifications', 'auth', 'cases']

async function load(reset = false) {
  if (reset) page.value = 1
  loading.value = true
  errorMsg.value = ''
  try {
    const r = await adminApiAudit.list({
      page: page.value,
      page_size: pageSize.value,
      module: moduleFilter.value || undefined,
      operator: operatorFilter.value || undefined,
    })
    items.value = r.data?.items || []
    total.value = r.data?.total || 0
  } catch (e: any) {
    errorMsg.value = e?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function search() {
  load(true)
}

function go(p: number) {
  page.value = p
  load()
}

function fmtTime(iso: string) {
  if (!iso) return ''
  const d = new Date(iso)
  return isNaN(d.getTime()) ? iso : d.toLocaleString('zh-CN')
}

onMounted(() => load())
</script>

<template>
  <div class="audit">
    <h2 class="audit-title">操作审计</h2>

    <div class="audit-toolbar">
      <select v-model="moduleFilter" class="sel">
        <option value="">全部模块</option>
        <option v-for="m in moduleOptions" :key="m" :value="m">{{ m }}</option>
      </select>
      <input v-model="operatorFilter" class="inp" placeholder="操作者用户名" @keyup.enter="search" />
      <button class="btn" @click="search">查询</button>
    </div>

    <div v-if="errorMsg" class="audit-error">{{ errorMsg }}</div>

    <table class="tbl">
      <thead>
        <tr>
          <th>操作者</th>
          <th>模块</th>
          <th>动作</th>
          <th>目标</th>
          <th>详情</th>
          <th>IP</th>
          <th>时间</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="it in items" :key="it.id">
          <td>{{ it.operator }}</td>
          <td><span class="tag">{{ it.module }}</span></td>
          <td>{{ it.action }}</td>
          <td>{{ it.target_id || '-' }}</td>
          <td class="detail-cell">{{ JSON.stringify(it.detail) }}</td>
          <td>{{ it.ip || '-' }}</td>
          <td>{{ fmtTime(it.create_time) }}</td>
        </tr>
        <tr v-if="!loading && items.length === 0">
          <td colspan="7" class="empty">暂无审计记录</td>
        </tr>
      </tbody>
    </table>

    <div class="pager">
      <button class="btn" :disabled="page <= 1" @click="go(page - 1)">上一页</button>
      <span>第 {{ page }} / {{ totalPages }} 页 · 共 {{ total }} 条</span>
      <button class="btn" :disabled="page >= totalPages" @click="go(page + 1)">下一页</button>
    </div>
  </div>
</template>

<style scoped>
.audit-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 16px;
}
.audit-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.sel,
.inp {
  padding: 7px 10px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-white);
  font-size: 13px;
}
.inp {
  min-width: 160px;
}
.btn {
  padding: 7px 14px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-white);
  cursor: pointer;
}
.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.audit-error {
  background: #fef2f2;
  color: #b91c1c;
  padding: 10px 12px;
  border-radius: 8px;
  margin-bottom: 12px;
  font-size: 13px;
}
.tbl {
  width: 100%;
  border-collapse: collapse;
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  font-size: 13px;
  overflow: hidden;
}
.tbl th,
.tbl td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
}
.tbl th {
  color: var(--color-text-secondary);
  font-weight: 600;
}
.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(64, 128, 255, 0.1);
  color: var(--color-accent);
  font-size: 12px;
}
.detail-cell {
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-text-secondary);
}
.empty {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 40px 0;
}
.pager {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
</style>