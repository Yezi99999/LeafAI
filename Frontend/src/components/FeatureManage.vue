<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApiFeatures, type FeatureToggle } from '../api/index'

const toggles = ref<FeatureToggle[]>([])
const loading = ref(false)
const errorMsg = ref('')

const KNOWN_CODES: Record<string, { name: string; desc: string }> = {
  image_generate: { name: '图片生成', desc: '控制图片生成能力的启停' },
  video_generate: { name: '视频生成', desc: '控制视频生成能力的启停' },
  chat: { name: '智能对话', desc: '控制对话聊天能力的启停' },
  audio_tts: { name: '语音合成', desc: '控制文本转语音能力的启停' },
  audio_asr: { name: '语音识别', desc: '控制语音转文字能力的启停' },
  points: { name: '积分体系', desc: '开关积分计费模式的启停' },
}

async function loadFeatures() {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await adminApiFeatures.listFeatures()
    toggles.value = res.data?.items || []
  } catch (e: any) {
    errorMsg.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function toggleEnabled(t: FeatureToggle) {
  try {
    await adminApiFeatures.updateFeature(t.code, { enabled: !t.enabled })
    t.enabled = !t.enabled
  } catch (e: any) {
    errorMsg.value = e.message || '操作失败'
  }
}

async function removeFeature(t: FeatureToggle) {
  if (!confirm(`确定删除开关「${t.name}」吗？`)) return
  try {
    await adminApiFeatures.deleteFeature(t.code)
    toggles.value = toggles.value.filter((x) => x.code !== t.code)
  } catch (e: any) {
    errorMsg.value = e.message || '删除失败'
  }
}

// 白名单编辑
const whitelistTarget = ref<FeatureToggle | null>(null)
const whitelistIds = ref('')
function openWhitelist(t: FeatureToggle) {
  whitelistTarget.value = t
  whitelistIds.value = (t.whitelist_user_ids || []).join(',')
}
async function saveWhitelist() {
  if (!whitelistTarget.value) return
  const ids = whitelistIds.value
    .split(',')
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
    .map(Number)
  try {
    await adminApiFeatures.updateFeature(whitelistTarget.value.code, { whitelist_user_ids: ids })
    whitelistTarget.value.whitelist_user_ids = ids
    whitelistTarget.value = null
  } catch (e: any) {
    errorMsg.value = e.message || '保存失败'
  }
}

// 新建开关
const showCreate = ref(false)
const form = ref({ code: '', name: '', description: '', defaultEnabled: true })
async function submitCreate() {
  if (!form.value.code || !form.value.name) {
    errorMsg.value = '请填写开关标识和名称'
    return
  }
  try {
    await adminApiFeatures.createFeature({
      code: form.value.code,
      name: form.value.name,
      description: form.value.description,
      enabled: form.value.defaultEnabled,
      whitelist_user_ids: [],
    })
    showCreate.value = false
    form.value = { code: '', name: '', description: '', defaultEnabled: true }
    await loadFeatures()
  } catch (e: any) {
    errorMsg.value = e.message || '创建失败'
  }
}

onMounted(loadFeatures)
</script>

<template>
  <div class="feature-manage">
    <div class="fm-header">
      <h2 class="fm-title">功能开关</h2>
      <button class="btn primary" @click="showCreate = true">新建开关</button>
    </div>

    <div v-if="errorMsg" class="fm-error">{{ errorMsg }}</div>

    <div class="fm-grid">
      <div v-for="t in toggles" :key="t.code" class="fm-card" :class="{ disabled: !t.enabled }">
        <div class="fm-card-head">
          <div class="fm-name">{{ t.name }}</div>
          <label class="switch">
            <input type="checkbox" :checked="t.enabled" @change="toggleEnabled(t)" />
            <span class="switch-slider" />
          </label>
        </div>
        <div class="fm-code">{{ t.code }}</div>
        <div class="fm-desc">{{ t.description || KNOWN_CODES[t.code]?.desc || '暂无说明' }}</div>
        <div class="fm-card-foot">
          <span class="tag" :class="t.enabled ? 'on' : 'off'">{{ t.enabled ? '开启' : '关闭' }}</span>
          <span class="fm-whitelist">白名单：{{ t.whitelist_user_ids && t.whitelist_user_ids.length ? t.whitelist_user_ids.length + ' 人' : '全量' }}</span>
          <div class="fm-ops">
            <button class="link" @click="openWhitelist(t)">白名单</button>
            <button class="link danger" @click="removeFeature(t)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <p v-if="!loading && toggles.length === 0" class="fm-empty">暂无功能开关。未配置的开关默认全量开放。</p>

    <!-- 白名单弹窗 -->
    <div v-if="whitelistTarget" class="fm-modal-mask" @click.self="whitelistTarget = null">
      <div class="fm-modal">
        <h3>灰度白名单 — {{ whitelistTarget.name }}</h3>
        <p class="fm-hint">留空表示对全量用户开放；填写用户 ID（逗号分隔）则仅白名单内用户可用（超管始终可用）。</p>
        <input v-model="whitelistIds" class="fm-input" placeholder="例如：1, 2, 55" />
        <div v-if="errorMsg" class="fm-error">{{ errorMsg }}</div>
        <div class="fm-modal-ops">
          <button class="btn" @click="whitelistTarget = null">取消</button>
          <button class="btn primary" @click="saveWhitelist">保存</button>
        </div>
      </div>
    </div>

    <!-- 新建弹窗 -->
    <div v-if="showCreate" class="fm-modal-mask" @click.self="showCreate = false">
      <div class="fm-modal">
        <h3>新建功能开关</h3>
        <div class="fm-form">
          <label>能力标识
            <input v-model="form.code" class="fm-input" placeholder="image_generate / video_generate / chat ..." />
          </label>
          <label>展示名
            <input v-model="form.name" class="fm-input" placeholder="例如：图片生成" />
          </label>
          <label>说明
            <textarea v-model="form.description" class="fm-input fm-textarea" placeholder="选填" />
          </label>
          <label class="fm-check">
            <input type="checkbox" v-model="form.defaultEnabled" />
            创建后默认开启
          </label>
        </div>
        <div v-if="errorMsg" class="fm-error">{{ errorMsg }}</div>
        <div class="fm-modal-ops">
          <button class="btn" @click="showCreate = false">取消</button>
          <button class="btn primary" @click="submitCreate">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.feature-manage {
  max-width: 1200px;
}
.fm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.fm-title {
  font-size: 22px;
  font-weight: 600;
}
.btn {
  padding: 8px 16px;
  border-radius: 8px;
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  font-size: 13px;
  cursor: pointer;
}
.btn:hover:not(:disabled) {
  background: var(--color-hover);
}
.btn.primary {
  background: var(--color-accent);
  color: #fff;
  border-color: transparent;
}
.fm-error {
  color: #dc2626;
  margin-bottom: 12px;
  font-size: 13px;
}
.fm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
.fm-card {
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 16px;
  transition: box-shadow 0.15s;
}
.fm-card.disabled {
  opacity: 0.7;
}
.fm-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.fm-name {
  font-size: 15px;
  font-weight: 600;
}
.fm-code {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 6px 0;
}
.fm-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  min-height: 38px;
  line-height: 1.5;
}
.fm-card-foot {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}
.tag {
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
}
.tag.on {
  background: #dcfce7;
  color: #15803d;
}
.tag.off {
  background: #fee2e2;
  color: #b91c1c;
}
.fm-whitelist {
  font-size: 12px;
  color: var(--color-text-secondary);
}
.fm-ops {
  margin-left: auto;
  display: flex;
  gap: 8px;
}
.link {
  color: var(--color-accent);
  font-size: 13px;
}
.link.danger {
  color: #dc2626;
}
.fm-empty {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 48px 0;
}
.switch {
  position: relative;
  width: 42px;
  height: 24px;
  display: inline-block;
}
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.switch-slider {
  position: absolute;
  inset: 0;
  background: #d1d5db;
  border-radius: 999px;
  transition: background 0.2s;
  cursor: pointer;
}
.switch-slider::before {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  left: 3px;
  top: 3px;
  background: #fff;
  border-radius: 50%;
  transition: transform 0.2s;
}
.switch input:checked + .switch-slider {
  background: var(--color-accent);
}
.switch input:checked + .switch-slider::before {
  transform: translateX(18px);
}
.fm-modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2100;
}
.fm-modal {
  width: 420px;
  background: var(--color-bg-white);
  border-radius: 14px;
  padding: 24px;
}
.fm-modal h3 {
  margin-bottom: 12px;
  font-size: 16px;
}
.fm-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 10px;
  line-height: 1.5;
}
.fm-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.fm-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.fm-form .fm-check {
  flex-direction: row;
  align-items: center;
  gap: 8px;
  color: var(--color-text-primary);
}
.fm-input {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 8px 12px;
  background: var(--color-bg-white);
  color: var(--color-text-primary);
  font-size: 13px;
}
.fm-textarea {
  min-height: 60px;
  resize: vertical;
}
.fm-modal-ops {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 18px;
}
</style>