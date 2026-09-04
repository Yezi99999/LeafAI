<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  login: [username: string, password: string]
  register: [username: string, password: string, email?: string]
  close: []
}>()

const isRegister = ref(false)
const username = ref('')
const password = ref('')
const email = ref('')
const error = ref('')
const loading = ref(false)
// 记录本次鼠标按下是否发生在弹窗外部（遮罩层）上，用于区分「点击外部关闭」与「拖动选择误触」
const pressOutside = ref(false)

function onOverlayPointerDown() {
  pressOutside.value = true
}

function onOverlayClick() {
  // 仅当按下起点在遮罩层上才视为「点击外部关闭」；
  // 从框内拖动到框外松开的 click 不影响关闭，避免拖动选择文本时误关弹窗
  if (pressOutside.value) {
    emit('close')
  }
  pressOutside.value = false
}

async function handleSubmit() {
  error.value = ''
  if (!username.value.trim() || !password.value.trim()) {
    error.value = '请填写用户名和密码'
    return
  }
  if (password.value.length < 6) {
    error.value = '密码至少6位'
    return
  }
  loading.value = true
  try {
    if (isRegister.value) {
      emit('register', username.value.trim(), password.value, email.value.trim() || undefined)
    } else {
      emit('login', username.value.trim(), password.value)
    }
  } catch (e: any) {
    error.value = e.message || '请求失败'
  } finally {
    loading.value = false
  }
}

function toggleMode() {
  isRegister.value = !isRegister.value
  error.value = ''
}
</script>

<template>
  <div
    class="auth-overlay"
    @pointerdown.self="onOverlayPointerDown"
    @click="onOverlayClick"
  >
    <div class="auth-card" @pointerdown="pressOutside = false">
      <div class="auth-header">
        <h2 class="auth-title">{{ isRegister ? '注册' : '登录' }}</h2>
        <p class="auth-subtitle">
          {{ isRegister ? '创建新账户以使用 LeafAI' : '登录以使用 LeafAI 智能工作台' }}
        </p>
        <button class="auth-close" @click="emit('close')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <div class="auth-body">
        <div v-if="error" class="auth-error">{{ error }}</div>

        <label class="auth-label">用户名</label>
        <input
          v-model="username"
          type="text"
          class="auth-input"
          placeholder="请输入用户名"
          @keyup.enter="handleSubmit"
        />

        <label v-if="isRegister" class="auth-label">邮箱（选填）</label>
        <input
          v-if="isRegister"
          v-model="email"
          type="email"
          class="auth-input"
          placeholder="请输入邮箱"
          @keyup.enter="handleSubmit"
        />

        <label class="auth-label">密码</label>
        <input
          v-model="password"
          type="password"
          class="auth-input"
          placeholder="请输入密码"
          @keyup.enter="handleSubmit"
        />

        <button class="auth-submit" :disabled="loading" @click="handleSubmit">
          {{ loading ? '请稍候...' : (isRegister ? '注册' : '登录') }}
        </button>

        <div class="auth-toggle">
          {{ isRegister ? '已有账户？' : '没有账户？' }}
          <button class="auth-toggle-btn" @click="toggleMode">
            {{ isRegister ? '去登录' : '去注册' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.auth-card {
  width: 400px;
  max-width: 90vw;
  background: var(--color-bg-white);
  border-radius: 16px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.auth-header {
  position: relative;
  padding: 28px 28px 0;
}

.auth-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.auth-subtitle {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.auth-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: var(--color-text-secondary);
  transition: background 0.15s;
}
.auth-close:hover {
  background: var(--color-hover);
}

.auth-body {
  padding: 20px 28px 28px;
}

.auth-error {
  font-size: 13px;
  color: #EF4444;
  background: #FEF2F2;
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.auth-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 6px;
  margin-top: 12px;
}
.auth-label:first-of-type {
  margin-top: 0;
}

.auth-input {
  width: 100%;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  outline: none;
  transition: border-color 0.15s;
}
.auth-input:focus {
  border-color: var(--color-accent);
}
.auth-input::placeholder {
  color: var(--color-text-secondary);
}

.auth-submit {
  width: 100%;
  margin-top: 20px;
  padding: 11px 0;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  background: var(--color-accent);
  border-radius: 10px;
  transition: opacity 0.15s;
}
.auth-submit:hover {
  opacity: 0.9;
}
.auth-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-toggle {
  margin-top: 16px;
  text-align: center;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.auth-toggle-btn {
  color: var(--color-accent);
  font-weight: 500;
  margin-left: 4px;
}
.auth-toggle-btn:hover {
  text-decoration: underline;
}
</style>