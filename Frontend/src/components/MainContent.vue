<script setup lang="ts">
import { ref, nextTick, watch, onMounted, onUnmounted } from 'vue'

interface Message {
  id: number
  role: 'system' | 'user' | 'assistant'
  content: string
  time: string
  images?: string[]
}

interface ImageRecord {
  taskId: string
  prompt: string
  images: string[]
  status: string
  errorMsg: string
  time: string
}

const props = defineProps<{
  sidebarVisible: boolean
  mode: 'chat' | 'image'
  messages: Message[]
  imageRecords: ImageRecord[]
}>()

const emit = defineEmits<{
  toggleSidebar: []
  collapseInput: []
  expandInput: []
}>()

const COLLAPSE_THRESHOLD = 80

function onScroll() {
  if (!contentBodyRef.value) return
  const top = contentBodyRef.value.scrollTop
  if (top > COLLAPSE_THRESHOLD) {
    emit('collapseInput')
  } else if (top <= COLLAPSE_THRESHOLD) {
    emit('expandInput')
  }
}

const contentBodyRef = ref<HTMLElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    if (contentBodyRef.value) {
      contentBodyRef.value.scrollTop = contentBodyRef.value.scrollHeight
    }
  })
}

watch(() => props.messages, () => scrollToBottom(), { deep: true })

const previewRec = ref<ImageRecord | null>(null)
const previewIndex = ref(0)

function openPreview(rec: ImageRecord) {
  if (rec.images.length === 0) return
  previewRec.value = rec
  previewIndex.value = 0
}

function closePreview() {
  previewRec.value = null
}

function previewPrev() {
  if (!previewRec.value) return
  previewIndex.value = (previewIndex.value - 1 + previewRec.value.images.length) % previewRec.value.images.length
}

function previewNext() {
  if (!previewRec.value) return
  previewIndex.value = (previewIndex.value + 1) % previewRec.value.images.length
}

function onKeydown(e: KeyboardEvent) {
  if (!previewRec.value) return
  if (e.key === 'Escape') closePreview()
  else if (e.key === 'ArrowLeft') previewPrev()
  else if (e.key === 'ArrowRight') previewNext()
}

// 下载原图：先拉取为 Blob 再触发浏览器下载，避免跨域/签名链接直接跳转
async function downloadImage(url: string) {
  try {
    const res = await fetch(url)
    const blob = await res.blob()
    const ext = (blob.type.split('/')[1] || 'png').replace(/jpeg$/i, 'jpg')
    const objectUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = objectUrl
    a.download = `leafai-image-${Date.now()}.${ext}`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(objectUrl)
  } catch {
    // 降级：新窗口打开原图
    window.open(url, '_blank')
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
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

    <div ref="contentBodyRef" class="content-body" @scroll.passive="onScroll">
      <template v-if="mode === 'chat'">
        <div class="chat-messages">
          <div
            v-for="msg in messages"
            :key="msg.id"
            :class="['message-row', msg.role === 'assistant' ? 'system' : msg.role]"
          >
            <div :class="['message-bubble', msg.role === 'assistant' ? 'system' : msg.role]">
              <div class="bubble-text">{{ msg.content }}</div>
              <div v-if="msg.images && msg.images.length > 0" class="bubble-images">
                <img
                  v-for="(img, idx) in msg.images"
                  :key="idx"
                  :src="img"
                  :alt="'生成结果 ' + (idx + 1)"
                  class="result-img"
                />
              </div>
              <div class="bubble-time">{{ msg.time }}</div>
            </div>
          </div>
        </div>
      </template>

      <template v-else>
        <div class="image-records">
          <div
            v-for="rec in imageRecords"
            :key="rec.taskId"
            class="image-record-card"
            :class="{ pending: rec.status !== 'success' }"
          >
            <template v-if="rec.images.length > 0">
              <img
                :src="rec.images[0]"
                :alt="rec.prompt"
                class="image-record-img"
                loading="lazy"
                @click="openPreview(rec)"
              />
            </template>
            <div v-else class="image-record-placeholder">
              <div v-if="rec.status === 'pending' || rec.status === 'running'" class="placeholder-loading">
                <span class="spinner" />
                <span>正在生成中...</span>
              </div>
              <div v-else-if="rec.status === 'failed'" class="placeholder-failed">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <span>生成失败</span>
              </div>
              <div v-else class="placeholder-waiting">
                <span>排队中...</span>
              </div>
            </div>
            <div class="image-record-prompt">{{ rec.prompt }}</div>
            <div class="image-record-time">{{ rec.time }}</div>
          </div>
          <div v-if="imageRecords.length === 0" class="image-records-empty">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <circle cx="8.5" cy="8.5" r="1.5" />
              <polyline points="21 15 16 10 5 21" />
            </svg>
            <p>暂无图片生成记录，点击下方「图片生成」开始创作</p>
          </div>
        </div>
      </template>
    </div>

    <button class="scroll-btn" title="滚动到底部" @click="scrollToBottom">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="6 9 12 15 18 9" />
      </svg>
    </button>

    <Transition name="preview-fade">
      <div v-if="previewRec" class="preview-overlay" @click="closePreview">
        <div class="preview-body" @click.stop>
          <button class="preview-close" @click="closePreview" title="关闭">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
          <div class="preview-info">
            <div class="preview-info-label">提示词</div>
            <div class="preview-prompt">{{ previewRec.prompt }}</div>
            <div class="preview-info-label">创建时间</div>
            <div class="preview-time">
              {{ previewRec.time }}
              <template v-if="previewRec.images.length > 1"> · {{ previewIndex + 1 }}/{{ previewRec.images.length }}</template>
            </div>
            <button
              type="button"
              class="preview-download"
              @click="downloadImage(previewRec.images[previewIndex])"
            >下载原图</button>
          </div>
          <div class="preview-media">
            <div class="preview-stage">
              <button v-if="previewRec.images.length > 1" class="preview-nav prev" @click="previewPrev">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="15 18 9 12 15 6" />
                </svg>
              </button>
              <button v-if="previewRec.images.length > 1" class="preview-nav next" @click="previewNext">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </button>
              <img :src="previewRec.images[previewIndex]" :alt="previewRec.prompt" class="preview-img" />
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </main>
</template>

<style scoped>
.image-record-img {
  cursor: zoom-in;
}

.preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(12, 14, 18, 0.88);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.preview-body {
  position: relative;
  display: flex;
  gap: 28px;
  background: #fff;
  border-radius: 16px;
  padding: 28px;
  max-width: 96vw;
  max-height: 92vh;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.35);
}

.preview-info {
  width: 240px;
  flex-shrink: 0;
  color: var(--color-text-primary);
  display: flex;
  flex-direction: column;
}

.preview-info-label {
  font-size: 12px;
  letter-spacing: 0.5px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.preview-prompt {
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
  color: var(--color-text-primary);
  flex: 1;
  overflow-y: auto;
  margin-bottom: 20px;
  max-height: none;
}

.preview-time {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.preview-download {
  margin-top: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 9px 14px;
  border-radius: 8px;
  background: var(--color-accent);
  color: #fff;
  font-size: 13px;
  border: none;
  cursor: pointer;
  transition: opacity 0.15s;
}
.preview-download:hover {
  opacity: 0.85;
}

.preview-media {
  display: flex;
  align-items: center;
}

.preview-stage {
  position: relative;
  max-width: 70vw;
  max-height: 80vh;
}

.preview-img {
  display: block;
  max-width: 70vw;
  max-height: 80vh;
  border-radius: 8px;
  object-fit: contain;
}

.preview-close {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #fff;
  color: #4a4a4a;
  cursor: pointer;
  border: 1px solid #e3e6ea;
  transition: background 0.15s, border-color 0.15s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  z-index: 101;
}
.preview-close:hover {
  background: #f4f5f7;
  border-color: #d3d8dd;
}

.preview-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  cursor: pointer;
  transition: background 0.15s;
}
.preview-nav:hover {
  background: rgba(0, 0, 0, 0.7);
}
.preview-nav.prev {
  left: 10px;
}
.preview-nav.next {
  right: 10px;
}

.preview-fade-enter-active,
.preview-fade-leave-active {
  transition: opacity 0.2s;
}
.preview-fade-enter-from,
.preview-fade-leave-to {
  opacity: 0;
}

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
  padding-bottom: 180px;
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
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-bottom-left-radius: 4px;
}

.message-bubble.user {
  background: var(--color-accent);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.bubble-text {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.bubble-images {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.result-img {
  max-width: 320px;
  max-height: 320px;
  border-radius: 10px;
  object-fit: cover;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.15s;
}
.result-img:hover {
  transform: scale(1.02);
}

.bubble-time {
  font-size: 11px;
  margin-top: 6px;
  opacity: 0.6;
}

.message-row.user .bubble-time {
  text-align: right;
}

.image-records {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 20px;
}

.image-record-card {
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  overflow: hidden;
  transition: box-shadow 0.15s, transform 0.15s;
}
.image-record-card:hover {
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.image-record-img {
  width: 100%;
  aspect-ratio: 3/4;
  object-fit: cover;
  display: block;
  background: var(--color-bg-page);
}

.image-record-placeholder {
  width: 100%;
  aspect-ratio: 3/4;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-page);
  color: var(--color-text-secondary);
}

.image-record-card.pending {
  border-style: dashed;
}

.placeholder-loading,
.placeholder-failed,
.placeholder-waiting {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.placeholder-failed {
  color: #e74c3c;
}

.spinner {
  width: 26px;
  height: 26px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.image-record-prompt {
  font-size: 13px;
  color: var(--color-text-primary);
  padding: 10px 14px 2px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.image-record-time {
  font-size: 11px;
  color: var(--color-text-secondary);
  padding: 4px 14px 12px;
}

.image-records-empty {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--color-text-secondary);
  padding: 80px 0;
}
.image-records-empty p {
  margin: 0;
  font-size: 13px;
}

.scroll-btn {
  position: absolute;
  bottom: 180px;
  right: 32px;
  width: 36px;
  height: 36px;
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: background 0.15s;
}
.scroll-btn:hover {
  background: var(--color-hover);
}
</style>