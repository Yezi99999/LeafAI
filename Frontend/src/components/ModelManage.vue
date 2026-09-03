<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  adminApiModels,
  type AdminModel,
  type ModelMetrics,
} from '../api/index'

const models = ref<AdminModel[]>([])
const providers = ref<Record<number, string>>({})
const loading = ref(false)
const errorMsg = ref('')
const category = ref('')

const categoryOptions = [
  { value: '', label: '全部分类' },
  { value: 'chat', label: '对话' },
  { value: 'image', label: '图片' },
  { value: 'video', label: '视频' },
  { value: 'audio', label: '音频' },
]

const deployStatusMap: Record<string, { label: string; cls: string }> = {
  running: { label: '运行中', cls: 'on' },
  maintaining: { label: '维护中', cls: 'warn' },
  down: { label: '已下线', cls: 'off' },
}

async function loadProviders() {
  try {
    const res = await adminApiModels.listProviders()
    const items = res.data?.items || []
    providers.value = items.reduce((acc: Record<number, string>, p) => {
      acc[p.id] = p.name
      return acc
    }, {})
  } catch {
    providers.value = {}
  }
}

async function loadModels() {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await adminApiModels.listModels({ category: category.value || undefined, page_size: 100 })
    models.value = res.data?.items || []
  } catch (e: any) {
    errorMsg.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function toggleEnable(m: AdminModel) {
  try {
    await adminApiModels.updateModel(m.id, { is_enabled: !m.is_enabled })
    await loadModels()
  } catch (e: any) {
    errorMsg.value = e.message || '操作失败'
  }
}

async function cycleDeploy(m: AdminModel) {
  const next: Record<string, string> = { running: 'maintaining', maintaining: 'down', down: 'running' }
  try {
    await adminApiModels.setModelDeploy(m.id, next[m.deploy_status])
    await loadModels()
  } catch (e: any) {
    errorMsg.value = e.message || '操作失败'
  }
}

// 指标弹窗
const metricsRef = ref<AdminModel | null>(null)
const metrics = ref<ModelMetrics | null>(null)
async function viewMetrics(m: AdminModel) {
  metricsRef.value = m
  metrics.value = null
  try {
    const res = await adminApiModels.getModelMetrics(m.id)
    metrics.value = res.data
  } catch {
    metrics.value = null
  }
}

// 版本登记弹窗
const showVersion = ref(false)
const versionTarget = ref<AdminModel | null>(null)
const versionForm = ref({ version: '', deploy_env: 'prod' })
async function openVersion(m: AdminModel) {
  versionTarget.value = m
  versionForm.value = { version: m.version || '', deploy_env: m.deploy_env || 'prod' }
  showVersion.value = true
}
async function submitVersion() {
  if (!versionTarget.value) return
  try {
    await adminApiModels.registerModelVersion(versionTarget.value.id, versionForm.value.version, versionForm.value.deploy_env)
    showVersion.value = false
    await loadModels()
  } catch (e: any) {
    errorMsg.value = e.message || '保存失败'
  }
}

onMounted(() => {
  loadProviders()
  loadModels()
})
</script>

<template>
  <div class="model-manage">
    <div class="mm-header">
      <h2 class="mm-title">模型管理</h2>
      <div class="mm-filters">
        <select v-model="category" class="mm-input short" @change="loadModels">
          <option v-for="opt in categoryOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <button class="btn" @click="loadModels">刷新</button>
      </div>
    </div>

    <div v-if="errorMsg" class="mm-error">{{ errorMsg }}</div>

    <div class="mm-table-wrap">
      <table class="mm-table">
        <thead>
          <tr>
            <th>展示名</th>
            <th>服务商</th>
            <th>类型</th>
            <th>真实模型</th>
            <th>版本</th>
            <th>环境</th>
            <th>部署状态</th>
            <th>积分/次</th>
            <th>性能</th>
            <th>启用</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in models" :key="m.id">
            <td>{{ m.display_name }}</td>
            <td>{{ providers[m.provider_id] || m.provider_id }}</td>
            <td>{{ m.category }}</td>
            <td>{{ m.model_name }}</td>
            <td>{{ m.version || '—' }}</td>
            <td>{{ m.deploy_env }}</td>
            <td>
              <span class="tag" :class="deployStatusMap[m.deploy_status]?.cls">
                {{ deployStatusMap[m.deploy_status]?.label || m.deploy_status }}
              </span>
            </td>
            <td>{{ m.unit_points }}</td>
            <td class="mm-metrics">
              <span>{{ m.success_count + m.fail_count > 0 ? (m.fail_count / (m.success_count + m.fail_count)) : 0 }}
                <template v-if="m.success_count + m.fail_count > 0">%失败</template>
              </span>
              <button class="link" @click="viewMetrics(m)">查看</button>
            </td>
            <td><span class="tag" :class="m.is_enabled ? 'on' : 'off'">{{ m.is_enabled ? '启用' : '停用' }}</span></td>
            <td class="mm-ops">
              <button class="link" @click="openVersion(m)">登记版本</button>
              <button class="link" @click="cycleDeploy(m)">切换部署</button>
              <button class="link danger" @click="toggleEnable(m)">{{ m.is_enabled ? '停用' : '启用' }}</button>
            </td>
          </tr>
          <tr v-if="!loading && models.length === 0">
            <td colspan="11" class="mm-empty">暂无模型</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 指标弹窗 -->
    <div v-if="metricsRef" class="mm-modal-mask" @click.self="metricsRef = null">
      <div class="mm-modal">
        <h3>性能指标 — {{ metricsRef.display_name }}</h3>
        <div v-if="metrics" class="mm-metric-grid">
          <div class="mm-metric">
            <div class="mm-k">成功次数</div>
            <div class="mm-v">{{ metrics.success_count }}</div>
          </div>
          <div class="mm-metric">
            <div class="mm-k">失败次数</div>
            <div class="mm-v">{{ metrics.fail_count }}</div>
          </div>
          <div class="mm-metric">
            <div class="mm-k">成功率</div>
            <div class="mm-v">{{ (metrics.success_rate * 100).toFixed(2) }}%</div>
          </div>
          <div class="mm-metric">
            <div class="mm-k">平均延迟</div>
            <div class="mm-v">{{ metrics.avg_latency_ms != null ? metrics.avg_latency_ms + ' ms' : '—' }}</div>
          </div>
        </div>
        <div v-else class="mm-empty">指标数据暂不可用</div>
        <div class="mm-modal-ops">
          <button class="btn" @click="metricsRef = null">关闭</button>
        </div>
      </div>
    </div>

    <!-- 版本登记弹窗 -->
    <div v-if="showVersion" class="mm-modal-mask" @click.self="showVersion = false">
      <div class="mm-modal">
        <h3>登记版本 — {{ versionTarget?.display_name }}</h3>
        <div class="mm-form">
          <label>版本号<input v-model="versionForm.version" class="mm-input" placeholder="v2.0" /></label>
          <label>部署环境
            <select v-model="versionForm.deploy_env" class="mm-input">
              <option value="prod">prod</option>
              <option value="sandbox">sandbox</option>
            </select>
          </label>
        </div>
        <div v-if="errorMsg" class="mm-error">{{ errorMsg }}</div>
        <div class="mm-modal-ops">
          <button class="btn" @click="showVersion = false">取消</button>
          <button class="btn primary" @click="submitVersion">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.model-manage {
  max-width: 1200px;
}
.mm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.mm-title {
  font-size: 22px;
  font-weight: 600;
}
.mm-filters {
  display: flex;
  gap: 8px;
  align-items: center;
}
.mm-input {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 8px 12px;
  background: var(--color-bg-white);
  color: var(--color-text-primary);
  font-size: 13px;
}
.mm-input.short {
  width: 120px;
}
.btn {
  padding: 8px 16px;
  border-radius: 8px;
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  font-size: 13px;
}
.btn:hover:not(:disabled) {
  background: var(--color-hover);
}
.btn.primary {
  background: var(--color-accent);
  color: #fff;
  border-color: transparent;
}
.mm-error {
  color: #dc2626;
  margin-bottom: 12px;
  font-size: 13px;
}
.mm-table-wrap {
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  overflow: hidden;
}
.mm-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.mm-table th,
.mm-table td {
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}
.mm-table th {
  background: var(--color-hover);
  color: var(--color-text-secondary);
  font-weight: 500;
}
.mm-table tr:last-child td {
  border-bottom: none;
}
.tag {
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
}
.tag.on {
  background: #dcfce7;
  color: #15803d;
}
.tag.off {
  background: #fee2e2;
  color: #b91c1c;
}
.tag.warn {
  background: #fef9c3;
  color: #a16207;
}
.mm-metrics {
  display: flex;
  align-items: center;
  gap: 8px;
}
.mm-ops {
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
.mm-empty {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 32px 0;
}
.mm-modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2100;
}
.mm-modal {
  width: 380px;
  background: var(--color-bg-white);
  border-radius: 14px;
  padding: 24px;
}
.mm-modal h3 {
  margin-bottom: 16px;
  font-size: 16px;
}
.mm-metric-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.mm-metric {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 12px;
  text-align: center;
}
.mm-k {
  font-size: 12px;
  color: var(--color-text-secondary);
}
.mm-v {
  font-size: 22px;
  font-weight: 600;
  margin-top: 4px;
}
.mm-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.mm-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.mm-modal-ops {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}
</style>