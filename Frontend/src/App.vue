<script setup lang="ts">
import { ref } from 'vue'
import Sidebar from './components/Sidebar.vue'
import MainContent from './components/MainContent.vue'
import InputBar from './components/InputBar.vue'

const sidebarVisible = ref(true)

function toggleSidebar() {
  sidebarVisible.value = !sidebarVisible.value
}

function handleSend(message: string) {
  console.log('发送消息:', message)
}
</script>

<template>
  <Sidebar v-show="sidebarVisible" />
  <MainContent
    :sidebar-visible="sidebarVisible"
    @toggle-sidebar="toggleSidebar"
  />
  <InputBar
    :style="{ left: sidebarVisible ? 'var(--sidebar-width)' : '0' }"
    @send="handleSend"
  />
</template>