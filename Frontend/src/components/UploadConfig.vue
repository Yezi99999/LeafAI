<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiUpload, adminApiConfig } from '../api'

const maxSizeMb = ref(5)
const maxCount = ref(6)
const saved = ref(false)
const error = ref('')
const loading = ref(false)

onMounted(async () => {
  try {
    const res = await apiUpload.getConfig()
    maxSizeMb.value = res.data?.max_size_mb ?? 5
    maxCount.value = res.data?.max_count ?? 6
  } catch {
    // ignore
  }
})

async function save() {
  if (maxSizeMb.value <= 0 || maxCount.value <= 0) {
    error.value = '大小与数量均需为正整数'
    return
  }
  saved.value = false
  error.value = ''
  loading.value = true
  try {
    await adminApiConfig.set('upload_max_size_mb', maxSizeMb.value)
    await adminApiConfig.set('upload_max_count', maxCount.value)
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
  <div class="upload-config-page">
    <div class="uc-header">
      <h2 class="uc-title">上传设置</h2>
      <p class="uc-sub">控制图片生成参考图上传限制（单图大小 / 数量），对图床接口与工作台上传均生效</p>
    </div>

    <div class="uc-form">
      <label>单张图片大小限制（MB）
        <input v-model.number="maxSizeMb" type="number" min="1" step="1" class="uc-input" />
      </label>
      <label>单次上传图片数量限制（张）
        <input v-model.number="maxCount" type="number" min="1" step="1" class="uc-input" />
      </label>

      <div class="uc-ops">
        <button class="btn primary" :disabled="loading" @click="save">{{ loading ? '保存中...' : '保存' }}</button>
        <span v-if="saved" class="uc-ok">已保存</span>
        <span v-if="error" class="uc-err">{{ error }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.upload-config-page { max-width: 520px; }
.uc-header { margin-bottom: 18px; }
.uc-title { font-size: 22px; font-weight: 600; }
.uc-sub { font-size: 13px; color: var(--color-text-secondary); margin-top: 6px; }
.uc-form { display: flex; flex-direction: column; gap: 16px; }
.uc-form label { display: flex; flex-direction: column; gap: 8px; font-size: 13px; color: var(--color-text-secondary); }
.uc-input {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-bg-white);
}
.uc-ops { display: flex; align-items: center; gap: 12px; }
.btn { padding: 9px 18px; border-radius: 8px; background: var(--color-bg-white); border: 1px solid var(--color-border); color: var(--color-text-primary); cursor: pointer; }
.btn.primary { background: var(--color-accent); color: #fff; border-color: transparent; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.uc-ok { color: #15803d; font-size: 13px; }
.uc-err { color: #dc2626; font-size: 13px; }
</style>