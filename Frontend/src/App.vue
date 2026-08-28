<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import MainContent from './components/MainContent.vue'
import InputBar from './components/InputBar.vue'

const BREAKPOINT = 800
const sidebarVisible = ref(true)
const isMobile = ref(false)

function checkMobile() {
  isMobile.value = window.innerWidth < BREAKPOINT
  if (isMobile.value) {
    sidebarVisible.value = false
  }
}

function toggleSidebar() {
  sidebarVisible.value = !sidebarVisible.value
}

function closeSidebar() {
  sidebarVisible.value = false
}

function handleSend(message: string) {
  console.log('发送消息:', message)
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<template>
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
  />

  <MainContent
    :sidebar-visible="sidebarVisible"
    @toggle-sidebar="toggleSidebar"
  />

  <InputBar
    :style="{
      left: isMobile ? '0' : sidebarVisible ? 'var(--sidebar-width)' : '0',
    }"
    @send="handleSend"
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