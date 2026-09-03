<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApiConfig } from '../api'

const title = ref('')
const content = ref('')
const saved = ref(false)
const error = ref('')
const loading = ref(false)

onMounted(async () => {
  try {
    const res = await adminApiConfig.getDocs()
    const v = res.data?.value
    title.value = v?.title || ''
    content.value = v?.content || ''
  } catch {
    // ignore
  }
})

async function save() {
  saved.value = false
  error.value = ''
  loading.value = true
  try {
    await adminApiConfig.updateDocs({ title: title.value.trim(), content: content.value })
    saved.value = true
    setTimeout(() => (saved.value = false), 2500)
  } catch (e: any) {
    error.value = e.message || '保存失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="config-page">
    <div class="cp-header">
      <h2 class="cp-title">API 接入文档</h2>
      <p class="cp-sub">发布于工作台「API 服务」页面，支持 HTML 富文本</p>
    </div>

    <div class="cp-form">
      <label>文档标题
        <input v-model="title" class="cp-input" placeholder="LeafAI API 接入文档" />
      </label>
      <label>文档内容（支持 HTML）
        <textarea v-model="content" class="cp-textarea" rows="14" placeholder="<p>...</p>" />
      </label>

      <div class="cp-ops">
        <button class="btn primary" :disabled="loading" @click="save">{{ loading ? '保存中...' : '保存' }}</button>
        <span v-if="saved" class="cp-ok">已保存</span>
        <span v-if="error" class="cp-err">{{ error }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.config-page { max-width: 760px; }
.cp-header { margin-bottom: 18px; }
.cp-title { font-size: 22px; font-weight: 600; }
.cp-sub { font-size: 13px; color: var(--color-text-secondary); margin-top: 6px; }
.cp-form { display: flex; flex-direction: column; gap: 16px; }
.cp-form label { display: flex; flex-direction: column; gap: 8px; font-size: 13px; color: var(--color-text-secondary); }
.cp-input {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-bg-white);
}
.cp-textarea {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 13px;
  font-family: monospace;
  color: var(--color-text-primary);
  background: var(--color-bg-white);
  resize: vertical;
}
.cp-ops { display: flex; align-items: center; gap: 12px; }
.btn { padding: 9px 18px; border-radius: 8px; background: var(--color-bg-white); border: 1px solid var(--color-border); color: var(--color-text-primary); cursor: pointer; }
.btn.primary { background: var(--color-accent); color: #fff; border-color: transparent; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.cp-ok { color: #15803d; font-size: 13px; }
.cp-err { color: #dc2626; font-size: 13px; }
</style>