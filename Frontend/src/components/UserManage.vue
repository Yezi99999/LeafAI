<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi, type AdminUser } from '../api/index'

const users = ref<AdminUser[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 15
const loading = ref(false)
const keyword = ref('')
const roleFilter = ref('')
const statusFilter = ref('')
const errorMsg = ref('')

// 创建/编辑对话框
const showModal = ref(false)
const editing = ref<AdminUser | null>(null)
const QUOTA_KEYS = ['chat', 'image', 'video', 'audio'] as const
function emptyQuota(): Record<string, number> {
  return { chat: 0, image: 0, video: 0, audio: 0 }
}
const form = ref({
  username: '',
  password: '',
  email: '',
  role: 'user',
  points_balance: 0,
  free_quota: emptyQuota(),
})

async function loadUsers() {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await adminApi.listUsers({
      keyword: keyword.value || undefined,
      role: roleFilter.value || undefined,
      status: statusFilter.value || undefined,
      page: page.value,
      page_size: pageSize,
    })
    users.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e: any) {
    errorMsg.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.value = { username: '', password: '', email: '', role: 'user', points_balance: 0, free_quota: emptyQuota() }
  showModal.value = true
}

function openEdit(u: AdminUser) {
  editing.value = u
  const qi = u.free_quota || {}
  form.value = {
    username: u.username,
    password: '',
    email: u.email || '',
    role: u.role,
    points_balance: u.points_balance,
    free_quota: {
      chat: qi.chat ?? 0,
      image: qi.image ?? 0,
      video: qi.video ?? 0,
      audio: qi.audio ?? 0,
    },
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

async function submit() {
  const quotaNums = QUOTA_KEYS.reduce((acc: Record<string, number>, k) => {
    acc[k] = Number(form.value.free_quota[k])
    return acc
  }, {})
  try {
    if (editing.value) {
      await adminApi.updateUser(editing.value.id, {
        email: form.value.email || undefined,
        role: form.value.role,
        points_balance: form.value.points_balance,
        free_quota: quotaNums,
        password: form.value.password || undefined,
      })
    } else {
      await adminApi.createUser({
        username: form.value.username,
        password: form.value.password,
        email: form.value.email || undefined,
        role: form.value.role,
        points_balance: form.value.points_balance,
        free_quota: quotaNums,
      })
    }
    showModal.value = false
    await loadUsers()
  } catch (e: any) {
    errorMsg.value = e.message || '保存失败'
  }
}

async function toggleActive(u: AdminUser) {
  try {
    if (u.is_active) {
      await adminApi.disableUser(u.id)
    } else {
      await adminApi.enableUser(u.id)
    }
    await loadUsers()
  } catch (e: any) {
    errorMsg.value = e.message || '操作失败'
  }
}

function resetFilters() {
  keyword.value = ''
  roleFilter.value = ''
  statusFilter.value = ''
  page.value = 1
  loadUsers()
}

function search() {
  page.value = 1
  loadUsers()
}

const pageCount = Math.max(1, Math.ceil(total.value / pageSize))

onMounted(loadUsers)
</script>

<template>
  <div class="user-manage">
    <div class="um-header">
      <h2 class="um-title">用户管理</h2>
      <button class="btn primary" @click="openCreate">创建用户</button>
    </div>

    <div class="um-toolbar">
      <input
        v-model="keyword"
        class="um-input"
        placeholder="搜索用户名/邮箱"
        @keyup.enter="search"
      />
      <select v-model="roleFilter" class="um-input short">
        <option value="">全部角色</option>
        <option value="user">普通用户</option>
        <option value="admin">管理员</option>
      </select>
      <select v-model="statusFilter" class="um-input short">
        <option value="">全部状态</option>
        <option value="active">启用</option>
        <option value="disabled">停用</option>
      </select>
      <button class="btn" @click="search">查询</button>
      <button class="btn" @click="resetFilters">重置</button>
    </div>

    <div v-if="errorMsg" class="um-error">{{ errorMsg }}</div>

    <div class="um-table-wrap">
      <table class="um-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>邮箱</th>
            <th>角色</th>
            <th>积分</th>
            <th>图片次数</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.email || '—' }}</td>
            <td><span class="tag" :class="u.role">{{ u.role === 'admin' ? '管理员' : '用户' }}</span></td>
            <td>{{ u.points_balance }}</td>
            <td>{{ u.free_quota?.image === -1 ? '不限' : (u.free_quota?.image ?? 0) }}</td>
            <td><span class="tag" :class="u.is_active ? 'on' : 'off'">{{ u.is_active ? '启用' : '停用' }}</span></td>
            <td>{{ u.create_time?.slice(0, 10) || '—' }}</td>
            <td class="um-ops">
              <button class="link" @click="openEdit(u)">编辑</button>
              <button class="link danger" @click="toggleActive(u)">{{ u.is_active ? '停用' : '启用' }}</button>
            </td>
          </tr>
          <tr v-if="!loading && users.length === 0">
            <td colspan="9" class="um-empty">暂无用户</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="um-pager">
      <span>共 {{ total }} 条</span>
      <div class="um-pager-btns">
        <button class="btn" :disabled="page <= 1" @click="page--; loadUsers()">上一页</button>
        <span>{{ page }} / {{ pageCount }}</span>
        <button class="btn" :disabled="page >= pageCount" @click="page++; loadUsers()">下一页</button>
      </div>
    </div>

    <div v-if="showModal" class="um-modal-mask" @click.self="closeModal">
      <div class="um-modal">
        <h3>{{ editing ? '编辑用户' : '创建用户' }}</h3>
        <div class="um-form">
          <label>用户名<input v-model="form.username" :disabled="!!editing" class="um-input" /></label>
          <label>密码<input v-model="form.password" type="password" class="um-input" :placeholder="editing ? '留空则不修改' : ''" /></label>
          <label>邮箱<input v-model="form.email" class="um-input" /></label>
          <label>角色
            <select v-model="form.role" class="um-input">
              <option value="user">普通用户</option>
              <option value="admin">管理员</option>
            </select>
          </label>
          <label>积分余额<input v-model.number="form.points_balance" type="number" min="0" class="um-input" /></label>
          <label>免费次数（-1=不限次不扣积分，0=消耗积分）
            <div class="quota-grid">
              <div v-for="k in QUOTA_KEYS" :key="k" class="quota-item">
                <span>{{ { chat: '对话', image: '图片', video: '视频', audio: '音频' }[k] }}</span>
                <input v-model.number="form.free_quota[k]" type="number" min="-1" class="um-input short" />
              </div>
            </div>
          </label>
        </div>
        <div v-if="errorMsg" class="um-error">{{ errorMsg }}</div>
        <div class="um-modal-ops">
          <button class="btn" @click="closeModal">取消</button>
          <button class="btn primary" @click="submit">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.user-manage {
  max-width: 1100px;
}

.um-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.um-title {
  font-size: 22px;
  font-weight: 600;
}

.um-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.um-input {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 8px 12px;
  background: var(--color-bg-white);
  color: var(--color-text-primary);
  font-size: 13px;
  min-width: 160px;
}
.um-input.short {
  width: 120px;
  min-width: 120px;
}

.btn {
  padding: 8px 16px;
  border-radius: 8px;
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  font-size: 13px;
  transition: background 0.15s;
}
.btn:hover:not(:disabled) {
  background: var(--color-hover);
}
.btn.primary {
  background: var(--color-accent);
  color: #fff;
  border-color: transparent;
}
.btn.primary:hover {
  opacity: 0.9;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.um-table-wrap {
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  overflow: hidden;
}
.um-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.um-table th,
.um-table td {
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}
.um-table th {
  background: var(--color-hover);
  color: var(--color-text-secondary);
  font-weight: 500;
}
.um-table tr:last-child td {
  border-bottom: none;
}

.tag {
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
}
.tag.admin {
  background: #ede9fe;
  color: #6d28d9;
}
.tag.user {
  background: var(--color-hover);
  color: var(--color-text-secondary);
}
.tag.on {
  background: #dcfce7;
  color: #15803d;
}
.tag.off {
  background: #fee2e2;
  color: #b91c1c;
}

.um-ops {
  display: flex;
  gap: 8px;
}
.link {
  color: var(--color-accent);
  font-size: 13px;
}
.link.danger {
  color: #dc2626;
}
.um-empty {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 32px 0;
}

.um-pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  color: var(--color-text-secondary);
  font-size: 13px;
}
.um-pager-btns {
  display: flex;
  align-items: center;
  gap: 8px;
}

.um-error {
  color: #dc2626;
  margin-bottom: 12px;
  font-size: 13px;
}

.um-modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
}
.um-modal {
  width: 420px;
  background: var(--color-bg-white);
  border-radius: 14px;
  padding: 24px;
}
.um-modal h3 {
  margin-bottom: 16px;
  font-size: 17px;
}
.um-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.um-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.um-form .um-input {
  min-width: 0;
}

.quota-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.quota-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.quota-item span {
  width: 34px;
  flex-shrink: 0;
  color: var(--color-text-primary);
}
.quota-item .um-input.short {
  width: 100%;
  min-width: 0;
}
.um-modal-ops {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}
</style>