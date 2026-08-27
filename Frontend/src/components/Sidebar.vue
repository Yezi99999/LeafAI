<script setup lang="ts">
import { ref } from 'vue'

const navItems = [
  { id: 'new-chat', label: '新对话', icon: 'chat' },
  { id: 'workspace', label: 'AI 工作台', icon: 'monitor' },
  { id: 'skills', label: '技能·连接器·伙伴', icon: 'link' },
  { id: 'api', label: 'API 服务', icon: 'api', hasArrow: true },
  { id: 'more', label: '更多', icon: 'more', hasExpand: true },
]

const recentItems = [
  { id: 1, color: '#10B981', text: '生成一份产品需求文档' },
  { id: 2, color: '#3B82F6', text: '分析用户反馈数据' },
  { id: 3, color: '#F59E0B', text: '翻译技术文档为英文' },
  { id: 4, color: '#8B5CF6', text: '生成周报摘要' },
]

const activeNav = ref('new-chat')
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
      <button class="asset-item">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="asset-icon">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
          <polyline points="10 9 9 9 8 9" />
        </svg>
        <span class="asset-text">最新一条资产记录</span>
      </button>
    </div>

    <div class="sidebar-section recent-section">
      <div class="section-title">最近</div>
      <ul class="recent-list">
        <li v-for="item in recentItems" :key="item.id" class="recent-item">
          <span class="dot" :style="{ background: item.color }"></span>
          <span class="recent-text">{{ item.text }}</span>
        </li>
      </ul>
    </div>

    <div class="sidebar-footer">
      <button class="footer-btn">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
        <span>我的</span>
      </button>
    </div>
  </aside>
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
  padding: 16px 16px 0;
}

.section-title {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
  padding: 0 4px;
}

.asset-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  color: var(--color-text-primary);
  transition: background 0.15s;
  text-align: left;
}
.asset-item:hover {
  background: var(--color-hover);
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

.recent-section {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding-bottom: 0;
}

.recent-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}
.recent-item:hover {
  background: var(--color-hover);
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.recent-text {
  font-size: 13px;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-footer {
  padding: 8px 16px;
  border-top: 1px solid var(--color-border);
}

.footer-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 14px;
  color: var(--color-text-primary);
  transition: background 0.15s;
}
.footer-btn:hover {
  background: var(--color-hover);
}
</style>