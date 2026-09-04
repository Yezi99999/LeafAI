const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const API_PREFIX = '/api/v1'
export { BASE_URL, API_PREFIX }

interface ApiResponse<T = any> {
  code: number
  msg: string
  data: T
}

function getToken(): string | null {
  return localStorage.getItem('leafai_token')
}

async function request<T = any>(url: string, options?: RequestInit): Promise<ApiResponse<T>> {
  const isForm = options?.body instanceof FormData
  const headers: Record<string, string> = {
    ...(isForm ? {} : { 'Content-Type': 'application/json' }),
    ...(options?.headers as Record<string, string>),
  }
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const response = await fetch(`${BASE_URL}${API_PREFIX}${url}`, {
    headers,
    ...options,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ msg: 'Network Error' }))
    throw new Error(error.msg || error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export interface ImageGenerateParams {
  model_id: number
  prompt: string
  resolution: string
  aspect_ratio: string
  quality: string
  image?: string[]
  callback_url?: string
}

export interface ImageGenerateResult {
  task_id: string
  status: string
  message: string
}

export interface TaskStatusResult {
  task_id: string
  category: string
  status: string
  input_params: Record<string, any>
  result: Record<string, any> | null
  error_msg: string | null
  create_time: string
  update_time: string
}

export interface ChatCompletionParams {
  model_id: number
  messages: Array<{ role: string; content: string }>
  session_id?: string
  stream?: boolean
  temperature?: number
  max_tokens?: number
}

export interface ResolutionEntry {
  original: string
  aligned: string
}

export interface ResolutionConfig {
  ratio: string
  description: string
  resolutions: Record<string, ResolutionEntry>
}

export interface PointsRecord {
  id: number
  user_id: number
  tx_type: string
  points_delta: number
  service_code: string | null
  task_id: string | null
  model_id: number | null
  balance_after: number
  remark: string | null
  create_time: string
}

export const api = {
  generateImage(params: ImageGenerateParams): Promise<ApiResponse<ImageGenerateResult>> {
    return request('/image/generate', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  },

  getTaskStatus(taskId: string): Promise<ApiResponse<TaskStatusResult>> {
    return request(`/task/${taskId}`)
  },

  listTasks(params?: { status?: string; page?: number; page_size?: number }): Promise<ApiResponse<{ items: TaskStatusResult[]; total: number }>> {
    const query = new URLSearchParams()
    if (params?.status) query.set('status', params.status)
    if (params?.page) query.set('page', String(params.page))
    if (params?.page_size) query.set('page_size', String(params.page_size))
    const qs = query.toString()
    return request(`/task/${qs ? '?' + qs : ''}`)
  },

  getResolutions(): Promise<ApiResponse<{ aspect_ratios: ResolutionConfig[] }>> {
    return request('/config/resolutions')
  },

  getFeatures(): Promise<ApiResponse<{ items: string[]; total: number }>> {
    return request('/config/features')
  },

  chatCompletion(params: ChatCompletionParams): Promise<ApiResponse<any>> {
    return request('/chat/completions', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  },

  chatCompletionStream(params: ChatCompletionParams, onData: (content: string) => void): Promise<string> {
    return new Promise((resolve, reject) => {
      let url = `${BASE_URL}${API_PREFIX}/chat/completions`
      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ ...params, stream: true }),
      })
        .then(async (response) => {
          if (!response.ok || !response.body) {
            const err = await response.json().catch(() => ({ msg: `HTTP ${response.status}` }))
            throw new Error(err.msg || err.detail || `HTTP ${response.status}`)
          }
          const reader = response.body.getReader()
          const decoder = new TextDecoder()
          let buffer = ''
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            buffer += decoder.decode(value, { stream: true })
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''
            for (const line of lines) {
              if (!line.startsWith('data: ')) continue
              const data = line.slice(6)
              if (data === '[DONE]') continue
              try {
                const parsed = JSON.parse(data)
                const content = parsed.choices?.[0]?.delta?.content
                if (content) onData(content)
              } catch {
                // ignore malformed chunk
              }
            }
          }
          resolve('')
        })
        .catch(reject)
    })
  },

  getChatUsage(): Promise<ApiResponse<{ total_tokens: number }>> {
    return request('/chat/usage')
  },

  listChatSessions(): Promise<ApiResponse<{ items: Array<{ id: string; title: string; create_time: string; update_time: string }>; total: number }>> {
    return request('/chat/sessions')
  },

  getChatSessionMessages(sessionId: string): Promise<ApiResponse<{ items: Array<{ id: number; session_id: string; role: string; content: string; create_time: string }>; total: number }>> {
    return request(`/chat/sessions/${sessionId}/messages`)
  },

  getModels(category?: string): Promise<ApiResponse<any>> {
    const query = category ? `?category=${category}` : ''
    return request(`/config/models${query}`)
  },

  login(username: string, password: string): Promise<ApiResponse<{ access_token: string; token_type: string; username: string; user_id: string }>> {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
  },

  register(username: string, password: string, email?: string): Promise<ApiResponse<{ access_token: string; token_type: string; username: string; user_id: string }>> {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, email }),
    })
  },

  getMe(): Promise<ApiResponse<{ id: number; user_id: string; username: string; email: string | null; is_active: boolean; is_superuser: boolean; role: string; points_balance: number; free_quota: Record<string, number> }>> {
    return request('/auth/me')
  },

  getApiDocs(): Promise<ApiResponse<{ key: string; value: { title: string; content: string } }>> {
    return request('/config/item?key=api-docs')
  },

  myPointsRecords(params: { direction?: 'out' | 'in'; page?: number; page_size?: number }): Promise<ApiResponse<{ items: PointsRecord[]; total: number; page: number; page_size: number }>> {
    const q = new URLSearchParams()
    if (params.direction) q.set('direction', params.direction)
    q.set('page', String(params.page ?? 1))
    q.set('page_size', String(params.page_size ?? 20))
    return request(`/points/records?${q.toString()}`)
  },
}

export interface AdminUser {
  id: number
  user_id: string
  username: string
  email: string | null
  role: string
  is_active: boolean
  points_balance: number
  free_quota: Record<string, number>
  create_time: string
}

export interface AdminUserCreate {
  username: string
  password: string
  email?: string
  role?: string
  points_balance?: number
  free_quota?: Record<string, number>
}

export interface AdminUserUpdate {
  email?: string
  role?: string
  password?: string
  is_active?: boolean
  points_balance?: number
  free_quota?: Record<string, number>
}

export const adminApi = {
  listUsers(params?: { keyword?: string; role?: string; status?: string; page?: number; page_size?: number }): Promise<ApiResponse<{ items: AdminUser[]; total: number }>> {
    const query = new URLSearchParams()
    if (params?.keyword) query.set('keyword', params.keyword)
    if (params?.role) query.set('role', params.role)
    if (params?.status) query.set('status', params.status)
    if (params?.page) query.set('page', String(params.page))
    if (params?.page_size) query.set('page_size', String(params.page_size))
    const qs = query.toString()
    return request(`/admin/users${qs ? '?' + qs : ''}`)
  },

  getUser(userId: number): Promise<ApiResponse<AdminUser>> {
    return request(`/admin/users/${userId}`)
  },

  createUser(body: AdminUserCreate): Promise<ApiResponse<AdminUser>> {
    return request('/admin/users', { method: 'POST', body: JSON.stringify(body) })
  },

  updateUser(userId: number, body: AdminUserUpdate): Promise<ApiResponse<AdminUser>> {
    return request(`/admin/users/${userId}`, { method: 'PUT', body: JSON.stringify(body) })
  },

  disableUser(userId: number): Promise<ApiResponse<AdminUser>> {
    return request(`/admin/users/${userId}/disable`, { method: 'PATCH' })
  },

  enableUser(userId: number): Promise<ApiResponse<AdminUser>> {
    return request(`/admin/users/${userId}/enable`, { method: 'PATCH' })
  },
}

export interface AdminProvider {
  id: number
  name: string
  category: string
  is_enabled: boolean
  priority: number
}

export interface AdminModel {
  id: number
  display_name: string
  provider_id: number
  category: string
  model_name: string
  is_default: boolean
  is_enabled: boolean
  prompt_max_length: number
  version: string | null
  deploy_env: string
  deploy_status: string
  unit_points: number
  avg_latency_ms: number | null
  success_count: number
  fail_count: number
  last_deploy_time: string | null
  create_time: string
  update_time: string
}

export interface ModelMetrics {
  id: number
  model_name: string
  avg_latency_ms: number | null
  success_count: number
  fail_count: number
  success_rate: number
}

// 模型管理接口（M3）
export const adminApiModels = {
  listModels(params?: { category?: string; page?: number; page_size?: number }): Promise<ApiResponse<{ items: AdminModel[]; total: number }>> {
    const query = new URLSearchParams()
    if (params?.category) query.set('category', params.category)
    if (params?.page) query.set('page', String(params.page))
    if (params?.page_size) query.set('page_size', String(params.page_size))
    const qs = query.toString()
    return request(`/admin/models${qs ? '?' + qs : ''}`)
  },

  listProviders(): Promise<ApiResponse<{ items: AdminProvider[]; total: number }>> {
    return request('/admin/providers')
  },

  getModel(id: number): Promise<ApiResponse<AdminModel>> {
    return request(`/admin/models/${id}`)
  },

  updateModel(id: number, body: Partial<Pick<AdminModel, 'is_enabled' | 'version' | 'deploy_env' | 'unit_points' | 'display_name'>>): Promise<ApiResponse<AdminModel>> {
    return request(`/admin/models/${id}`, { method: 'PUT', body: JSON.stringify(body) })
  },

  setModelDeploy(id: number, deploy_status: string): Promise<ApiResponse<AdminModel>> {
    return request(`/admin/models/${id}/deploy`, { method: 'PUT', body: JSON.stringify({ deploy_status }) })
  },

  registerModelVersion(id: number, version: string, deploy_env: string): Promise<ApiResponse<AdminModel>> {
    return request(`/admin/models/${id}/versions`, { method: 'POST', body: JSON.stringify({ version, deploy_env }) })
  },

  getModelMetrics(id: number): Promise<ApiResponse<ModelMetrics>> {
    return request(`/admin/models/${id}/metrics`)
  },
}

export interface FeatureToggle {
  id: number
  code: string
  name: string
  enabled: boolean
  whitelist_user_ids: number[] | null
  description: string | null
  create_time: string
  update_time: string
}

export interface FeatureTogglePayload {
  code?: string
  name?: string
  enabled?: boolean
  whitelist_user_ids?: number[]
  description?: string
}

// 功能开关接口（M4）
export const adminApiFeatures = {
  listFeatures(): Promise<ApiResponse<{ items: FeatureToggle[]; total: number }>> {
    return request('/admin/features')
  },

  createFeature(body: FeatureTogglePayload): Promise<ApiResponse<FeatureToggle>> {
    return request('/admin/features', { method: 'POST', body: JSON.stringify(body) })
  },

  updateFeature(code: string, body: FeatureTogglePayload): Promise<ApiResponse<FeatureToggle>> {
    return request(`/admin/features/${code}`, { method: 'PUT', body: JSON.stringify(body) })
  },

  deleteFeature(code: string): Promise<ApiResponse<null>> {
    return request(`/admin/features/${code}`, { method: 'DELETE' })
  },
}

// ===== 积分费率模块（M5） =====
export interface PointsRate {
  id: number
  service_code: string
  multiplier: number
  rate_unit: string
  model_id: number | null
  enabled: boolean
  create_time: string
  update_time: string
  // 展示增强字段（后端算好下发）
  service_label?: string
  unit_label?: string
  model_display?: string | null
}

export interface PointsTransaction {
  id: number
  user_id: number
  tx_type: string
  points_delta: number
  service_code: string | null
  task_id: string | null
  model_id: number | null
  balance_after: number
  remark: string | null
  create_time: string
}

export interface PointsSummary {
  service: Array<{
    service_code: string
    consume: number
    recharge: number
    refund: number
    adjust: number
    tx_count: number
  }>
  daily: Array<{
    date: string
    consume: number
    recharge: number
    refund: number
    adjust: number
  }>
}

export const adminApiPoints = {
  listRates(serviceCode?: string): Promise<ApiResponse<{ items: PointsRate[]; total: number }>> {
    const q = serviceCode ? `?service_code=${encodeURIComponent(serviceCode)}` : ''
    return request(`/admin/points/rates${q}`)
  },

  createRate(body: { service_code: string; multiplier: number; rate_unit: string; model_id?: number | null; enabled?: boolean }): Promise<ApiResponse<PointsRate>> {
    return request('/admin/points/rates', { method: 'POST', body: JSON.stringify(body) })
  },

  updateRate(id: number, body: { multiplier?: number; rate_unit?: string; enabled?: boolean }): Promise<ApiResponse<PointsRate>> {
    return request(`/admin/points/rates/${id}`, { method: 'PUT', body: JSON.stringify(body) })
  },

  deleteRate(id: number): Promise<ApiResponse<null>> {
    return request(`/admin/points/rates/${id}`, { method: 'DELETE' })
  },

  recharge(body: { user_id: number; points_delta: number; remark?: string }): Promise<ApiResponse<{ user_id: number; username: string; points_delta: number; tx_type: string; balance_after: number }>> {
    return request('/admin/points/recharge', { method: 'POST', body: JSON.stringify(body) })
  },

  listTransactions(params: { user_id?: number; service_code?: string; tx_type?: string; page?: number; page_size?: number }): Promise<ApiResponse<{ items: PointsTransaction[]; total: number; page: number; page_size: number }>> {
    const qs = new URLSearchParams()
    if (params.user_id) qs.set('user_id', String(params.user_id))
    if (params.service_code) qs.set('service_code', params.service_code)
    if (params.tx_type) qs.set('tx_type', params.tx_type)
    qs.set('page', String(params.page || 1))
    qs.set('page_size', String(params.page_size || 20))
    return request(`/admin/points/transactions?${qs.toString()}`)
  },

  summary(): Promise<ApiResponse<PointsSummary>> {
    return request('/admin/points/summary')
  },

  listOrders(params: { username?: string; user_id?: number; service_code?: string; tx_type?: string; page?: number; page_size?: number }): Promise<ApiResponse<{ items: (PointsTransaction & { username: string })[]; total: number; page: number; page_size: number }>> {
    const qs = new URLSearchParams()
    if (params.username) qs.set('username', params.username)
    if (params.user_id) qs.set('user_id', String(params.user_id))
    if (params.service_code) qs.set('service_code', params.service_code)
    if (params.tx_type) qs.set('tx_type', params.tx_type)
    qs.set('page', String(params.page || 1))
    qs.set('page_size', String(params.page_size || 20))
    return request(`/admin/points/orders?${qs.toString()}`)
  },

  listModelPoints(): Promise<ApiResponse<{ items: ModelPoints[]; total: number }>> {
    return request('/admin/points/models')
  },

  updateModelPoints(id: number, unit_points: number): Promise<ApiResponse<{ id: number; display_name: string; unit_points: number }>> {
    return request(`/admin/points/models/${id}`, { method: 'PUT', body: JSON.stringify({ unit_points }) })
  },
}

export interface ModelPoints {
  id: number
  display_name: string
  category: string
  model_name: string
  unit_points: number
  success_count: number
  fail_count: number
  is_enabled: boolean
  deploy_status: string
}

// ===== 通知模块（M6） =====
export interface NotificationItem {
  token: string
  type: string
  title: string
  content: string
  extra_data: Record<string, unknown>
  is_read: boolean
  create_time: string
}

export const notifyMine = {
  history(params: { page?: number; page_size?: number; unread_only?: boolean } = {}): Promise<ApiResponse<{ items: NotificationItem[]; total: number; page: number; page_size: number }>> {
    const qs = new URLSearchParams()
    qs.set('page', String(params.page || 1))
    qs.set('page_size', String(params.page_size || 20))
    if (params.unread_only) qs.set('unread_only', 'true')
    return request(`/notify/history?${qs.toString()}`)
  },

  unreadCount(): Promise<ApiResponse<{ count: number }>> {
    return request('/notify/unread-count')
  },

  markRead(token: string): Promise<ApiResponse<NotificationItem>> {
    return request(`/notify/read/${token}`, { method: 'PATCH' })
  },

  markAllRead(): Promise<ApiResponse<{ mark_read: number }>> {
    return request('/notify/read-all', { method: 'PATCH' })
  },
}

export interface AdminNotificationItem extends NotificationItem {
  id: number
  user_id: number
  extra_data: Record<string, unknown>
}

export const adminApiNotify = {
  list(params: { page?: number; page_size?: number } = {}): Promise<ApiResponse<{ items: AdminNotificationItem[]; total: number; page: number; page_size: number }>> {
    const qs = new URLSearchParams()
    qs.set('page', String(params.page || 1))
    qs.set('page_size', String(params.page_size || 20))
    return request(`/admin/notifications?${qs.toString()}`)
  },

  broadcast(body: { type: string; title: string; content?: string; user_ids?: number[] | null }): Promise<ApiResponse<{ recipients: number }>> {
    return request('/admin/notifications/broadcast', { method: 'POST', body: JSON.stringify(body) })
  },
}

// ===== 报表模块（M7） =====
export interface AnalyticsOverview {
  total_users: number
  today_active_users: number
  cumulative_points_consumed: number
  weekly_success_rate: number
}

export const adminApiAnalytics = {
  overview(): Promise<ApiResponse<AnalyticsOverview>> {
    return request('/admin/analytics/overview')
  },

  users(days = 30): Promise<ApiResponse<{ dates: string[]; series: { new_users: number[]; dau: number[] } }>> {
    return request(`/admin/analytics/users?days=${days}`)
  },

  usage(): Promise<ApiResponse<{ dates: string[]; series: { chat_messages: number; chat_tokens: number; image_tasks: number; video_tasks: number } }>> {
    return request('/admin/analytics/usage')
  },

  points(days = 30): Promise<ApiResponse<{ dates: string[]; series: { points_consumed: number[] } }>> {
    return request(`/admin/analytics/points?days=${days}`)
  },

  performance(): Promise<ApiResponse<{ dates: string[]; series: { avg_latency_ms: number; task_success: number[]; task_failed: number[] } }>> {
    return request('/admin/analytics/performance')
  },

  services(): Promise<ApiResponse<{ dates: string[]; series: { services: Array<{ provider: string; model: string; success_count: number; fail_count: number; success_rate: number; deploy_status: string; avg_latency_ms: number | null }> } }>> {
    return request('/admin/analytics/services')
  },
}

// ===== 操作审计（M2） =====
export interface AuditLogItem {
  id: number
  operator: string
  admin_user_id: number
  module: string
  action: string
  target_id: string | null
  detail: Record<string, unknown> | null
  ip: string | null
  user_agent: string | null
  create_time: string
}

export const adminApiAudit = {
  list(params: { page?: number; page_size?: number; module?: string; operator?: string } = {}): Promise<ApiResponse<{ items: AuditLogItem[]; total: number; page: number; page_size: number }>> {
    const qs = new URLSearchParams()
    qs.set('page', String(params.page || 1))
    qs.set('page_size', String(params.page_size || 20))
    if (params.module) qs.set('module', params.module)
    if (params.operator) qs.set('operator', params.operator)
    return request(`/admin/audit-logs?${qs.toString()}`)
  },
}

export interface AdminConfigItem {
  key: string
  value: { title: string; content: string }
  update_time: string | null
}

export const adminApiConfig = {
  list(): Promise<ApiResponse<{ items: AdminConfigItem[]; total: number }>> {
    return request('/admin/configs')
  },
  getDocs(): Promise<ApiResponse<{ key: string; value: { title: string; content: string } }>> {
    return request('/config/item?key=api-docs')
  },
  updateDocs(value: { title: string; content: string }): Promise<ApiResponse<{ key: string; value: { title: string; content: string } }>> {
    return request('/admin/configs/api-docs', {
      method: 'PUT',
      body: JSON.stringify({ value }),
    })
  },
  set(key: string, value: unknown): Promise<ApiResponse<{ key: string; value: unknown }>> {
    return request(`/admin/configs/${key}`, {
      method: 'PUT',
      body: JSON.stringify({ value }),
    })
  },
}

// ===== 图片上传（可作独立图床） =====
export interface UploadConfig {
  max_size_mb: number
  max_count: number
}

export interface UploadResult {
  url: string
  file_name: string
  size: number
  content_type: string
}

export const apiUpload = {
  getConfig(): Promise<ApiResponse<UploadConfig>> {
    return request('/upload/image/config')
  },
  uploadImage(file: File): Promise<ApiResponse<UploadResult>> {
    const form = new FormData()
    form.append('file', file)
    return request('/upload/image', { method: 'POST', body: form })
  },
}

// ===== 用户调用记录 =====
export interface CallRecordItem {
  service_code: string
  kind: 'task' | 'chat'
  ref_id: string
  user_id: number
  username: string
  model_name: string | null
  title: string
  status: string
  message_count: number | null
  points: number | null
  create_time: string
}

export const adminApiRecords = {
  list(params: {
    user_id?: number
    username?: string
    service_code?: string
    start?: string
    end?: string
    page?: number
    page_size?: number
  } = {}): Promise<ApiResponse<{ items: CallRecordItem[]; total: number; page: number; page_size: number }>> {
    const qs = new URLSearchParams()
    if (params.user_id) qs.set('user_id', String(params.user_id))
    if (params.username) qs.set('username', params.username)
    if (params.service_code) qs.set('service_code', params.service_code)
    if (params.start) qs.set('start', params.start)
    if (params.end) qs.set('end', params.end)
    qs.set('page', String(params.page || 1))
    qs.set('page_size', String(params.page_size || 20))
    return request(`/admin/records?${qs.toString()}`)
  },
}