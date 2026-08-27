<script setup lang="ts">
import { ref } from 'vue'

const prompt = ref('')
const activeMode = ref('chat')

const modes = [
  { id: 'chat', label: '对话', icon: 'chat' },
  { id: 'image', label: '图片生成', icon: 'image' },
  { id: 'video', label: '视频生成', icon: 'video' },
  { id: 'translate', label: '翻译', icon: 'translate' },
  { id: 'more', label: '更多', icon: 'more' },
]

const emit = defineEmits<{
  send: [message: string]
}>()

function handleSend() {
  if (!prompt.value.trim()) return
  emit('send', prompt.value)
  prompt.value = ''
}
</script>

<template>
  <div class="input-bar">
    <div class="input-row">
      <div class="input-wrapper">
        <input
          v-model="prompt"
          type="text"
          class="input-field"
          placeholder="发消息..."
          @keyup.enter="handleSend"
        />
      </div>
      <span class="model-badge">AUTO</span>
      <button class="send-btn" :class="{ active: prompt.trim() }" @click="handleSend">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="19" x2="12" y2="5" />
          <polyline points="5 12 12 5 19 12" />
        </svg>
      </button>
    </div>

    <div class="toolbar">
      <button
        v-for="mode in modes"
        :key="mode.id"
        :class="['toolbar-btn', { active: activeMode === mode.id }]"
        @click="activeMode = mode.id"
      >
        <svg v-if="mode.icon === 'chat'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        <svg v-else-if="mode.icon === 'image'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <polyline points="21 15 16 10 5 21" />
        </svg>
        <svg v-else-if="mode.icon === 'video'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="23 7 16 12 23 17 23 7" />
          <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
        </svg>
        <svg v-else-if="mode.icon === 'translate'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="2" y1="12" x2="22" y2="12" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>
        <svg v-else-if="mode.icon === 'more'" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="5" cy="12" r="2" />
          <circle cx="12" cy="12" r="2" />
          <circle cx="19" cy="12" r="2" />
        </svg>
        <span>{{ mode.label }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.input-bar {
  position: fixed;
  bottom: 0;
  left: var(--sidebar-width);
  right: 0;
  background: var(--color-bg-page);
  padding: 16px 24px 20px;
  z-index: 10;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.input-wrapper {
  flex: 1;
  background: var(--color-bg-white);
  border-radius: 16px;
  padding: 10px 18px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid var(--color-border);
}

.input-field {
  width: 100%;
  padding: 4px 0;
  font-size: 14px;
  color: var(--color-text-primary);
}
.input-field::placeholder {
  color: var(--color-text-secondary);
}

.model-badge {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg-white);
}

.send-btn {
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--color-border);
  color: var(--color-text-secondary);
  transition: background 0.15s, color 0.15s, box-shadow 0.15s;
}
.send-btn.active {
  background: var(--color-accent);
  color: #fff;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
}

.toolbar {
  display: flex;
  gap: 4px;
  margin-top: 10px;
  padding: 0 4px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
  transition: background 0.15s, color 0.15s;
}
.toolbar-btn:hover {
  background: var(--color-hover);
  color: var(--color-text-primary);
}
.toolbar-btn.active {
  background: var(--color-hover);
  color: var(--color-text-primary);
  font-weight: 500;
}
</style>