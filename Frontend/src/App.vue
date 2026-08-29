<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import MainContent from './components/MainContent.vue'
import InputBar from './components/InputBar.vue'
import AuthOverlay from './components/AuthOverlay.vue'
import { api, type ResolutionConfig } from './api/index'

const BREAKPOINT = 800
const sidebarVisible = ref(true)
const isMobile = ref(false)
const activeMode = ref<'chat' | 'image'>('chat')

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
}

const assets = ref<Asset[]>([])
let msgIdCounter = ref(4)

const resolutionConfig = ref<ResolutionConfig[]>([])

interface UserInfo {
  id: number
  user_id: string
  username: string
  email: string | null
  is_active: boolean
  is_superuser: boolean
}

const isLoggedIn = ref(false)
const currentUser = ref<UserInfo | null>(null)
const showAuth = ref(false)
const inputCollapsed = ref(false)
const chatSessionId = ref<string | null>(null)

function genId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return 'xxxxxxxxxxxx4xxxyxxxxxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

function checkMobile() {
  isMobile.value = window.innerWidth < BREAKPOINT
  if (isMobile.value) sidebarVisible.value = false
}

function toggleSidebar() {
  sidebarVisible.value = !sidebarVisible.value
}

function closeSidebar() {
  sidebarVisible.value = false
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
}) {
  if (!isLoggedIn.value) {
    showAuth.value = true
    return
  }
  const nowIso = new Date().toISOString()
  let task: Asset
  try {
    const res = await api.generateImage({
      model_id: 1,
      prompt: params.prompt,
      resolution: params.resolution,
      aspect_ratio: params.aspectRatio,
      quality: params.quality,
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
    }
    assets.value.push(task)
    sortAssets()
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
  }
}

async function handleLogin(username: string, password: string) {
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
    }
    isLoggedIn.value = true
  }
  showAuth.value = false
  await loadAssets()
  await loadChatHistory()
}

async function handleRegister(username: string, password: string, email?: string) {
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
    }
    isLoggedIn.value = true
  }
  showAuth.value = false
  await loadAssets()
}

function handleLogout() {
  localStorage.removeItem('leafai_token')
  isLoggedIn.value = false
  currentUser.value = null
  showAuth.value = false
  assets.value = []
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
    const sessions = res.data?.sessions || []
    if (sessions.length === 0) return
    const latest = sessions[0]
    chatSessionId.value = latest.id
    const msgs = await api.getChatSessionMessages(latest.id)
    const list = (msgs.data || [])
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
    const tasks = res.data?.tasks || []
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
    }))
)

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)

  await restoreSession()

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
})
</script>

<template>
  <AuthOverlay
    v-if="showAuth"
    @login="handleLogin"
    @register="handleRegister"
    @close="showAuth = false"
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
    :class="{ overlay: isMobile }"
    :assets="assets"
    :is-logged-in="isLoggedIn"
    :current-user="currentUser"
    @login="showAuth = true"
    @logout="handleLogout"
  />

  <MainContent
    :sidebar-visible="sidebarVisible"
    :mode="activeMode"
    :messages="messages"
    :image-records="imageRecords"
    @toggle-sidebar="toggleSidebar"
    @collapse-input="inputCollapsed = true"
    @expand-input="inputCollapsed = false"
  />

  <InputBar
    :style="{
      left: isMobile ? '0' : sidebarVisible ? 'var(--sidebar-width)' : '0',
    }"
    :active-mode="activeMode"
    :resolution-config="resolutionConfig"
    :collapsed="inputCollapsed"
    @send="handleSend"
    @mode-change="handleModeChange"
    @image-generate="handleImageGenerate"
    @expand="inputCollapsed = false"
  />
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
</style>