<script setup lang="ts">
defineProps<{
  sidebarVisible: boolean
}>()

const emit = defineEmits<{
  toggleSidebar: []
}>()
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
        <h1 class="doc-title">LeafAI</h1>
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

    <div class="content-body">
      <div class="doc-content">
        <p>欢迎使用 LeafAI，这是一个生成与协作平台。</p>
        <p>你可以通过底部的输入栏与 AI 进行对话，生成各类文档内容。</p>
        <p>左侧导航栏可以帮助你快速切换功能模块和查看历史记录。</p>
      </div>
    </div>

    <button class="scroll-btn" title="滚动到下一节" @click="$emit('scrollNext')">
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
  font-size: 22px;
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
  padding: 32px 48px;
  padding-bottom: calc(var(--input-bar-height) + 32px);
}

.doc-content p {
  font-size: 15px;
  line-height: 1.8;
  color: var(--color-text-primary);
  margin-bottom: 16px;
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