<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import MainContent from './components/MainContent.vue'
import InputBar from './components/InputBar.vue'
import AuthOverlay from './components/AuthOverlay.vue'
import AdminLayout from './components/AdminLayout.vue'
import { api, type ResolutionConfig } from './api/index'
import ApiDocs from './components/ApiDocs.vue'
import MyRecordView from './components/MyRecordView.vue'

const BREAKPOINT = 800
const SIDEBAR_WIDTH = 260
const SIDEBAR_COLLAPSED_WIDTH = 64
// 侧边栏状态：full(260) → collapsed(64) → hidden(完全隐藏)，由顶栏按钮循环切换
type SidebarState = 'full' | 'collapsed' | 'hidden'
const sidebarState = ref<SidebarState>('full')
const isMobile = ref(false)
const activeMode = ref<'chat' | 'image'>('chat')

// 主视图：默认显示原工作台（MainContent + InputBar）；docs 为 API 文档，
// my-points / my-recharges 为「更多」里的积分/充值记录
type View = 'chat' | 'image' | 'docs' | 'my-points' | 'my-recharges'
const view = ref<View>('chat')

// 「重做」：将历史图片记录的完整参数回填到输入框
const inputBarRef = ref<{
  applyRedo: (p: {
    prompt?: string
    modelId?: number
    quality?: string
    resolution?: string
    refImages?: string[]
  }) => void
} | null>(null)
function handleRedo(rec: {
  prompt?: string
  modelId?: number
  quality?: string
  resolution?: string
  refImages?: string[]
}) {
  view.value = 'chat'
  activeMode.value = 'image'
  inputBarRef.value?.applyRedo(rec)
}

function onNavigate(navId: string) {
  if (navId === 'new-chat') {
    view.value = inputEnabledModes.value.includes('chat') ? 'chat' : 'image'
    activeMode.value = 'chat'
  } else if (navId === 'workspace') {
    // 「AI工作台」默认展示对话工作台
    view.value = 'chat'
  } else if (navId === 'skills') {
    showToast('技能·连接器·伙伴 暂未开放', 'info')
  } else if (navId === 'api') {
    view.value = 'docs'
  } else if (navId === 'my-points' || navId === 'my-recharges') {
    view.value = navId
  }
}

// 当前用户可用的功能：来自 C 端 /config/features（总开关+白名单）
const enabledFeatures = ref<Set<string>>(new Set())
const chatEnabled = computed(() => enabledFeatures.value.has('chat'))
const imageEnabled = computed(() => enabledFeatures.value.has('image_generate'))
const inputEnabledModes = computed(() => {
  const set: ('chat' | 'image')[] = []
  if (chatEnabled.value) set.push('chat')
  if (imageEnabled.value) set.push('image')
  return set
})

// 功能开关变化后，确保 activeMode 落在可用范围
watch([chatEnabled, imageEnabled], () => {
  const available = inputEnabledModes.value
  if (available.includes(activeMode.value)) return
  activeMode.value = available[0] ?? 'chat'
})

const sidebarVisible = computed(() => sidebarState.value !== 'hidden')
const sidebarCollapsed = computed(() => (isMobile.value ? false : sidebarState.value === 'collapsed'))

interface Message {
  id: number
  role: 'system' | 'user' | 'assistant'
  content: string
  time: string
  images?: string[]
}

const chatModelId = ref<number | null>(null)

const messages = ref<Message[]>([
  {
    id: 1,
    role: 'system',
    content: '欢迎使用 LeafAI 智能工作台！我是你的 AI 助手，可以帮助你完成文档生成、数据分析、代码编写、图片生成等任务。请随时告诉我你需要什么。',
    time: '刚刚',
  },
])

interface Asset {
  taskId: string
  type: 'image' | 'video' | 'audio'
  prompt: string
  status: 'pending' | 'running' | 'success' | 'failed'
  progress: number
  files: string[]
  errorMsg: string
  messageId: number
  createTime: string
  // 重做用：记录该次图片生成的完整参数，便于一键回填
  modelId?: number
  quality?: string
  resolution?: string
  refImages?: string[]
}

const assets = ref<Asset[]>([])
let msgIdCounter = ref(4)

const resolutionConfig = ref<ResolutionConfig[]>([])
const imageModels = ref<Array<{ id: number; label: string; promptMaxLength: number }>>([])

interface UserInfo {
  id: number
  user_id: string
  username: string
  email: string | null
  is_active: boolean
  is_superuser: boolean
  role: string
  points_balance: number
  free_quota: Record<string, number>
}

const isLoggedIn = ref(false)
const currentUser = ref<UserInfo | null>(null)
const showAuth = ref(false)
const showAdmin = ref(false)
const inputCollapsed = ref(false)
const chatSessionId = ref<string | null>(null)
const toast = ref<{ type: 'success' | 'error' | 'info'; text: string } | null>(null)
let toastTimer: ReturnType<typeof setTimeout> | null = null

function showToast(text: string, type: 'success' | 'error' | 'info' = 'info') {
  toast.value = { type, text }
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    toast.value = null
  }, 3500)
}

function genId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return 'xxxxxxxxxxxx4xxxyxxxxxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

function checkMobile() {
  const mobile = window.innerWidth < BREAKPOINT
  if (mobile !== isMobile.value) {
    isMobile.value = mobile
    // 跨断点时同步状态：进入窄屏关闭覆盖层，回到宽屏恢复完整
    sidebarState.value = mobile ? 'hidden' : 'full'
  }
}

function toggleSidebar() {
  // 顶栏按钮：桌面端循环 full → collapsed → hidden → full；移动端仅 show/hide 覆盖层
  if (isMobile.value) {
    sidebarState.value = sidebarState.value === 'hidden' ? 'full' : 'hidden'
    return
  }
  if (sidebarState.value === 'full') sidebarState.value = 'collapsed'
  else if (sidebarState.value === 'collapsed') sidebarState.value = 'hidden'
  else sidebarState.value = 'full'
}

// InputBar 的左侧偏移：仅桌面端且侧边栏可见时按其宽度取值
const sidebarOffset = computed(() => {
  if (isMobile.value || !sidebarVisible.value) return 0
  return sidebarCollapsed.value ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH
})

function closeSidebar() {
  sidebarState.value = 'hidden'
}

function openAdmin() {
  if (currentUser.value?.is_superuser) showAdmin.value = true
}

function closeAdmin() {
  showAdmin.value = false
}

async function handleSend(text: string) {
  if (!isLoggedIn.value) {
    showAuth.value = true
    return
  }
  if (!chatModelId.value) {
    await loadChatModel()
    if (!chatModelId.value) {
      messages.value.push({
        id: msgIdCounter.value++,
        role: 'system',
        content: '暂无可用的对话模型，请先在后端启用 DeepSeek 模型',
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      })
      return
    }
  }

  if (!chatSessionId.value) {
    chatSessionId.value = genId()
  }

  const now = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  messages.value.push({
    id: msgIdCounter.value++,
    role: 'user',
    content: text,
    time: now,
  })

  const history = messages.value
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .map((m) => ({ role: m.role, content: m.content }))

  const sysMsgId = msgIdCounter.value++
  messages.value.push({ id: sysMsgId, role: 'assistant', content: '', time: now })

  try {
    await api.chatCompletionStream(
      { model_id: chatModelId.value!, messages: history, session_id: chatSessionId.value },
      (content) => {
        const sysMsg = messages.value.find((m) => m.id === sysMsgId)
        if (sysMsg) sysMsg.content += content
      }
    )
  } catch (e: any) {
    const sysMsg = messages.value.find((m) => m.id === sysMsgId)
    if (sysMsg) sysMsg.content = `请求失败: ${e.message || '未知错误'}`
  }
}

async function loadChatModel() {
  try {
    const res = await api.getModels('chat')
    const items = res.data?.items || []
    const model = items.find((m: any) => m.is_enabled) || items[0]
    chatModelId.value = model ? model.id : null
  } catch {
    chatModelId.value = null
  }
}

async function handleImageGenerate(params: {
  prompt: string
  resolution: string
  aspectRatio: string
  quality: string
  modelId?: number | string
  images?: string[]
}) {
  if (!isLoggedIn.value) {
    showAuth.value = true
    return
  }
  const nowIso = new Date().toISOString()
  let task: Asset
  try {
    // 图片模型：优先使用用户所选，缺省回退到已加载列表中的首个
    let mid: number
    if (typeof params.modelId === 'number') {
      mid = params.modelId
    } else {
      mid = imageModels.value[0]?.id ?? 1
    }
    const res = await api.generateImage({
      model_id: mid,
      prompt: params.prompt,
      resolution: params.resolution,
      aspect_ratio: params.aspectRatio,
      quality: params.quality,
      image: params.images && params.images.length ? params.images : undefined,
    })

    const taskId = res.data.task_id
    task = {
      taskId,
      type: 'image',
      prompt: params.prompt,
      status: 'pending',
      progress: 0,
      files: [],
      errorMsg: '',
      messageId: 0,
      createTime: nowIso,
      modelId: mid,
      quality: params.quality,
      resolution: params.resolution,
      refImages: params.images && params.images.length ? [...params.images] : [],
    }
    assets.value.push(task)
    sortAssets()

    pollTask(taskId)
  } catch (e: any) {
    // 提交失败也作为一条图片记录展示，方便看到错误
    task = {
      taskId: genId(),
      type: 'image',
      prompt: params.prompt,
      status: 'failed',
      progress: 0,
      files: [],
      errorMsg: e.message || '未知错误',
      messageId: 0,
      createTime: nowIso,
      modelId: imageModels.value[0]?.id ?? 1,
      quality: params.quality,
      resolution: params.resolution,
      refImages: params.images && params.images.length ? [...params.images] : [],
    }
    assets.value.push(task)
    sortAssets()
    if (e.message && e.message.includes('积分不足')) {
      showToast(e.message, 'error')
    }
  }
}

function pollTask(taskId: string) {
  const check = async (timer: ReturnType<typeof setInterval>) => {
    let data: any
    try {
      const res = await api.getTaskStatus(taskId)
      data = res.data
    } catch {
      return
    }

    // 通过任务ID从响应式 assets 中取回 reactive 代理，直接改引用对象不会触发视图更新
    const asset = assets.value.find((a) => a.taskId === taskId)
    if (!asset) {
      clearInterval(timer)
      return
    }
    asset.status = data.status as Asset['status']
    asset.progress = (data.result || {}).progress || 0
    asset.errorMsg = data.error_msg || ''

    const sysMsg = messages.value.find((m) => m.id === asset.messageId)
    if (sysMsg) {
      if (asset.status === 'pending') {
        sysMsg.content = '任务已提交，正在排队...'
      } else if (asset.status === 'running') {
        sysMsg.content = '正在生成图片...'
      }
    }

    if (asset.status === 'success') {
      clearInterval(timer)
      // 消耗积分/免费次数后刷新余额，保持「余额」提示准确
      refreshCurrentUser()
      const images = (data.result || {}).images || []
      asset.files = images
      if (sysMsg) {
        sysMsg.content = '图片生成完成'
        sysMsg.images = images
      }
    } else if (asset.status === 'failed') {
      clearInterval(timer)
      if (sysMsg) {
        sysMsg.content = `生成失败: ${asset.errorMsg || '未知错误'}`
      }
    }
  }

  const timer = setInterval(() => check(timer), 1500)
}

function handleModeChange(mode: string) {
  if (mode === 'chat' || mode === 'image') {
    activeMode.value = mode
    view.value = mode
  }
}

async function handleLogin(username: string, password: string) {
  try {
    const res = await api.login(username, password)
    localStorage.setItem('leafai_token', res.data.access_token)
    try {
      const me = await api.getMe()
      currentUser.value = me.data
      isLoggedIn.value = true
    } catch {
      currentUser.value = {
        id: 0,
        user_id: res.data.user_id,
        username: res.data.username,
        email: null,
        is_active: true,
        is_superuser: false,
        role: 'user',
        points_balance: 0,
        free_quota: {},
      }
      isLoggedIn.value = true
    }
    showAuth.value = false
    await loadFeatures()
    await loadAssets()
    await loadImageModels()
    await loadChatHistory()
  } catch (e: any) {
    showToast(e.message || '登录失败', 'error')
  }
}

async function handleRegister(username: string, password: string, email?: string) {
  try {
    const res = await api.register(username, password, email)
    localStorage.setItem('leafai_token', res.data.access_token)
    try {
      const me = await api.getMe()
      currentUser.value = me.data
      isLoggedIn.value = true
    } catch {
      currentUser.value = {
        id: 0,
        user_id: res.data.user_id,
        username: res.data.username,
        email: null,
        is_active: true,
        is_superuser: false,
        role: 'user',
        points_balance: 0,
        free_quota: {},
      }
      isLoggedIn.value = true
    }
    showAuth.value = false
    await loadFeatures()
    await loadAssets()
    await loadImageModels()
    await loadChatHistory()
  } catch (e: any) {
    showToast(e.message || '注册失败', 'error')
  }
}

async function loadFeatures() {
  if (!isLoggedIn.value) {
    enabledFeatures.value = new Set()
    return
  }
  try {
    const res = await api.getFeatures()
    enabledFeatures.value = new Set(res.data?.items || [])
  } catch {
    // 接口失败时保持全量可用，避免误隐藏
    enabledFeatures.value = new Set(['chat', 'image_generate'])
  }
}

// 拉取最新用户信息（余额/免费配额），用于消耗积分后的实时刷新
async function refreshCurrentUser() {
  if (!isLoggedIn.value) return
  try {
    const me = await api.getMe()
    currentUser.value = me.data as UserInfo
  } catch {
    // ignore
  }
}

async function loadImageModels() {
  try {
    const res = await api.getModels('image')
    const items = res.data?.items || []
    imageModels.value = items
      .filter((m: any) => m.is_enabled)
      .map((m: any) => ({
        id: m.id,
        label: m.display_name || m.model_name,
        promptMaxLength: m.prompt_max_length || 5000,
      }))
  } catch {
    imageModels.value = []
  }
}

function handleLogout() {
  localStorage.removeItem('leafai_token')
  isLoggedIn.value = false
  currentUser.value = null
  showAuth.value = false
  assets.value = []
  imageModels.value = []
  chatSessionId.value = null
  messages.value = [{
    id: 1,
    role: 'system',
    content: '欢迎使用 LeafAI 智能工作台！我是你的 AI 助手，可以帮助你完成文档生成、数据分析、代码编写、图片生成等任务。请随时告诉我你需要什么。',
    time: '刚刚',
  }]
}

async function restoreSession() {
  const token = localStorage.getItem('leafai_token')
  if (!token) return
  try {
    const res = await api.getMe()
    currentUser.value = res.data
    isLoggedIn.value = true
    await loadAssets()
    await loadImageModels()
    await loadChatHistory()
  } catch {
    localStorage.removeItem('leafai_token')
  }
}

function formatMsgTime(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  return `${d.getMonth() + 1}-${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// 登录后恢复最近一次会话记录
async function loadChatHistory() {
  try {
    const res = await api.listChatSessions()
    const sessions = res.data?.items || []
    if (sessions.length === 0) return
    const latest = sessions[0]
    chatSessionId.value = latest.id
    const msgs = await api.getChatSessionMessages(latest.id)
    const list = (msgs.data?.items || [])
      .filter((m: any) => m.role === 'user' || m.role === 'assistant')
      .map((m: any) => ({
        id: msgIdCounter.value++,
        role: m.role as Message['role'],
        content: m.content,
        time: formatMsgTime(m.create_time),
      }))
    if (list.length) {
      messages.value = list
    }
  } catch {
    // ignore
  }
}

async function loadAssets() {
  try {
    const res = await api.listTasks({ page_size: 50 })
    const tasks = res.data?.items || []
    assets.value = tasks.map((t: any) => {
      const category = t.category || ''
      let type: Asset['type'] = 'image'
      if (category.includes('video')) type = 'video'
      else if (category.includes('audio')) type = 'audio'

      return {
        taskId: t.task_id,
        type,
        prompt: t.input_params?.prompt || '',
        status: t.status as Asset['status'],
        progress: (t.result || {}).progress || 0,
        files: (t.result || {}).images || (t.result || {}).files || [],
        errorMsg: t.error_msg || '',
        messageId: 0,
        createTime: t.create_time || '',
        modelId: t.input_params?.model_id ?? undefined,
        quality: t.input_params?.quality || undefined,
        resolution: t.input_params?.resolution || undefined,
        refImages: Array.isArray(t.input_params?.image) ? t.input_params.image : undefined,
      }
    })
    sortAssets()
  } catch {
    // ignore
  }
}

// 按创建时间倒序排列（最新在前），新发送任务无需刷新即可置顶
function sortAssets() {
  assets.value.sort(
    (a, b) => new Date(b.createTime).getTime() - new Date(a.createTime).getTime()
  )
}

// 图片记录：与对话记录分离，包含所有图片生成任务（进行中/失败以占位展示）
const imageRecords = computed(() =>
  assets.value
    .filter((a) => a.type === 'image')
    .map((a) => ({
      taskId: a.taskId,
      prompt: a.prompt,
      images: a.files,
      status: a.status,
      errorMsg: a.errorMsg,
      time: formatMsgTime(a.createTime),
      modelId: a.modelId,
      quality: a.quality,
      resolution: a.resolution,
      refImages: a.refImages,
    }))
)

function onWindowFocus() {
  // 切回页面时刷新余额/免费配额，后台管理充值后切回即同步
  refreshCurrentUser()
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  window.addEventListener('focus', onWindowFocus)
  document.addEventListener('visibilitychange', onWindowFocus)

  await restoreSession()
  await loadFeatures()

  try {
    const res = await api.getResolutions()
    const ratios = res.data?.aspect_ratios || []
    resolutionConfig.value = ratios
  } catch {
    // ignore
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
  window.removeEventListener('focus', onWindowFocus)
  document.removeEventListener('visibilitychange', onWindowFocus)
})
</script>

<template>
  <AuthOverlay
    v-if="showAuth"
    @login="handleLogin"
    @register="handleRegister"
    @close="showAuth = false"
  />

  <AdminLayout
    v-if="showAdmin"
    :username="currentUser?.username || ''"
    @exit="closeAdmin"
  />

  <Transition name="overlay-fade">
    <div
      v-if="isMobile && sidebarVisible"
      class="sidebar-overlay"
      @click="closeSidebar"
    />
  </Transition>

  <Sidebar
    v-show="sidebarVisible"
    :class="{ overlay: isMobile, collapsed: sidebarCollapsed }"
    :assets="assets"
    :is-logged-in="isLoggedIn"
    :current-user="currentUser"
    :enabled-features="enabledFeatures"
    :collapsed="sidebarCollapsed"
    :current-view="view"
    @login="showAuth = true"
    @logout="handleLogout"
    @admin="openAdmin"
    @navigate="onNavigate"
  />

  <MainContent
    v-if="view === 'chat' || view === 'image'"
    :sidebar-visible="sidebarVisible"
    :mode="activeMode"
    :messages="messages"
    :image-records="imageRecords"
    @toggle-sidebar="toggleSidebar"
    @collapse-input="inputCollapsed = true"
    @expand-input="inputCollapsed = false"
    @redo="handleRedo"
    @toast="showToast"
  />

  <ApiDocs v-else-if="view === 'docs'" />
  <MyRecordView v-else-if="view === 'my-points'" title="积分消耗记录" direction="out" empty-text="暂无积分消耗记录" />
  <MyRecordView v-else-if="view === 'my-recharges'" title="充值记录" direction="in" empty-text="暂无充值记录" />

  <InputBar
    ref="inputBarRef"
    v-if="view === 'chat' || view === 'image'"
    :style="{
      left: sidebarOffset + 'px',
    }"
    :active-mode="activeMode"
    :enabled-features="enabledFeatures"
    :resolution-config="resolutionConfig"
    :image-models="imageModels"
    :free-quota-image="currentUser?.free_quota?.image ?? 0"
    :points-balance="currentUser?.points_balance ?? 0"
    :collapsed="inputCollapsed"
    @send="handleSend"
    @mode-change="handleModeChange"
    @image-generate="handleImageGenerate"
    @expand="inputCollapsed = false"
  />

  <Transition name="toast">
    <div v-if="toast" class="app-toast" :class="toast.type">{{ toast.text }}</div>
  </Transition>
</template>

<style scoped>
.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 90;
}

.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: opacity 0.2s;
}
.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}

.app-toast {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 3000;
  max-width: 80vw;
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 14px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  color: #fff;
  background: #1f2937;
}
.app-toast.error {
  background: #dc2626;
}
.app-toast.success {
  background: #059669;
}
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.25s, transform 0.25s;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-8px);
}
</style>