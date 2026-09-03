<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApiNotify, type AdminNotificationItem } from '../api/index'

const items = ref<AdminNotificationItem[]>([])
const total = ref(0)
const page = ref(1)
const PAGE_SIZE = 20
const errorMsg = ref('')
const sending = ref(false)
const form = ref({ type: 'system', title: '', content: '', user_ids: '' })

const TYPES = ['system', 'points', 'task']

function load(pageNo: number) {
  page.value = pageNo
  adminApiNotify.list({ page: pageNo, page_size: PAGE_SIZE }).then((res) => {
    items.value = res.data?.items || []
    total.value = res.data?.total || 0
  }).catch((e: any) => (errorMsg.value = e.message || '加载失败'))
}

async function send() {
  if (!form.value.title.trim()) {
    errorMsg.value = '请填写通知标题'
    return
  }
  sending.value = true
  errorMsg.value = ''
  let user_ids: number[] | null = null
  const idsText = form.value.user_ids.trim()
  if (idsText) {
    user_ids = idsText.split(',').map((s) => Number(s.trim())).filter(Number.isFinite)
  }
  try {
    await adminApiNotify.broadcast({ type: form.value.type, title: form.value.title, content: form.value.content, user_ids })
    form.value = { type: 'system', title: '', content: '', user_ids: '' }
    load(1)
  } catch (e: any) {
    errorMsg.value = e.message || '发送失败'
  } finally {
    sending.value = false
  }
}

function fmtTime(iso: string) {
  const d = new Date(iso)
  return isNaN(d.getTime()) ? iso : d.toLocaleString()
}

onMounted(() => load(1))
</script>

<template>
  <div class="notify-manage">
    <div class="nm-header">
      <h2 class="nm-title">通知管理</h2>
    </div>

    <div class="nm-broadcast">
      <h3 class="nm-subtitle">群发通知</h3>
      <div class="nm-form">
        <div class="nm-row">
          <label>类型
            <select v-model="form.type" class="nm-input">
              <option v-for="t in TYPES" :key="t" :value="t">{{ t }}</option>
            </select>
          </label>
          <label>标题
            <input v-model="form.title" class="nm-input" placeholder="通知标题" />
          </label>
        </div>
        <div class="nm-row">
          <label>内容
            <textarea v-model="form.content" class="nm-input nm-textarea" placeholder="通知正文（选填）" />
          </label>
        </div>
        <div class="nm-row">
          <label>指定用户ID（逗号分隔，留空=发送给全部用户）
            <input v-model="form.user_ids" class="nm-input" placeholder="例如：1, 2, 55（留空则全量）" />
          </label>
        </div>
        <div v-if="errorMsg" class="nm-error">{{ errorMsg }}</div>
        <div class="nm-submit">
          <button class="btn primary" :disabled="sending" @click="send">{{ sending ? '发送中...' : '发送' }}</button>
        </div>
      </div>
    </div>

    <div class="nm-sent">
      <h3 class="nm-subtitle">已发送</h3>
      <table class="nm-table">
        <thead>
          <tr>
            <th>ID</th><th>类型</th><th>标题</th><th>接收者</th><th>内容</th><th>已读</th><th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="n in items" :key="n.id">
            <td>{{ n.id }}</td>
            <td>{{ n.type }}</td>
            <td>{{ n.title }}</td>
            <td>{{ n.user_id }}</td>
            <td class="nm-content">{{ n.content }}</td>
            <td>{{ n.is_read ? '是' : '否' }}</td>
            <td>{{ fmtTime(n.create_time) }}</td>
          </tr>
          <tr v-if="items.length === 0">
            <td colspan="7" class="nm-empty">暂无发送记录</td>
          </tr>
        </tbody>
      </table>
      <div class="nm-pager">
        <button class="btn" :disabled="page <= 1" @click="load(page - 1)">上一页</button>
        <span>第 {{ page }} 页 / 共 {{ Math.ceil(total / PAGE_SIZE) || 1 }} 页</span>
        <button class="btn" :disabled="page * PAGE_SIZE >= total" @click="load(page + 1)">下一页</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notify-manage { max-width: 1200px; }
.nm-header { margin-bottom: 16px; }
.nm-title { font-size: 22px; font-weight: 600; }
.nm-broadcast {
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
}
.nm-subtitle { font-size: 14px; font-weight: 600; margin-bottom: 12px; }
.nm-form { display: flex; flex-direction: column; gap: 12px; }
.nm-row { display: flex; gap: 16px; flex-wrap: wrap; }
.nm-row label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
  flex: 1;
  min-width: 200px;
}
.nm-input {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 8px 12px;
  background: var(--color-bg-white);
  color: var(--color-text-primary);
  font-size: 13px;
}
.nm-textarea { min-height: 70px; resize: vertical; }
.nm-error { color: #dc2626; font-size: 13px; }
.nm-submit { display: flex; justify-content: flex-end; }
.btn {
  padding: 8px 16px;
  border-radius: 8px;
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  cursor: pointer;
  font-size: 13px;
}
.btn.primary { background: var(--color-accent); color: #fff; border-color: transparent; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.nm-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.nm-table th, .nm-table td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--color-border); }
.nm-table th { color: var(--color-text-secondary); font-weight: 500; }
.nm-content { color: var(--color-text-secondary); }
.nm-empty { text-align: center; color: var(--color-text-secondary); padding: 24px 0; }
.nm-pager { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 16px; }
</style>