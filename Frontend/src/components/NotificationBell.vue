<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { BASE_URL, API_PREFIX, notifyMine, type NotificationItem } from '../api/index'

const open = ref(false)
const unread = ref(0)
const items = ref<NotificationItem[]>([])
const loading = ref(false)
let es: EventSource | null = null

function getToken(): string | null {
  return localStorage.getItem('leafai_token')
}

function toggle() {
  open.value = !open.value
  if (open.value) loadHistory()
}

function loadHistory() {
  loading.value = true
  notifyMine.unreadCount().then((r) => (unread.value = r.data?.count || 0)).catch(() => {})
  notifyMine.history({ page: 1, page_size: 20 })
    .then((r) => (items.value = r.data?.items || []))
    .finally(() => (loading.value = false))
}

async function markRead(n: NotificationItem) {
  if (n.is_read) return
  try {
    await notifyMine.markRead(n.token)
    n.is_read = true
    if (unread.value > 0) unread.value -= 1
  } catch { /* ignore */ }
}

async function markAll() {
  try {
    await notifyMine.markAllRead()
    items.value.forEach((n) => (n.is_read = true))
    unread.value = 0
  } catch { /* ignore */ }
}

function fmtTime(iso: string) {
  const d = new Date(iso)
  return isNaN(d.getTime()) ? '' : d.toLocaleString('zh-CN', { dateStyle: 'short', timeStyle: 'short' })
}

function onSSEEvent(evt: MessageEvent) {
  try {
    const data = JSON.parse(evt.data)
    // 移除重放/已存在的，并插到最前
    items.value = items.value.filter((i) => i.token !== data.token)
    items.value.unshift(data as NotificationItem)
    if (!data.is_read) unread.value += 1
    if (items.value.length > 50) items.value.length = 50
  } catch { /* ignore */ }
}

function connectSSE() {
  const token = getToken()
  if (!token) return
  try {
    es = new EventSource(`${BASE_URL}${API_PREFIX}/notify/stream?token=${encodeURIComponent(token)}`)
    es.addEventListener('points', onSSEEvent)
    es.addEventListener('task', onSSEEvent)
    es.addEventListener('system', onSSEEvent)
    es.addEventListener('message', (evt) => {
      // 捕获默认事件名（如数据推成 message）
      const isKeepAlive = evt.data === undefined || evt.data === null || evt.data === ''
      if (!isKeepAlive) onSSEEvent(evt)
    })
    es.onerror = () => {
      // EventSource 断线自动重连
    }
  } catch { /* ignore */ }
}

function closeSSE() {
  if (es) {
    es.close()
    es = null
  }
}

onMounted(() => {
  if (getToken()) {
    loadHistory()
    connectSSE()
  }
  window.addEventListener('click', onDocClick)
})

onUnmounted(() => {
  closeSSE()
  window.removeEventListener('click', onDocClick)
})

function onDocClick(e: MouseEvent) {
  const el = (e.target as HTMLElement)?.closest?.('.noti-bell-wrap')
  if (!el) open.value = false
}
</script>

<template>
  <div class="noti-bell-wrap">
    <button class="icon-btn noti-bell" title="通知" @click.stop="toggle">
      <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
      </svg>
      <span v-if="unread > 0" class="noti-badge">{{ unread > 99 ? '99+' : unread }}</span>
    </button>

    <Transition name="noti-fade">
      <div v-if="open" class="noti-panel" @click.stop>
        <div class="noti-panel-head">
          <span>通知</span>
          <button class="noti-mark-all" @click="markAll">全部已读</button>
        </div>
        <div class="noti-list">
          <div
            v-for="n in items"
            :key="n.token"
            :class="['noti-item', { unread: !n.is_read }]"
            @click="markRead(n)"
          >
            <div class="noti-item-title">
              <span v-if="!n.is_read" class="noti-dot" />
              {{ n.title }}
            </div>
            <div class="noti-item-content">{{ n.content }}</div>
            <div class="noti-item-time">{{ fmtTime(n.create_time) }}</div>
          </div>
          <div v-if="!loading && items.length === 0" class="noti-empty">暂无通知</div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.noti-bell-wrap {
  position: relative;
  display: inline-flex;
}
.icon-btn {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: var(--color-text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.icon-btn:hover {
  background: rgba(37, 99, 235, 0.12);
  color: var(--color-accent);
}
.noti-bell {
  position: relative;
}
.noti-badge {
  position: absolute;
  top: 3px;
  right: 3px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  background: #e02424;
  color: #fff;
  font-size: 10px;
  line-height: 16px;
  text-align: center;
}
.noti-panel {
  position: absolute;
  top: 40px;
  right: 0;
  width: 340px;
  max-height: 460px;
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
  z-index: 2000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.noti-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  font-size: 14px;
  font-weight: 600;
}
.noti-mark-all {
  font-size: 12px;
  color: var(--color-accent);
  background: none;
  border: none;
  cursor: pointer;
}
.noti-list {
  overflow-y: auto;
  max-height: 400px;
}
.noti-item {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
}
.noti-item:hover {
  background: var(--color-hover);
}
.noti-item.unread {
  background: rgba(64, 128, 255, 0.06);
}
.noti-item-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}
.noti-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-accent);
}
.noti-item-content {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 4px;
  line-height: 1.5;
  word-break: break-word;
}
.noti-item-time {
  font-size: 11px;
  color: var(--color-text-tertiary);
  margin-top: 4px;
}
.noti-empty {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 40px 0;
  font-size: 13px;
}
.noti-fade-enter-active,
.noti-fade-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}
.noti-fade-enter-from,
.noti-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>