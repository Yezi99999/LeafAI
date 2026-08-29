<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api, type TaskStatusResult, type ResolutionConfig } from '../api/index'

const prompt = ref('')
const selectedResolution = ref('')
const selectedRatio = ref('')
const quality = ref('medium')
const referenceImage = ref('')

const generating = ref(false)
const taskId = ref('')
const taskStatus = ref('')
const taskError = ref('')
const resultImage = ref('')
const resultImages = ref<string[]>([])
const pollProgress = ref(0)
const pollTimer = ref<ReturnType<typeof setInterval> | null>(null)

const resolutionConfig = ref<ResolutionConfig[]>([])
const loading = ref(true)

const selectedRatioObj = computed(() =>
  resolutionConfig.value.find((r) => r.ratio === selectedRatio.value)
)

const availableResolutions = computed(() => {
  const obj = selectedRatioObj.value
  if (!obj) return []
  return Object.entries(obj.resolutions).map(([key, val]) => ({
    key,
    original: val.original,
    aligned: val.aligned,
  }))
})

const sizeInfo = computed(() => {
  const obj = selectedRatioObj.value
  if (obj && selectedResolution.value) {
    const res = obj.resolutions[selectedResolution.value]
    if (res) return res.aligned
  }
  return '1024x1024'
})

const pixelCount = computed(() => {
  const [w, h] = sizeInfo.value.split('x').map(Number)
  return w * h
})

const pixelValid = computed(() => {
  const pc = pixelCount.value
  return pc >= 655360 && pc <= 8294400
})

const ratios = computed(() =>
  resolutionConfig.value.map((r) => ({
    value: r.ratio,
    label: r.description ? `${r.ratio} ${r.description}` : r.ratio,
  }))
)

const qualities = [
  { value: 'low', label: '低 (快速)' },
  { value: 'medium', label: '中 (默认)' },
  { value: 'high', label: '高 (精细)' },
]

onMounted(async () => {
  try {
    const res = await api.getResolutions()
    const ratios = res.data?.aspect_ratios || []
    resolutionConfig.value = ratios
    if (ratios.length > 0) {
      selectedRatio.value = ratios[0].ratio
      const keys = Object.keys(ratios[0].resolutions)
      selectedResolution.value = keys.length > 0 ? keys[0] : ''
    }
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
})

async function handleGenerate() {
  if (!prompt.value.trim() || !pixelValid.value) return

  generating.value = true
  taskError.value = ''
  resultImage.value = ''
  taskStatus.value = ''

  try {
    const res = await api.generateImage({
      model_id: 1,
      prompt: prompt.value.trim(),
      resolution: selectedResolution.value,
      aspect_ratio: selectedRatio.value,
      quality: quality.value,
      image: referenceImage.value ? [referenceImage.value] : undefined,
    })

    taskId.value = res.data.task_id
    taskStatus.value = 'pending'
    startPolling()
  } catch (e: any) {
    taskError.value = e.message || '生成失败'
    generating.value = false
  }
}

function startPolling() {
  pollTimer.value = setInterval(async () => {
    try {
      const res = await api.getTaskStatus(taskId.value)
      const task = res.data
      taskStatus.value = task.status

      const result = task.result || {}
      if (result.progress != null) {
        pollProgress.value = result.progress
      }

      if (task.status === 'success') {
        stopPolling()
        generating.value = false
        pollProgress.value = 100

        const images = result.images || []
        if (images.length > 0) {
          resultImages.value = images
          resultImage.value = images[0]
        } else if (result.raw_response?.data?.[0]?.url) {
          resultImage.value = result.raw_response.data[0].url
        } else if (result.raw_response?.url) {
          resultImage.value = result.raw_response.url
        }
      } else if (task.status === 'failed') {
        stopPolling()
        generating.value = false
        taskError.value = task.error_msg || '生成失败'
      }
    } catch {
      // ignore poll errors
    }
  }, 2000)
}

function stopPolling() {
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

function handleReset() {
  stopPolling()
  generating.value = false
  taskId.value = ''
  taskStatus.value = ''
  taskError.value = ''
  resultImage.value = ''
  resultImages.value = []
  pollProgress.value = 0
}

function onRatioChange() {
  const obj = selectedRatioObj.value
  if (obj) {
    const keys = Object.keys(obj.resolutions)
    selectedResolution.value = keys.length > 0 ? keys[0] : ''
  }
}
</script>

<template>
  <div class="image-generator">
    <div class="ig-panel">
      <h2 class="ig-title">图片生成</h2>

      <div v-if="loading" class="ig-loading">加载分辨率配置...</div>

      <div v-else class="ig-form">
        <div class="ig-field">
          <label class="ig-label">描述词 (Prompt)</label>
          <textarea
            v-model="prompt"
            class="ig-textarea"
            placeholder="描述你想要的图片内容..."
            rows="3"
            :disabled="generating"
          />
          <span class="ig-hint">{{ prompt.length }} / 5000</span>
        </div>

        <div class="ig-row">
          <div class="ig-field">
            <label class="ig-label">宽高比</label>
            <select v-model="selectedRatio" class="ig-select" :disabled="generating" @change="onRatioChange">
              <option v-for="r in ratios" :key="r.value" :value="r.value">
                {{ r.label }}
              </option>
            </select>
          </div>

          <div class="ig-field">
            <label class="ig-label">分辨率</label>
            <select v-model="selectedResolution" class="ig-select" :disabled="generating">
              <option v-for="r in availableResolutions" :key="r.key" :value="r.key">
                {{ r.key }} ({{ r.aligned }})
              </option>
            </select>
          </div>

          <div class="ig-field">
            <label class="ig-label">质量</label>
            <select v-model="quality" class="ig-select" :disabled="generating">
              <option v-for="q in qualities" :key="q.value" :value="q.value">
                {{ q.label }}
              </option>
            </select>
          </div>
        </div>

        <div class="ig-field">
          <label class="ig-label">参考图 URL (可选)</label>
          <input
            v-model="referenceImage"
            class="ig-input"
            type="text"
            placeholder="https://example.com/reference.png"
            :disabled="generating"
          />
        </div>

        <div class="ig-info">
          <span>计算尺寸: <strong>{{ sizeInfo }}</strong></span>
          <span>像素总数: <strong>{{ pixelCount.toLocaleString() }}</strong></span>
          <span :class="pixelValid ? 'valid' : 'invalid'">
            {{ pixelValid ? '✓ 符合像素预算' : '✗ 超出像素预算 (655,360 ~ 8,294,400)' }}
          </span>
        </div>
      </div>

      <div class="ig-actions">
        <button
          class="ig-btn primary"
          :disabled="!prompt.trim() || !pixelValid || generating"
          @click="handleGenerate"
        >
          <svg v-if="generating" class="spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" stroke-opacity="0.25" />
            <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round" />
          </svg>
          {{ generating ? '生成中...' : '生成图片' }}
        </button>
        <button v-if="generating || resultImage" class="ig-btn" @click="handleReset">
          重置
        </button>
      </div>

      <div v-if="taskStatus" class="ig-status">
        <div class="status-row">
          <span class="status-label">任务状态:</span>
          <span :class="['status-badge', taskStatus]">
            {{ taskStatus === 'pending' ? '排队中' : taskStatus === 'running' ? '生成中' : taskStatus === 'success' ? '已完成' : '失败' }}
          </span>
          <span v-if="taskId" class="task-id">ID: {{ taskId }}</span>
        </div>
        <div v-if="pollProgress > 0" class="progress-bar-wrapper">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: pollProgress + '%' }" />
          </div>
          <span class="progress-text">{{ pollProgress }}%</span>
        </div>
      </div>

      <div v-if="taskError" class="ig-error">
        {{ taskError }}
      </div>

      <div v-if="resultImage" class="ig-result">
        <img :src="resultImage" alt="生成结果" class="result-img" />
        <a :href="resultImage" target="_blank" class="ig-link">查看原图</a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.image-generator {
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 40px 24px;
  overflow-y: auto;
}

.ig-panel {
  width: 100%;
  max-width: 680px;
  background: var(--color-bg-white);
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--color-border);
}

.ig-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 24px;
  color: var(--color-text-primary);
}

.ig-loading {
  text-align: center;
  padding: 40px 0;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.ig-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ig-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.ig-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.ig-textarea {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  font-size: 14px;
  font-family: inherit;
  line-height: 1.5;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s;
  background: var(--color-bg-page);
}
.ig-textarea:focus {
  border-color: var(--color-accent);
}

.ig-select,
.ig-input {
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s;
  background: var(--color-bg-page);
  color: var(--color-text-primary);
}
.ig-select:focus,
.ig-input:focus {
  border-color: var(--color-accent);
}

.ig-hint {
  font-size: 11px;
  color: var(--color-text-secondary);
  text-align: right;
}

.ig-row {
  display: flex;
  gap: 12px;
}

.ig-info {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--color-text-secondary);
  padding: 8px 12px;
  background: var(--color-bg-page);
  border-radius: 8px;
  flex-wrap: wrap;
}
.ig-info .valid { color: #10B981; }
.ig-info .invalid { color: #EF4444; }

.ig-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.ig-btn {
  padding: 10px 24px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.15s;
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
}
.ig-btn:hover:not(:disabled) {
  background: var(--color-hover);
}
.ig-btn.primary {
  background: var(--color-accent);
  color: #fff;
  border-color: var(--color-accent);
}
.ig-btn.primary:hover:not(:disabled) {
  opacity: 0.9;
}
.ig-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.ig-status {
  margin-top: 16px;
  padding: 12px;
  background: var(--color-bg-page);
  border-radius: 8px;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.status-label {
  color: var(--color-text-secondary);
}

.status-badge {
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.status-badge.pending { background: #FEF3C7; color: #D97706; }
.status-badge.running { background: #DBEAFE; color: #2563EB; }
.status-badge.success { background: #D1FAE5; color: #059669; }
.status-badge.failed { background: #FEE2E2; color: #DC2626; }

.task-id {
  font-size: 11px;
  color: var(--color-text-secondary);
  font-family: monospace;
}

.progress-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #E5E7EB;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-accent);
  border-radius: 3px;
  transition: width 0.5s ease;
}

.progress-text {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
  min-width: 36px;
  text-align: right;
}

.ig-error {
  margin-top: 16px;
  padding: 12px;
  background: #FEE2E2;
  color: #DC2626;
  border-radius: 8px;
  font-size: 13px;
}

.ig-result {
  margin-top: 20px;
  text-align: center;
}

.result-img {
  max-width: 100%;
  max-height: 480px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.ig-link {
  display: inline-block;
  margin-top: 10px;
  font-size: 13px;
  color: var(--color-accent);
  text-decoration: none;
}
.ig-link:hover {
  text-decoration: underline;
}
</style>