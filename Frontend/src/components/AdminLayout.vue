<script setup lang="ts">
import { ref } from 'vue'
import UserManage from './UserManage.vue'
import ModelManage from './ModelManage.vue'
import FeatureManage from './FeatureManage.vue'
import PointsManage from './PointsManage.vue'
import NotifyManage from './NotifyManage.vue'
import Dashboard from './Dashboard.vue'
import AuditManage from './AuditManage.vue'
import ApiConfig from './ApiConfig.vue'
import CallRecordsManage from './CallRecordsManage.vue'

const props = defineProps<{
  username: string
}>()

const emit = defineEmits<{
  exit: []
}>()

type ViewKey = 'dashboard' | 'users' | 'models' | 'features' | 'points' | 'notify' | 'records' | 'audit' | 'config'
const activeView = ref<ViewKey>('dashboard')

const navItems: Array<{ id: ViewKey; label: string }> = [
  { id: 'dashboard', label: '仪表盘' },
  { id: 'users', label: '用户管理' },
  { id: 'records', label: '调用记录' },
  { id: 'models', label: '模型管理' },
  { id: 'features', label: '功能开关' },
  { id: 'points', label: '积分管理' },
  { id: 'notify', label: '通知管理' },
  { id: 'audit', label: '操作审计' },
  { id: 'config', label: '接入文档' },
]
</script>

<template>
  <div class="admin-shell">
    <aside class="admin-sidebar">
      <div class="admin-brand">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
        <span>LeafAI 管理平台</span>
      </div>
      <nav class="admin-nav">
        <button
          v-for="item in navItems"
          :key="item.id"
          class="admin-nav-item"
          :class="{ active: activeView === item.id }"
          @click="activeView = item.id"
        >
          {{ item.label }}
        </button>
      </nav>
      <div class="admin-foot">
        <span>{{ props.username }}</span>
        <button class="admin-back" @click="emit('exit')">返回工作台</button>
      </div>
    </aside>

    <main class="admin-main">
      <Dashboard v-if="activeView === 'dashboard'" />
      <UserManage v-else-if="activeView === 'users'" />
      <ModelManage v-else-if="activeView === 'models'" />
      <FeatureManage v-else-if="activeView === 'features'" />
      <PointsManage v-else-if="activeView === 'points'" />
      <NotifyManage v-else-if="activeView === 'notify'" />
      <CallRecordsManage v-else-if="activeView === 'records'" />
      <AuditManage v-else-if="activeView === 'audit'" />
      <ApiConfig v-else-if="activeView === 'config'" />
    </main>
  </div>
</template>

<style scoped>
.admin-shell {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  background: var(--color-bg-page);
  font-family: var(--font-sans);
}

.admin-sidebar {
  width: 220px;
  flex-shrink: 0;
  background: #1f232b;
  color: #e6e8eb;
  display: flex;
  flex-direction: column;
  padding: 16px 12px;
}

.admin-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  padding: 8px 10px 20px;
}

.admin-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.admin-nav-item {
  text-align: left;
  padding: 10px 12px;
  border-radius: 8px;
  color: #c7cbd1;
  transition: background 0.15s, color 0.15s;
}
.admin-nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}
.admin-nav-item.active {
  background: var(--color-accent);
  color: #fff;
}

.admin-foot {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
}

.admin-back {
  padding: 8px 0;
  color: var(--color-text-secondary);
  text-align: left;
}
.admin-back:hover {
  color: #fff;
}

.admin-main {
  flex: 1;
  overflow-y: auto;
  padding: 28px 32px;
}

.admin-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--color-text-secondary);
}
.ph-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-primary);
}
.ph-sub {
  font-size: 14px;
}
</style>