<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { apiUpload } from '../api'
import type { ResolutionConfig } from '../api/index'

const props = defineProps<{
  activeMode: 'chat' | 'image'
  resolutionConfig: ResolutionConfig[]
  enabledFeatures?: Set<string>
  collapsed?: boolean
  imageModels?: Array<{ id: number; label: string; promptMaxLength: number }>
  freeQuotaImage?: number
  pointsBalance?: number
}>()

const prompt = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const showModelDropdown = ref(false)
const showRatioDropdown = ref(false)
const showQualityDropdown = ref(false)
const modelSelectorRef = ref<HTMLElement | null>(null)
const ratioSelectorRef = ref<HTMLElement | null>(null)
const qualitySelectorRef = ref<HTMLElement | null>(null)

// 图片模式：参考图上传（40x60px 堆叠卡片预览，走后端存储接口拿 URL）
const uploadedImages = ref<string[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const uploadError = ref('')
const uploadMaxMb = ref(5)
const uploadMaxCount = ref(6)

onMounted(async () => {
  document.addEventListener('click', onDocumentClick)
  try {
    const res = await apiUpload.getConfig()
    uploadMaxMb.value = res.data?.max_size_mb ?? 5
    uploadMaxCount.value = res.data?.max_count ?? 6
  } catch {
    // 未登录或接口不可用时使用默认限制
  }
})

function triggerUpload() {
  fileInputRef.value?.click()
}

async function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files || [])
  input.value = '' // 允许重复选择同一文件
  if (files.length) await processFiles(files)
}

const dragOver = ref(false)

function onDragEnter(e: DragEvent) {
  if (uploading.value || !(e.dataTransfer?.types || []).includes('Files')) return
  dragOver.value = true
}

function onDragLeave() {
  dragOver.value = false
}

async function onDrop(e: DragEvent) {
  dragOver.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  if (files.length) await processFiles(files)
}

async function processFiles(files: File[]) {
  if (!files.length || uploading.value) return
  uploading.value = true
  uploadError.value = ''
  try {
    const remaining = uploadMaxCount.value - uploadedImages.value.length
    const batch = files.slice(0, Math.max(0, remaining))
    for (const file of batch) {
      if (!file.type.startsWith('image/')) continue
      if (file.size > uploadMaxMb.value * 1024 * 1024) {
        uploadError.value = `单张图片不能超过 ${uploadMaxMb.value}MB`
        continue
      }
      try {
        const res = await apiUpload.uploadImage(file)
        if (res.data?.url) uploadedImages.value.push(res.data.url)
      } catch (err: any) {
        uploadError.value = err.message || '上传失败'
      }
    }
  } finally {
    uploading.value = false
  }
}

function removeImage(idx: number) {
  uploadedImages.value.splice(idx, 1)
  uploadError.value = ''
}

// 供外部（重做）填充输入框
function setPrompt(text: string) {
  prompt.value = text
  nextTick(() => {
    textareaRef.value?.focus()
  })
}

defineExpose({ setPrompt })

interface ModelOption {
  id: number | string
  label: string
  promptMaxLength: number
}

const models = ref<ModelOption[]>([{ id: 'auto', label: 'AUTO', promptMaxLength: 5000 }])
const selectedModel = ref<ModelOption>(models.value[0])

const promptMaxLength = computed(() => selectedModel.value.promptMaxLength)
const promptLength = computed(() => prompt.value.length)
const promptExceeded = computed(() => promptLength.value > promptMaxLength.value)

const modes = [
  { id: 'chat', label: '对话', icon: 'chat', feature: 'chat' },
  { id: 'image', label: '图片生成', icon: 'image', feature: 'image_generate' },
  { id: 'video', label: '视频生成', icon: 'video', feature: 'video_generate' },
  { id: 'translate', label: '翻译', icon: 'translate' },
  { id: 'more', label: '更多', icon: 'more' },
] as const

// 功能开关关闭时隐藏对应模式按钮；无映射的（翻译/更多）始终显示
const visibleModes = computed(() =>
  modes.filter((m) => !('feature' in m) || (props.enabledFeatures?.has(m.feature!) ?? true))
)

const qualities = [
  { value: 'low', label: '低 (快速)' },
  { value: 'medium', label: '中 (默认)' },
  { value: 'high', label: '高 (精细)' },
]

const selectedRatio = ref('')
const selectedResolution = ref('')
const selectedQuality = ref(qualities[1])

const ratioOptions = computed(() =>
  props.resolutionConfig.map((r) => ({
    value: r.ratio,
    label: r.ratio,
  }))
)

const currentRatioObj = computed(() =>
  props.resolutionConfig.find((r) => r.ratio === selectedRatio.value)
)

const resolutionOptions = computed(() => {
  const obj = currentRatioObj.value
  if (!obj) return []
  const order = ['1K', '2K', '4K']
  return order
    .filter((k) => obj.resolutions[k])
    .map((k) => ({
      value: k,
      label: k,
    }))
})

const ratioLabel = computed(() => {
  const opt = ratioOptions.value.find((r) => r.value === selectedRatio.value)
  return opt ? opt.label : '宽高比'
})

const resolutionLabel = computed(() => {
  return selectedResolution.value || '分辨率'
})

const qualityLabel = computed(() => {
  return selectedQuality.value.label
})

// 免费次数 / 积分提示
const imageQuotaHint = computed(() => {
  const q = props.freeQuotaImage ?? 0
  if (q === -1) return '免费不限次数'
  if (q > 0) return `免费次数剩余 ${q} 次`
  return `消耗积分 · 余额 ${props.pointsBalance ?? 0}`
})

const emit = defineEmits<{
  send: [message: string]
  modeChange: [mode: string]
  imageGenerate: [params: {
    prompt: string
    resolution: string
    aspectRatio: string
    quality: string
    modelId?: number | string
    images?: string[]
  }]
  expand: []
}>()

function expandInput() {
  emit('expand')
  nextTick(() => {
    const el = document.querySelector('.input-field') as HTMLTextAreaElement | null
    el?.focus()
  })
}

function handleSend() {
  if (!prompt.value.trim()) return
  if (promptExceeded.value) return

  if (props.activeMode === 'image') {
    emit('imageGenerate', {
      prompt: prompt.value.trim(),
      resolution: selectedResolution.value,
      aspectRatio: selectedRatio.value,
      quality: selectedQuality.value.value,
      modelId: selectedModel.value.id,
      images: [...uploadedImages.value],
    })
    uploadedImages.value = []
  } else {
    emit('send', prompt.value)
  }
  prompt.value = ''
  autoResize()
}

function autoResize() {
  nextTick(() => {
    const el = document.querySelector('.input-field') as HTMLTextAreaElement
    if (el) {
      el.style.height = 'auto'
      el.style.height = Math.min(el.scrollHeight, 260) + 'px'
    }
  })
}

function onInput() {
  autoResize()
}

function setActiveMode(modeId: string) {
  emit('modeChange', modeId)
}

function selectModel(model: ModelOption) {
  selectedModel.value = model
  showModelDropdown.value = false
}

function selectRatio(ratio: string) {
  selectedRatio.value = ratio
  showRatioDropdown.value = false
  const obj = props.resolutionConfig.find((r) => r.ratio === ratio)
  if (obj) {
    const keys = Object.keys(obj.resolutions)
    selectedResolution.value = keys.length > 0 ? keys[0] : ''
  }
}

function selectResolution(res: string) {
  selectedResolution.value = res
  showRatioDropdown.value = false
}

function selectQuality(q: typeof qualities[0]) {
  selectedQuality.value = q
  showQualityDropdown.value = false
}

function toggleDropdown(type: string) {
  showModelDropdown.value = false
  showRatioDropdown.value = false
  showQualityDropdown.value = false
  if (type === 'model') showModelDropdown.value = true
  else if (type === 'ratio') showRatioDropdown.value = true
  else if (type === 'quality') showQualityDropdown.value = true
}

function onDocumentClick(e: MouseEvent) {
  const target = e.target as Node
  if (modelSelectorRef.value && !modelSelectorRef.value.contains(target)) {
    showModelDropdown.value = false
  }
  if (ratioSelectorRef.value && !ratioSelectorRef.value.contains(target)) {
    showRatioDropdown.value = false
  }
  if (qualitySelectorRef.value && !qualitySelectorRef.value.contains(target)) {
    showQualityDropdown.value = false
  }
}

watch(
  () => props.resolutionConfig,
  (config) => {
    if (config.length === 0) return
    if (selectedRatio.value) return
    const idx9x16 = config.findIndex((r) => r.ratio === '9:16')
    const idx = idx9x16 >= 0 ? idx9x16 : 0
    selectedRatio.value = config[idx].ratio
    const keys = Object.keys(config[idx].resolutions)
    const k1k = keys.find((k) => k === '1K')
    selectedResolution.value = k1k || (keys.length > 0 ? keys[0] : '')
  },
  { immediate: true }
)

onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
})

// 模型列表由 App.vue 在登录后加载并下发，避免未登录时的鉴权 401 导致列表为空
watch(
  () => props.imageModels,
  (items) => {
    if (!items || !Array.isArray(items)) return
    const remoteModels: ModelOption[] = items.map((m) => ({
      id: m.id,
      label: m.label,
      promptMaxLength: m.promptMaxLength,
    }))
    models.value = [{ id: 'auto', label: 'AUTO', promptMaxLength: 5000 }, ...remoteModels]
    if (selectedModel.value.id === 'auto') {
      selectedModel.value = models.value[0]
    }
  },
  { immediate: true }
)
</script>

<template>
  <div class="input-bar" :class="{ collapsed: collapsed }">
    <Transition name="collapse">
      <div v-if="collapsed" class="input-card collapsed-card">
        <input
          class="collapsed-input"
          :placeholder="activeMode === 'image' ? '描述你想要的图片内容...' : '发消息...'"
          @focus="expandInput"
          @click="expandInput"
        />
      </div>
      <div v-else class="input-card">
        <Transition name="mode-fade" mode="out-in">
        <div v-if="activeMode === 'image'" class="image-options">
        <div ref="modelSelectorRef" class="option-selector">
          <button class="option-badge" @click="toggleDropdown('model')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
            <span>{{ selectedModel.label }}</span>
            <svg :class="['chevron', { open: showModelDropdown }]" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          <Transition name="dropdown">
            <div v-if="showModelDropdown" class="option-dropdown">
              <div
                v-for="model in models"
                :key="model.id"
                :class="['dropdown-option', { active: selectedModel.id === model.id }]"
                @click="selectModel(model)"
              >
                {{ model.label }}
                <svg v-if="selectedModel.id === model.id" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
            </div>
          </Transition>
        </div>

        <div ref="ratioSelectorRef" class="option-selector">
          <button class="option-badge" @click="toggleDropdown('ratio')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" />
            </svg>
            <span>{{ ratioLabel }}</span>
            <span class="option-sep">·</span>
            <span>{{ resolutionLabel }}</span>
            <svg :class="['chevron', { open: showRatioDropdown }]" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          <Transition name="dropdown">
            <div v-if="showRatioDropdown" class="option-dropdown ratio-dropdown">
              <div class="dropdown-columns">
                <div class="dropdown-col">
                  <div class="dropdown-label">宽高比</div>
                  <div
                    v-for="r in ratioOptions"
                    :key="r.value"
                    :class="['dropdown-option', { active: selectedRatio === r.value }]"
                    @click="selectRatio(r.value)"
                  >
                    {{ r.label }}
                    <svg v-if="selectedRatio === r.value" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </div>
                </div>
                <div class="dropdown-col-sep" />
                <div class="dropdown-col">
                  <div class="dropdown-label">分辨率</div>
                  <div
                    v-for="r in resolutionOptions"
                    :key="r.value"
                    :class="['dropdown-option', { active: selectedResolution === r.value }]"
                    @click="selectResolution(r.value)"
                  >
                    {{ r.label }}
                    <svg v-if="selectedResolution === r.value" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </div>

        <div ref="qualitySelectorRef" class="option-selector">
          <button class="option-badge" @click="toggleDropdown('quality')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 6v6l4 2" />
            </svg>
            <span>{{ qualityLabel }}</span>
            <svg :class="['chevron', { open: showQualityDropdown }]" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          <Transition name="dropdown">
            <div v-if="showQualityDropdown" class="option-dropdown">
              <div
                v-for="q in qualities"
                :key="q.value"
                :class="['dropdown-option', { active: selectedQuality.value === q.value }]"
                @click="selectQuality(q)"
              >
                {{ q.label }}
                <svg v-if="selectedQuality.value === q.value" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
            </div>
          </Transition>
        </div>

        <div
          class="upload-dropper"
          :class="{ dragover: dragOver }"
          @dragover.prevent
          @dragenter.prevent="onDragEnter"
          @dragleave="onDragLeave"
          @drop.prevent="onDrop"
        >
          <button class="upload-badge" type="button" :disabled="uploading" @click="triggerUpload">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <span>{{ uploading ? '上传中...' : `图片${uploadedImages.length}/${uploadMaxCount}` }}</span>
          </button>
          <input ref="fileInputRef" type="file" accept="image/*" multiple style="display: none" @change="onFileChange" />
        </div>

        <span class="image-quota-hint">{{ imageQuotaHint }}</span>

        <div v-if="uploadedImages.length" class="image-stack">
          <TransitionGroup name="stack" tag="div" class="image-stack-inner">
            <div v-for="(img, i) in uploadedImages" :key="img" class="image-stack-card">
              <img :src="img" alt="参考图" />
              <button class="stack-remove" type="button" @click="removeImage(i)">
                <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          </TransitionGroup>
        </div>
        <div v-if="uploadError" class="upload-error-hint">{{ uploadError }}</div>
      </div>
        </Transition>

      <div class="input-row">
        <div class="input-wrapper">
          <textarea
            ref="textareaRef"
            v-model="prompt"
            class="input-field"
            :class="{ exceeded: promptExceeded }"
            :placeholder="activeMode === 'image' ? '描述你想要的图片内容...' : '发消息...'"
            rows="1"
            @input="onInput"
            @keyup.enter.exact="handleSend"
          />
          <span v-if="activeMode === 'image'" class="prompt-counter" :class="{ exceeded: promptExceeded }">
            {{ promptLength }} / {{ promptMaxLength }}
          </span>
        </div>

        <button class="send-btn" :class="{ active: prompt.trim() }" @click="handleSend">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="19" x2="12" y2="5" />
            <polyline points="5 12 12 5 19 12" />
          </svg>
        </button>
      </div>

      <div class="toolbar">
        <button
          v-for="mode in visibleModes"
          :key="mode.id"
          :class="['toolbar-btn', { active: activeMode === mode.id }]"
          @click="setActiveMode(mode.id)"
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
    </Transition>
  </div>
</template>

<style scoped>
.input-bar {
  position: fixed;
  bottom: 0;
  left: var(--sidebar-width);
  right: 0;
  z-index: 10;
  padding: 0 24px 20px;
  background: transparent;
  pointer-events: none;
  min-width: 540px;
}

.collapse-enter-active,
.collapse-leave-active {
  transition: opacity 0.25s, transform 0.25s;
}
.collapse-enter-from {
  opacity: 0;
  transform: translateY(10px) scale(0.98);
}
.collapse-leave-to {
  opacity: 0;
  transform: translateY(6px) scale(0.99);
}

.mode-fade-enter-active {
  transition: opacity 0.2s, transform 0.2s;
}
.mode-fade-leave-active {
  transition: opacity 0.1s, transform 0.1s;
}
.mode-fade-enter-from {
  opacity: 0;
  transform: translateY(-6px);
}
.mode-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.input-card {
  max-width: 780px;
  margin: 0 auto;
  background: var(--color-bg-white);
  border-radius: 16px;
  padding: 16px 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid var(--color-border);
  pointer-events: auto;
}

.input-bar.collapsed .input-card {
  max-width: 440px;
}

.collapsed-card {
  padding: 0;
  overflow: hidden;
}

.collapsed-input {
  width: 100%;
  padding: 12px 18px;
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-bg-page);
  border: none;
  outline: none;
  cursor: text;
  font-family: inherit;
  text-align: center;
}
.collapsed-input::placeholder {
  color: var(--color-text-secondary);
}
.collapsed-input:focus {
  background: transparent;
}

.image-options {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.option-selector {
  position: relative;
}

.option-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--color-text-secondary);
  padding: 5px 12px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-page);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
  white-space: nowrap;
}
.option-badge:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.option-sep {
  color: var(--color-border);
  margin: 0 -2px;
}

.option-dropdown {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 0;
  min-width: 160px;
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.1);
  padding: 4px;
  z-index: 30;
}

.ratio-dropdown {
  min-width: 240px;
}

.dropdown-columns {
  display: flex;
  gap: 0;
}

.dropdown-col {
  flex: 1;
  min-width: 0;
}

.dropdown-col-sep {
  width: 1px;
  background: var(--color-border);
  margin: 4px 0;
}

.dropdown-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-secondary);
  padding: 4px 12px 2px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.dropdown-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: var(--color-text-primary);
  cursor: pointer;
  transition: background 0.12s;
}
.dropdown-option:hover {
  background: var(--color-hover);
}
.dropdown-option.active {
  color: var(--color-accent);
  font-weight: 500;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.input-wrapper {
  flex: 1;
  background: var(--color-bg-page);
  border-radius: 12px;
  padding: 8px 16px;
  border: 1px solid transparent;
  transition: border-color 0.15s;
}
.input-wrapper:focus-within {
  border-color: var(--color-accent);
}

.input-field {
  width: 100%;
  padding: 4px 0;
  font-size: 14px;
  color: var(--color-text-primary);
  resize: none;
  border: none;
  outline: none;
  background: transparent;
  font-family: inherit;
  line-height: 1.5;
  max-height: 260px;
  overflow-y: auto;
}
.input-field::placeholder {
  color: var(--color-text-secondary);
}
.input-field::-webkit-scrollbar {
  display: none;
}
.input-field {
  scrollbar-width: none;
}
.input-field.exceeded {
  color: #e74c3c;
}

.prompt-counter {
  display: block;
  text-align: right;
  font-size: 11px;
  color: var(--color-text-secondary);
  margin-top: 2px;
  transition: color 0.15s;
}
.prompt-counter.exceeded {
  color: #e74c3c;
}

.image-quota-hint {
  display: inline-block;
  margin-bottom: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.upload-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--color-accent);
  padding: 5px 12px;
  border: 1px dashed var(--color-accent);
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}
.upload-badge:hover {
  background: color-mix(in srgb, var(--color-accent) 12%, transparent);
}
.upload-badge:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.upload-dropper {
  position: relative;
  display: inline-flex;
  border-radius: 10px;
  transition: box-shadow 0.15s, background 0.15s;
}
.upload-dropper.dragover {
  background: color-mix(in srgb, var(--color-accent) 14%, transparent);
  box-shadow: 0 0 0 2px var(--color-accent);
}
.upload-dropper .upload-badge {
  pointer-events: auto;
}

.upload-error-hint {
  font-size: 12px;
  color: #e74c3c;
  margin-top: 2px;
}

/* 40x60px 参考图堆叠卡片 */
.image-stack {
  margin-bottom: 12px;
  padding-left: 4px;
}
.image-stack-inner {
  display: flex;
}
.image-stack-card {
  position: relative;
  width: 40px;
  height: 60px;
  flex-shrink: 0;
  margin-left: -10px;
  border-radius: 6px;
  overflow: hidden;
  border: 1.5px solid var(--color-bg-white);
  background: var(--color-bg-page);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.18);
  transition: margin-left 0.25s;
}
.image-stack-card:first-child {
  margin-left: 0;
}
.image-stack-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.stack-remove {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 13px;
  height: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  opacity: 0;
  transition: opacity 0.15s;
  cursor: pointer;
}
.image-stack-card:hover .stack-remove {
  opacity: 1;
}

.stack-enter-active {
  transition: all 0.25s;
}
.stack-leave-active {
  transition: all 0.2s;
}
.stack-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.stack-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

.chevron {
  transition: transform 0.2s;
}
.chevron.open {
  transform: rotate(180deg);
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}
.send-btn:hover {
  background: var(--color-accent);
  color: #fff;
}

.dropdown-enter-active {
  transition: opacity 0.15s, transform 0.15s;
}
.dropdown-leave-active {
  transition: opacity 0.1s, transform 0.1s;
}
.dropdown-enter-from {
  opacity: 0;
  transform: translateY(4px);
}
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
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
  color: var(--color-accent);
}
</style>