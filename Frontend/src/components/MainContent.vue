<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'

defineProps<{
  sidebarVisible: boolean
}>()

const emit = defineEmits<{
  toggleSidebar: []
}>()

interface Message {
  id: number
  role: 'system' | 'user'
  content: string
  time: string
}

const messages = ref<Message[]>([
  {
    id: 1,
    role: 'system',
    content: '欢迎使用 LeafAI 智能工作台！我是你的 AI 助手，可以帮助你完成文档生成、数据分析、代码编写等任务。请随时告诉我你需要什么。',
    time: '刚刚',
  },
  {
    id: 2,
    role: 'user',
    content: '帮我生成一份产品需求文档',
    time: '刚刚',
  },
  {
    id: 3,
    role: 'system',
    content: '好的，我来为你生成一份产品需求文档（PRD）。请稍等，正在整理文档结构和内容要点...',
    time: '刚刚',
  },
])

const contentBodyRef = ref<HTMLElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    if (contentBodyRef.value) {
      contentBodyRef.value.scrollTop = contentBodyRef.value.scrollHeight
    }
  })
}

watch(messages, () => scrollToBottom(), { deep: true })
</script>

<template>
  <main class="main-content">
    <header class="content-header">
      <div class="header-left">
        <button class="icon-btn" title="文档功能">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
        </button>
        <button class="icon-btn" title="切换侧边栏" @click="emit('toggleSidebar')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <line x1="9" y1="3" x2="9" y2="21" />
          </svg>
        </button>
      </div>

      <div class="header-center">
        <h1 class="doc-title">AI 工作台</h1>
        <p class="doc-notice">AI 生成可能有误，注意核实</p>
      </div>

      <div class="header-right">
        <button class="icon-btn" title="更多">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="5" cy="12" r="2" />
            <circle cx="12" cy="12" r="2" />
            <circle cx="19" cy="12" r="2" />
          </svg>
        </button>
      </div>
    </header>

    <div ref="contentBodyRef" class="content-body">
      <div class="chat-messages">
        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="['message-row', msg.role]"
        >
          <div :class="['message-bubble', msg.role]">
            <div class="bubble-text">{{ msg.content }}</div>
            <div class="bubble-time">{{ msg.time }}</div>
          </div>
        </div>
      </div>
    </div>

    <button class="scroll-btn" title="滚动到底部" @click="scrollToBottom">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="6 9 12 15 18 9" />
      </svg>
    </button>
  </main>
</template>

<style scoped>
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-bg-white);
  position: relative;
  overflow: hidden;
}

.content-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.header-left,
.header-right {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.icon-btn {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: var(--color-text-secondary);
  transition: background 0.15s, color 0.15s;
}
.icon-btn:hover {
  background: var(--color-hover);
  color: var(--color-text-primary);
}

.header-center {
  text-align: center;
  flex: 1;
}

.doc-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 4px;
}

.doc-notice {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.content-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  padding-bottom: calc(var(--input-bar-height) + 32px);
}

.chat-messages {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-row {
  display: flex;
}

.message-row.system {
  justify-content: flex-start;
}

.message-row.user {
  justify-content: flex-end;
}

.message-bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 14px;
  position: relative;
}

.message-bubble.system {
  background: #f3f4f6;
  border-top-left-radius: 4px;
}

.message-bubble.user {
  background: var(--color-accent);
  color: #fff;
  border-top-right-radius: 4px;
}

.bubble-text {
  font-size: 14px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.bubble-time {
  font-size: 11px;
  margin-top: 6px;
  opacity: 0.5;
  text-align: right;
}

.scroll-btn {
  position: absolute;
  right: 24px;
  bottom: calc(var(--input-bar-height) + 40px);
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  color: var(--color-text-secondary);
  transition: box-shadow 0.15s, color 0.15s;
}
.scroll-btn:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  color: var(--color-text-primary);
}
</style>