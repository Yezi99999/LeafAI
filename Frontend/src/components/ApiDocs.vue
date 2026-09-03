<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../api'

const loading = ref(true)
const title = ref('LeafAI API 接入文档')
const content = ref('')
const error = ref('')

onMounted(async () => {
  try {
    const res = await api.getApiDocs()
    const v = res.data?.value
    title.value = v?.title || 'LeafAI API 接入文档'
    content.value = v?.content || ''
  } catch (e: any) {
    error.value = e.message || '文档加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <main class="api-docs">
    <header class="docs-header">
      <h2 class="docs-title">{{ title }}</h2>
      <p class="docs-sub">Leaf AI接口文档</p>
    </header>

    <div v-if="loading" class="docs-loading">加载中...</div>
    <div v-else-if="error" class="docs-error">{{ error }}</div>
    <div v-else class="docs-body" v-html="content"></div>
  </main>
</template>

<style scoped>
.api-docs {
  flex: 1;
  overflow-y: auto;
  padding: 56px 40px 40px;
  background: var(--color-bg-page);
}
.docs-header {
  max-width: 760px;
  margin: 0 auto 24px;
}
.docs-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-text-primary);
}
.docs-sub {
  margin-top: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.docs-loading,
.docs-error {
  text-align: center;
  padding: 40px;
  color: var(--color-text-secondary);
}
.docs-error {
  color: #dc2626;
}
.docs-body {
  max-width: 820px;
  margin: 0 auto;
  padding: 28px 32px;
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.75;
  color: var(--color-text-primary);
}
.docs-body :deep(h1),
.docs-body :deep(h2),
.docs-body :deep(h3) {
  margin: 22px 0 10px;
  color: var(--color-text-primary);
}
.docs-body :deep(h1) {
  font-size: 24px;
  margin-top: 4px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}
.docs-body :deep(h2) {
  font-size: 18px;
  padding-top: 6px;
}
.docs-body :deep(h3) {
  font-size: 15px;
}
.docs-body :deep(p) {
  margin: 10px 0;
}
.docs-body :deep(ul),
.docs-body :deep(ol) {
  margin: 10px 0 10px 22px;
}
.docs-body :deep(li) {
  margin: 4px 0;
}
.docs-body :deep(a) {
  color: var(--color-accent);
  text-decoration: none;
}
.docs-body :deep(a:hover) {
  text-decoration: underline;
}
.docs-body :deep(code) {
  background: rgba(37, 99, 235, 0.08);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 13px;
  color: #1d4ed8;
}
.docs-body :deep(pre) {
  background: #0f172a;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}
.docs-body :deep(pre code) {
  background: transparent;
  color: inherit;
  padding: 0;
  font-size: 13px;
  line-height: 1.6;
}
.docs-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 13px;
}
.docs-body :deep(th),
.docs-body :deep(td) {
  border: 1px solid var(--color-border);
  padding: 8px 12px;
  text-align: left;
}
.docs-body :deep(th) {
  background: var(--color-bg-hover, #f6f7f9);
  font-weight: 600;
}
</style>