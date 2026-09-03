<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApiPoints, adminApi, type PointsRate, type PointsTransaction, type PointsSummary, type ModelPoints, type AdminUser } from '../api'

const tab = ref<'recharge' | 'rates' | 'tx' | 'models' | 'summary'>('recharge')

// ===== 费率配置 =====
const rates = ref<PointsRate[]>([])
const rateLoading = ref(false)
function loadRates() {
  rateLoading.value = true
  adminApiPoints.listRates()
    .then((res) => (rates.value = res.data?.items || []))
    .finally(() => (rateLoading.value = false))
}
async function toggleRate(r: PointsRate) {
  try {
    await adminApiPoints.updateRate(r.id, { enabled: !r.enabled })
    r.enabled = !r.enabled
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}
async function removeRate(r: PointsRate) {
  if (!confirm(`确定删除「${r.service_label || r.service_code}」的费率吗？`)) return
  try {
    await adminApiPoints.deleteRate(r.id)
    rates.value = rates.value.filter((x) => x.id !== r.id)
  } catch (e: any) {
    alert(e.message || '删除失败')
  }
}

// 服务（分类）选项：label=中文，category=模型分类筛选，code=服务代码
const SERVICE_OPTIONS = [
  { label: '图片生成', category: 'image', code: 'image_generate' },
  { label: '对话', category: 'chat', code: 'chat' },
  { label: '视频生成', category: 'video', code: 'video_generate' },
  { label: '语音', category: 'audio', code: 'audio' },
]
const UNIT_LABELS: Record<string, string> = { per_call: '次', per_token: 'token', per_image: '张' }
const MULTIPLIER_PRESETS = [1, 1.5, 2, 3, 5, 10]

const showCreateRate = ref(false)
const rateForm = ref({
  service_code: 'image_generate',
  model_id: null as number | null,
  rate_unit: 'per_call',
  multiplier: 1.0,
  enabled: true,
})

const modelsForRate = ref<ModelPoints[]>([])
const rateService = ref(`${SERVICE_OPTIONS[0].code}|${SERVICE_OPTIONS[0].category}`)
function openCreateRate() {
  showCreateRate.value = true
  resetRateForm()
}
function resetRateForm() {
  const [code, cat] = rateService.value.split('|')
  rateForm.value = { service_code: code, model_id: null, rate_unit: 'per_call', multiplier: 1.0, enabled: true }
  modelsForRate.value = models.value.filter((m) => m.category === cat)
}
function onServiceChange() {
  const [, cat] = rateService.value.split('|')
  modelsForRate.value = models.value.filter((m) => m.category === cat)
  rateForm.value.model_id = null
}
async function submitRate() {
  if (!rateForm.value.service_code || rateForm.value.multiplier < 0) return alert('请选择分类并填写有效倍率')
  try {
    await adminApiPoints.createRate({
      service_code: rateForm.value.service_code,
      model_id: rateForm.value.model_id,
      rate_unit: rateForm.value.rate_unit,
      multiplier: rateForm.value.multiplier,
      enabled: rateForm.value.enabled,
    })
    showCreateRate.value = false
    resetRateForm()
    loadRates()
  } catch (e: any) {
    alert(e.message || '创建失败')
  }
}

// ===== 充值 =====
const rechargeForm = ref({ user_id: 0, points_delta: 0, remark: '' })
async function doRecharge() {
  if (!rechargeForm.value.user_id || !rechargeForm.value.points_delta) return alert('请填写用户ID和增减积分')
  try {
    const res = await adminApiPoints.recharge(rechargeForm.value)
    const d = res.data
    alert(`已${d.points_delta > 0 ? '充值' : '调整'} ${d.points_delta}，余额 ${d.balance_after}`)
    rechargeForm.value = { user_id: 0, points_delta: 0, remark: '' }
    loadTx(1)
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}

// ===== 充值模块（独立） =====
const userSearch = ref('')
const userResults = ref<AdminUser[]>([])
const selectedUser = ref<AdminUser | null>(null)
const searching = ref(false)
const recharging = ref(false)
const rechargeAmount = ref(0)
const rechargeRemark = ref('')
const rechargeMsg = ref('')

async function searchUsers() {
  const kw = userSearch.value.trim()
  if (!kw) {
    userResults.value = []
    return
  }
  searching.value = true
  rechargeMsg.value = ''
  try {
    const res = await adminApi.listUsers({ keyword: kw, page_size: 20 })
    userResults.value = res.data?.items || []
  } catch (e: any) {
    rechargeMsg.value = e.message || '查询失败'
  } finally {
    searching.value = false
  }
}
function pickUser(u: AdminUser) {
  selectedUser.value = u
  userSearch.value = `${u.username}（ID ${u.id}）`
  userResults.value = []
}
async function doRecharge2() {
  if (!selectedUser.value) return alert('请先选择用户')
  if (!rechargeAmount.value) return alert('请输入充值积分')
  recharging.value = true
  rechargeMsg.value = ''
  try {
    const res = await adminApiPoints.recharge({
      user_id: selectedUser.value.id,
      points_delta: rechargeAmount.value,
      remark: rechargeRemark.value.trim() || undefined,
    })
    rechargeMsg.value = `已${res.data.points_delta > 0 ? '充值' : '调整'} ${res.data.points_delta} 积分，当前余额 ${res.data.balance_after}`
    selectedUser.value!.points_balance = res.data.balance_after
    rechargeAmount.value = 0
    rechargeRemark.value = ''
  } catch (e: any) {
    rechargeMsg.value = e.message || '操作失败'
  } finally {
    recharging.value = false
  }
}

// ===== 流水（仿订单） =====
const tx = ref<(PointsTransaction & { username: string })[]>([])
const txTotal = ref(0)
const txPage = ref(1)
const orderFilter = ref({ username: '', tx_type: '' })
const PAGE_SIZE = 20
function loadTx(page: number) {
  txPage.value = page
  adminApiPoints.listOrders({
    username: orderFilter.value.username || undefined,
    tx_type: orderFilter.value.tx_type || undefined,
    page,
    page_size: PAGE_SIZE,
  }).then((res) => {
    tx.value = res.data?.items || []
    txTotal.value = res.data?.total || 0
  })
}
const TX_LABEL: Record<string, string> = { recharge: '充值', consume: '消费', refund: '返还', admin_adjust: '人工调整' }
function fmtDelta(d: number) {
  return (d > 0 ? '+' : '') + d
}

// ===== 模型积分消耗 =====
const models = ref<ModelPoints[]>([])
const modelLoading = ref(false)
const editingId = ref<number | null>(null)
const editPoints = ref(0)
function loadModels() {
  modelLoading.value = true
  adminApiPoints.listModelPoints()
    .then((res) => (models.value = res.data?.items || []))
    .finally(() => (modelLoading.value = false))
}
function startEdit(m: ModelPoints) {
  editingId.value = m.id
  editPoints.value = m.unit_points
}
async function savePoints(m: ModelPoints) {
  if (editPoints.value < 0) return alert('积分不能为负数')
  try {
    const res = await adminApiPoints.updateModelPoints(m.id, editPoints.value)
    m.unit_points = res.data.unit_points
    editingId.value = null
  } catch (e: any) {
    alert(e.message || '保存失败')
  }
}
const CAT_LABEL: Record<string, string> = { chat: '对话', image: '图片', video: '视频', audio: '语音' }

// ===== 汇总 =====
const summary = ref<PointsSummary | null>(null)
function loadSummary() {
  adminApiPoints.summary().then((res) => (summary.value = res.data))
}

function switchTab(t: 'recharge' | 'rates' | 'tx' | 'models' | 'summary') {
  tab.value = t
  if (t === 'tx') loadTx(1)
  else if (t === 'models') loadModels()
  else if (t === 'summary') loadSummary()
}

onMounted(() => {
  loadRates()
  loadModels()
  loadSummary()
})
</script>

<template>
  <div class="points-manage">
    <div class="pm-header">
      <h2 class="pm-title">积分管理</h2>
      <div class="pm-tabs">
        <button :class="{ active: tab === 'recharge' }" @click="switchTab('recharge')">充值管理</button>
        <button :class="{ active: tab === 'rates' }" @click="switchTab('rates')">费率配置</button>
        <button :class="{ active: tab === 'models' }" @click="switchTab('models')">模型消耗</button>
        <button :class="{ active: tab === 'tx' }" @click="switchTab('tx')">消耗记录</button>
        <button :class="{ active: tab === 'summary' }" @click="switchTab('summary')">消耗汇总</button>
      </div>
    </div>

    <!-- 充值管理 -->
    <div v-if="tab === 'recharge'">
      <div class="pm-recharge-box">
        <h3 class="pm-recharge-title">给用户充值 / 调整积分</h3>
        <div class="pm-recharge-form">
          <div class="pm-user-search">
            <input v-model="userSearch" class="pm-input" placeholder="输入用户名/ID 检索用户" @keyup.enter="searchUsers" />
            <button class="btn" :disabled="searching" @click="searchUsers">{{ searching ? '搜索中...' : '搜索' }}</button>
            <div v-if="userResults.length" class="pm-search-drop">
              <div
                v-for="u in userResults"
                :key="u.id"
                class="pm-search-item"
                @click="pickUser(u)"
              >
                <span>{{ u.username }}（ID {{ u.id }}）</span>
                <span class="pm-search-balance">余额 {{ u.points_balance }} / 免费次数 {{ JSON.stringify(u.free_quota) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-if="selectedUser" class="pm-recharge-form pm-recharge-form2">
          <div class="pm-recharge-now">当前用户：{{ selectedUser.username }}（ID {{ selectedUser.id }}），积分余额 <b>{{ selectedUser.points_balance }}</b></div>
          <input v-model.number="rechargeAmount" type="number" class="pm-input" placeholder="充入积分（正=充值，负=扣回）" />
          <input v-model="rechargeRemark" class="pm-input" placeholder="备注（选填）" />
          <button class="btn primary" :disabled="recharging" @click="doRecharge2">{{ recharging ? '执行中...' : '执行充值' }}</button>
        </div>
        <div v-if="rechargeMsg" class="pm-recharge-msg">{{ rechargeMsg }}</div>
      </div>
      <p class="pm-tip">提示：净增积分为正即充值，为负即从用户积分中扣回；操作会记为「充值」或「人工调整」流水并计入余额快照。</p>
    </div>

    <!-- 费率配置 -->
    <div v-if="tab === 'rates'">
      <p class="pm-tip">计费单位按中文显示（次 / token / 张）；选择倍率后，实际消耗积分 = 该模型「模型消耗」中的单次积分 × 倍率。选"全部模型"表示该分类下所有模型统一按此倍率。</p>
      <div class="pm-toolbar">
        <button class="btn primary" @click="openCreateRate">新增费率</button>
      </div>

      <!-- 新增费率表单 -->
      <div v-if="showCreateRate" class="pm-recharge-box">
        <h3 class="pm-recharge-title">新增费率配置</h3>
        <div class="pm-recharge-form">
          <select v-model="rateService" class="pm-input pm-select" @change="onServiceChange">
            <option v-for="s in SERVICE_OPTIONS" :key="s.code" :value="`${s.code}|${s.category}`">{{ s.label }}</option>
          </select>
          <select v-model.number="rateForm.model_id" class="pm-input pm-select">
            <option :value="null">全部模型</option>
            <option v-for="m in modelsForRate" :key="m.id" :value="m.id">{{ m.display_name }}（单次 {{ m.unit_points }} 积分）</option>
          </select>
          <select v-model="rateForm.rate_unit" class="pm-input pm-select">
            <option v-for="(label, k) in UNIT_LABELS" :key="k" :value="k">{{ label }}</option>
          </select>
          <select v-model.number="rateForm.multiplier" class="pm-input pm-select">
            <option v-for="m in MULTIPLIER_PRESETS" :key="m" :value="m">{{ m }}×</option>
          </select>
          <label class="pm-check">
            <input v-model="rateForm.enabled" type="checkbox" /> 启用
          </label>
          <button class="btn primary" @click="submitRate">保存</button>
          <button class="btn" @click="showCreateRate = false">取消</button>
        </div>
      </div>

      <div class="pm-recharge-box">
        <h3 class="pm-recharge-title">积分充值 / 调整</h3>
        <div class="pm-recharge-form">
          <input v-model.number="rechargeForm.user_id" type="number" class="pm-input" placeholder="用户ID" />
          <input v-model.number="rechargeForm.points_delta" type="number" class="pm-input" placeholder="增减积分（正=充值，负=扣回）" />
          <input v-model="rechargeForm.remark" class="pm-input" placeholder="备注（选填）" />
          <button class="btn primary" @click="doRecharge">执行</button>
        </div>
      </div>
      <table class="pm-table">
        <thead>
          <tr>
            <th>分类</th><th>模型</th><th>计费单位</th><th>倍率</th><th>状态</th><th class="row-ops">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rates" :key="r.id">
            <td>{{ r.service_label || r.service_code }}</td>
            <td>{{ r.model_display || '全部模型' }}</td>
            <td>{{ r.unit_label || r.rate_unit }}</td>
            <td>{{ r.multiplier }}×</td>
            <td><span class="tag" :class="r.enabled ? 'on' : 'off'">{{ r.enabled ? '启用' : '停用' }}</span></td>
            <td class="row-ops">
              <button class="link" @click="toggleRate(r)">{{ r.enabled ? '停用' : '启用' }}</button>
              <button class="link danger" @click="removeRate(r)">删除</button>
            </td>
          </tr>
          <tr v-if="!rateLoading && rates.length === 0">
            <td colspan="6" class="pm-empty">暂无费率配置</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 模型积分消耗 -->
    <div v-if="tab === 'models'">
      <p class="pm-tip">修改已有模型单次调用消耗积分（计费按模型 `unit_points`，任务成功后从用户积分扣减）。</p>
      <table class="pm-table">
        <thead>
          <tr>
            <th>ID</th><th>模型</th><th>分类</th><th>单次消耗(积分)</th><th>成功/失败</th><th class="row-ops">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in models" :key="m.id">
            <td>{{ m.id }}</td>
            <td>{{ m.display_name }} <span class="mono pm-sub">({{ m.model_name }})</span></td>
            <td>{{ CAT_LABEL[m.category] || m.category }}</td>
            <td>
              <template v-if="editingId === m.id">
                <input v-model.number="editPoints" type="number" class="pm-input pm-edits" min="0" />
              </template>
              <template v-else>{{ m.unit_points }}</template>
            </td>
            <td><span class="pos">{{ m.success_count }}</span> / <span class="neg">{{ m.fail_count }}</span></td>
            <td class="row-ops">
              <template v-if="editingId === m.id">
                <button class="link" @click="savePoints(m)">保存</button>
                <button class="link danger" @click="editingId = null">取消</button>
              </template>
              <button v-else class="link" @click="startEdit(m)">修改消耗</button>
            </td>
          </tr>
          <tr v-if="!modelLoading && models.length === 0">
            <td colspan="6" class="pm-empty">暂无模型</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 消耗记录（仿订单） -->
    <div v-if="tab === 'tx'" class="pm-tx">
      <div class="pm-filters">
        <input v-model="orderFilter.username" class="pm-input" placeholder="用户名" @keyup.enter="loadTx(1)" />
        <select v-model="orderFilter.tx_type" class="pm-input" @change="loadTx(1)">
          <option value="">全部类型</option>
          <option v-for="(label, k) in TX_LABEL" :key="k" :value="k">{{ label }}</option>
        </select>
        <button class="btn primary" @click="loadTx(1)">查询</button>
      </div>
      <table class="pm-table">
        <thead>
          <tr>
            <th>单号</th><th>用户</th><th>类型</th><th>变动(积分)</th><th>余额</th><th>服务</th><th>任务</th><th>备注</th><th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in tx" :key="t.id">
            <td class="mono">#{{ t.id }}</td>
            <td>{{ t.username || t.user_id }}</td>
            <td>{{ TX_LABEL[t.tx_type] || t.tx_type }}</td>
            <td :class="t.points_delta < 0 ? 'neg' : 'pos'">{{ fmtDelta(t.points_delta) }}</td>
            <td>{{ t.balance_after }}</td>
            <td>{{ t.service_code || '-' }}</td>
            <td class="mono">{{ (t.task_id || '').slice(0, 8) || '-' }}</td>
            <td>{{ t.remark || '-' }}</td>
            <td>{{ new Date(t.create_time).toLocaleString() }}</td>
          </tr>
          <tr v-if="tx.length === 0">
            <td colspan="9" class="pm-empty">暂无记录</td>
          </tr>
        </tbody>
      </table>
      <div class="pm-pager">
        <button class="btn" :disabled="txPage <= 1" @click="loadTx(txPage - 1)">上一页</button>
        <span>第 {{ txPage }} 页 / 共 {{ Math.ceil(txTotal / PAGE_SIZE) || 1 }} 页（{{ txTotal }} 条）</span>
        <button class="btn" :disabled="txPage * PAGE_SIZE >= txTotal" @click="loadTx(txPage + 1)">下一页</button>
      </div>
    </div>

    <!-- 消耗汇总 -->
    <div v-if="tab === 'summary'" class="pm-summary">
      <h3>按服务汇总</h3>
      <table class="pm-table">
        <thead>
          <tr><th>服务</th><th>消费</th><th>充值</th><th>返还</th><th>人工调整</th><th>笔数</th></tr>
        </thead>
        <tbody>
          <tr v-for="s in summary?.service || []" :key="s.service_code">
            <td>{{ s.service_code }}</td>
            <td class="neg">{{ s.consume }}</td>
            <td class="pos">{{ s.recharge }}</td>
            <td class="pos">{{ s.refund }}</td>
            <td>{{ s.adjust }}</td>
            <td>{{ s.tx_count }}</td>
          </tr>
          <tr v-if="!(summary?.service?.length)">
            <td colspan="6" class="pm-empty">暂无数据</td>
          </tr>
        </tbody>
      </table>
      <h3>按日汇总</h3>
      <table class="pm-table">
        <thead>
          <tr><th>日期</th><th>消费</th><th>充值</th><th>返还</th><th>人工调整</th></tr>
        </thead>
        <tbody>
          <tr v-for="d in summary?.daily || []" :key="d.date">
            <td>{{ d.date }}</td>
            <td class="neg">{{ d.consume }}</td>
            <td class="pos">{{ d.recharge }}</td>
            <td class="pos">{{ d.refund }}</td>
            <td>{{ d.adjust }}</td>
          </tr>
          <tr v-if="!(summary?.daily?.length)">
            <td colspan="5" class="pm-empty">暂无数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.points-manage { max-width: 1200px; }
.pm-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.pm-title { font-size: 22px; font-weight: 600; }
.pm-tabs { display: flex; gap: 8px; }
.pm-tabs button { padding: 8px 16px; border-radius: 8px; border: 1px solid var(--color-border); background: var(--color-bg-white); color: var(--color-text-primary); cursor: pointer; }
.pm-tabs button.active { background: var(--color-accent); color: #fff; border-color: transparent; }
.pm-toolbar, .pm-filters { display: flex; gap: 12px; margin-bottom: 12px; align-items: center; flex-wrap: wrap; }
.pm-recharge-box { background: var(--color-bg-white); border: 1px solid var(--color-border); border-radius: 12px; padding: 16px; margin-bottom: 16px; }
.pm-recharge-title { font-size: 14px; font-weight: 600; margin-bottom: 10px; }
.pm-recharge-form { display: flex; gap: 10px; flex-wrap: wrap; }
.pm-recharge-form2 { align-items: center; margin-top: 12px; }
.pm-recharge-now { font-size: 13px; width: 100%; }
.pm-recharge-msg { margin-top: 8px; font-size: 13px; color: var(--color-accent); }
.pm-user-search { position: relative; display: flex; gap: 8px; width: 100%; }
.pm-search-drop {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  z-index: 20;
  max-height: 240px;
  overflow-y: auto;
  background: var(--color-bg-white, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 8px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
}
.pm-search-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  border-bottom: 1px solid var(--color-border, #f0f0f0);
}
.pm-search-item:last-child { border-bottom: none; }
.pm-search-item:hover { background: var(--color-bg-hover, #f6f7f9); }
.pm-search-balance { color: var(--color-text-secondary); font-size: 12px; }
.pm-tip { font-size: 12px; color: var(--color-text-secondary); margin-bottom: 12px; line-height: 1.6; }
.pm-edits { width: 80px; }
.pm-sub { font-size: 11px; color: var(--color-text-secondary); }
.pm-select { min-width: 140px; }
.pm-check { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; padding: 7px 0; }
.btn { padding: 8px 16px; border-radius: 8px; background: var(--color-bg-white); border: 1px solid var(--color-border); color: var(--color-text-primary); cursor: pointer; font-size: 13px; }
.btn.primary { background: var(--color-accent); color: #fff; border-color: transparent; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.pm-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.pm-table th, .pm-table td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--color-border); }
.pm-table th { color: var(--color-text-secondary); font-weight: 500; }
.row-ops { text-align: right; }
.link { color: var(--color-accent); margin-right: 8px; }
.link.danger { color: #dc2626; }
.pos { color: #15803d; }
.neg { color: #b91c1c; }
.mono { font-family: monospace; }
.pm-empty { text-align: center; color: var(--color-text-secondary); padding: 24px 0; }
.pm-pager { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 16px; }
.pm-input { border: 1px solid var(--color-border); border-radius: 8px; padding: 8px 12px; background: var(--color-bg-white); color: var(--color-text-primary); font-size: 13px; }
.tag { padding: 2px 10px; border-radius: 999px; font-size: 12px; }
.tag.on { background: #dcfce7; color: #15803d; }
.tag.off { background: #fee2e2; color: #b91c1c; }
.pm-summary h3 { margin: 20px 0 8px; font-size: 15px; }
</style>