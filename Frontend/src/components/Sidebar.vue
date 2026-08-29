<script setup lang="ts">
import { ref, computed } from 'vue'

type AssetType = 'image' | 'video' | 'audio'

interface Asset {
  taskId: string
  type: AssetType
  prompt: string
  status: 'pending' | 'running' | 'success' | 'failed'
  progress: number
  files: string[]
  errorMsg: string
  messageId: number
  createTime: string
}

interface UserInfo {
  id: number
  user_id: string
  username: string
  email: string | null
  is_active: boolean
  is_superuser: boolean
}

const props = defineProps<{
  assets: Asset[]
  isLoggedIn: boolean
  currentUser: UserInfo | null
}>()

const emit = defineEmits<{
  login: []
  logout: []
}>()

const navItems = [
  { id: 'new-chat', label: '新对话', icon: 'chat' },
  { id: 'workspace', label: 'AI 工作台', icon: 'monitor' },
  { id: 'skills', label: '技能·连接器·伙伴', icon: 'link' },
  { id: 'api', label: 'API 服务', icon: 'api', hasArrow: true },
  { id: 'more', label: '更多', icon: 'more', hasExpand: true },
]

const activeNav = ref('workspace')
const selectedAsset = ref<Asset | null>(null)

const maxVisible = 5
const visibleAssets = computed(() => props.assets.slice(0, maxVisible))
const hiddenCount = computed(() => Math.max(0, props.assets.length - maxVisible))

function openDetail(asset: Asset) {
  selectedAsset.value = asset
}

function closeDetail() {
  selectedAsset.value = null
}

function statusText(status: string) {
  const map: Record<string, string> = {
    pending: '排队中',
    running: '生成中',
    success: '已完成',
    failed: '失败',
  }
  return map[status] || status
}

function typeLabel(type: AssetType) {
  const map: Record<AssetType, string> = {
    image: '图片',
    video: '视频',
    audio: '语音',
  }
  return map[type]
}

function formatTime(iso: string) {
  if (!iso) return ''
  const date = new Date(iso)
  if (isNaN(date.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <span class="sidebar-title">LeafAI</span>
      <button class="icon-btn" title="搜索">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      </button>
    </div>

    <nav class="sidebar-nav">
      <button
        v-for="item in navItems"
        :key="item.id"
        :class="['nav-item', { active: activeNav === item.id }]"
        @click="activeNav = item.id"
      >
        <svg v-if="item.icon === 'chat'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        <svg v-else-if="item.icon === 'monitor'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
          <line x1="8" y1="21" x2="16" y2="21" />
          <line x1="12" y1="17" x2="12" y2="21" />
        </svg>
        <svg v-else-if="item.icon === 'link'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
        </svg>
        <svg v-else-if="item.icon === 'api'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
        </svg>
        <svg v-else-if="item.icon === 'more'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="1" />
          <circle cx="12" cy="5" r="1" />
          <circle cx="12" cy="19" r="1" />
        </svg>
        <span class="nav-label">{{ item.label }}</span>
        <svg v-if="item.hasArrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="nav-arrow">
          <line x1="5" y1="12" x2="19" y2="12" />
          <polyline points="12 5 19 12 12 19" />
        </svg>
        <svg v-if="item.hasExpand" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="nav-arrow">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
    </nav>

    <div class="sidebar-section">
      <div class="section-title">资产</div>
      <div v-if="assets.length === 0" class="asset-empty">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="asset-icon">
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <polyline points="21 15 16 10 5 21" />
        </svg>
        <span class="asset-text">暂无生成任务</span>
      </div>
      <div v-for="asset in visibleAssets" :key="asset.taskId" class="asset-task" @click="openDetail(asset)">
        <div class="asset-task-header">
          <span :class="['asset-status-dot', asset.status]" />
          <span class="asset-task-type">{{ typeLabel(asset.type) }}</span>
          <span class="asset-task-status-sep">·</span>
          <span class="asset-task-status">{{ statusText(asset.status) }}</span>
          <span class="asset-task-time">{{ formatTime(asset.createTime) }}</span>
        </div>
        <div class="asset-task-prompt">{{ asset.prompt.slice(0, 30) }}{{ asset.prompt.length > 30 ? '...' : '' }}</div>
        
        <div v-if="asset.files.length > 0" class="asset-preview">
          <img v-if="asset.type === 'image'" :src="asset.files[0]" alt="缩略图" class="asset-thumb-img" />
          <div v-else-if="asset.type === 'video'" class="asset-thumb-video">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" class="play-icon">
              <polygon points="8,5 19,12 8,19" />
            </svg>
          </div>
          <div v-else-if="asset.type === 'audio'" class="asset-thumb-audio">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 18V5l12-2v13" />
              <circle cx="6" cy="18" r="3" />
              <circle cx="18" cy="16" r="3" />
            </svg>
          </div>
        </div>
      </div>
      <div v-if="hiddenCount > 0" class="asset-more">+ {{ hiddenCount }} 项更多</div>
    </div>

    <div class="sidebar-footer">
      <button v-if="!isLoggedIn" class="footer-btn full" @click="emit('login')">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
          <polyline points="10 17 15 12 10 7" />
          <line x1="15" y1="12" x2="3" y2="12" />
        </svg>
        <span>登录/注册</span>
      </button>
      <div v-else class="footer-row">
        <div class="footer-user">
          <span class="footer-avatar">{{ (currentUser?.username || 'U')[0].toUpperCase() }}</span>
          <span class="footer-username">{{ currentUser?.username }}</span>
        </div>
        <button class="icon-btn logout-btn" title="退出登录" @click="emit('logout')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
        </button>
      </div>
    </div>
  </aside>

  <Transition name="detail-slide">
    <div v-if="selectedAsset" class="asset-detail-overlay" @click.self="closeDetail">
      <div class="asset-detail-card">
        <div class="detail-header">
          <span class="detail-title">{{ typeLabel(selectedAsset.type) }}详情</span>
          <button class="icon-btn" @click="closeDetail">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div class="detail-body">
          <div class="detail-row">
            <span class="detail-label">状态</span>
            <span :class="['detail-status', selectedAsset.status]">{{ statusText(selectedAsset.status) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">创建时间</span>
            <span class="detail-value">{{ formatTime(selectedAsset.createTime) }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">提示词</span>
            <span class="detail-value">{{ selectedAsset.prompt }}</span>
          </div>
          
          <div v-if="selectedAsset.errorMsg" class="detail-row">
            <span class="detail-label">错误</span>
            <span class="detail-value detail-error">{{ selectedAsset.errorMsg }}</span>
          </div>

          <div v-if="selectedAsset.files.length > 0" class="detail-files">
            <div class="detail-label">生成结果</div>
            <img v-if="selectedAsset.type === 'image'" v-for="(url, i) in selectedAsset.files" :key="'img-' + i" :src="url" class="detail-img" />
            <video v-else-if="selectedAsset.type === 'video'" v-for="(url, i) in selectedAsset.files" :key="'vid-' + i" :src="url" controls class="detail-video" />
            <audio v-else-if="selectedAsset.type === 'audio'" v-for="(url, i) in selectedAsset.files" :key="'aud-' + i" :src="url" controls class="detail-audio" />
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  background: var(--color-bg-white);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
}

.sidebar.overlay {
  position: absolute;
  left: 0;
  top: 0;
  z-index: 100;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.15);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 12px;
}

.sidebar-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: var(--color-text-secondary);
  transition: background 0.15s;
}
.icon-btn:hover {
  background: var(--color-hover);
}

.sidebar-nav {
  padding: 4px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  color: var(--color-text-primary);
  transition: background 0.15s;
  text-align: left;
}
.nav-item:hover {
  background: var(--color-hover);
}
.nav-item.active {
  background: var(--color-hover);
  font-weight: 500;
}

.nav-label {
  flex: 1;
}

.nav-arrow {
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.sidebar-section {
  flex: 1;
  overflow-y: auto;
  padding: 16px 16px 0;
  padding-bottom: 8px;
}
.sidebar-section::-webkit-scrollbar,
.detail-body::-webkit-scrollbar {
  display: none;
}
.sidebar-section,
.detail-body {
  scrollbar-width: none;
}

.section-title {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
  padding: 0 4px;
}

.asset-empty {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.asset-icon {
  flex-shrink: 0;
  color: var(--color-text-secondary);
}

.asset-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.asset-task {
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--color-bg-page);
  margin-bottom: 6px;
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: background 0.15s;
}
.asset-task:hover {
  background: var(--color-hover);
}

.asset-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.asset-status-dot.pending { background: #F59E0B; }
.asset-status-dot.running { background: #3B82F6; animation: pulse 1.5s infinite; }
.asset-status-dot.success { background: #10B981; }
.asset-status-dot.failed { background: #EF4444; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.asset-task-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.asset-task-time {
  margin-left: auto;
  font-size: 11px;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.asset-task-status-sep {
  font-size: 10px;
  color: var(--color-text-secondary);
}

.asset-task-type {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-accent);
}

.asset-task-status {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.asset-task-prompt {
  font-size: 11px;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.asset-progress {
  display: flex;
  align-items: center;
  gap: 6px;
}

.asset-progress-bar {
  flex: 1;
  height: 4px;
  background: #E5E7EB;
  border-radius: 2px;
  overflow: hidden;
}

.asset-progress-fill {
  height: 100%;
  background: var(--color-accent);
  border-radius: 2px;
  transition: width 0.5s ease;
}

.asset-progress-text {
  font-size: 10px;
  color: var(--color-text-secondary);
  min-width: 28px;
  text-align: right;
}

.asset-preview {
  margin-top: 6px;
}

.asset-thumb-img {
  width: 100%;
  max-height: 80px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid var(--color-border);
}

.asset-thumb-video {
  width: 100%;
  height: 56px;
  background: #1f2937;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
}

.asset-thumb-video .play-icon {
  color: #fff;
  opacity: 0.8;
}

.asset-more {
  font-size: 12px;
  color: var(--color-text-secondary);
  text-align: center;
  padding: 6px 0;
}

.asset-thumb-audio {
  width: 100%;
  height: 44px;
  background: #f3f4f6;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  color: #6b7280;
}

.sidebar-footer {
  flex-shrink: 0;
  padding: 8px 16px;
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-white);
}

.footer-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.footer-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  color: var(--color-text-primary);
  transition: background 0.15s;
}
.footer-btn:hover {
  background: var(--color-hover);
}
.footer-btn.full {
  width: 100%;
}

.footer-user {
  display: flex;
  align-items: center;
  gap: 10px;
}

.footer-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-accent);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.footer-username {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout-btn {
  flex-shrink: 0;
}

/* 资产详情卡片 */
.asset-detail-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  justify-content: flex-end;
  background: rgba(0, 0, 0, 0.2);
}

.asset-detail-card {
  width: 380px;
  max-width: 90vw;
  height: 100vh;
  background: var(--color-bg-white);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}

.detail-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.detail-value {
  font-size: 14px;
  color: var(--color-text-primary);
  line-height: 1.5;
  word-break: break-all;
}

.detail-error {
  color: #EF4444;
}

.detail-status {
  font-size: 13px;
  font-weight: 500;
}
.detail-status.pending { color: #F59E0B; }
.detail-status.running { color: #3B82F6; }
.detail-status.success { color: #10B981; }
.detail-status.failed { color: #EF4444; }

.detail-progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-progress .asset-progress-bar {
  flex: 1;
  height: 6px;
  background: #E5E7EB;
  border-radius: 3px;
  overflow: hidden;
}

.detail-progress .asset-progress-fill {
  height: 100%;
  background: var(--color-accent);
  border-radius: 3px;
  transition: width 0.5s ease;
}

.detail-progress .asset-progress-text {
  font-size: 12px;
  color: var(--color-text-secondary);
  min-width: 32px;
  text-align: right;
}

.detail-files {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-img {
  width: 100%;
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.detail-video {
  width: 100%;
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.detail-audio {
  width: 100%;
}

/* 右滑动画 */
.detail-slide-enter-active,
.detail-slide-leave-active {
  transition: all 0.25s ease;
}
.detail-slide-enter-active .asset-detail-card,
.detail-slide-leave-active .asset-detail-card {
  transition: transform 0.25s ease;
}

.detail-slide-enter-from,
.detail-slide-leave-to {
  background: transparent;
}
.detail-slide-enter-from .asset-detail-card,
.detail-slide-leave-to .asset-detail-card {
  transform: translateX(100%);
}
</style>