<script setup lang="ts">
import { ref } from 'vue'

const title = ref(document.title)
const prompt = ref('')
const response = ref('')
const loading = ref(false)

async function sendMessage() {
  if (!prompt.value.trim() || loading.value) return
  loading.value = true
  response.value = ''

  await new Promise((resolve) => setTimeout(resolve, 1500))

  response.value = `你输入的内容是：「${prompt.value}」\n\n这是一个示例响应，你可以在这里接入实际的 AI 服务。`
  prompt.value = ''
  loading.value = false
}
</script>

<template>
  <section id="center">
    <div class="hero">
      <h1>{{ title }}</h1>
    </div>

    <div class="chat-area">
      <div class="input-group">
        <input
          v-model="prompt"
          type="text"
          placeholder="请输入你的问题..."
          @keyup.enter="sendMessage"
        />
        <button type="button" :disabled="loading || !prompt.trim()" @click="sendMessage">
          {{ loading ? '思考中...' : '发送' }}
        </button>
      </div>

      <div v-if="loading" class="loading">AI 正在思考中...</div>

      <div v-if="response" class="response-card">
        <pre>{{ response }}</pre>
      </div>
    </div>
  </section>
</template>