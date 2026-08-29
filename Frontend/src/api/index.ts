const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const API_PREFIX = '/api/v1'

interface ApiResponse<T = any> {
  code: number
  msg: string
  data: T
}

function getToken(): string | null {
  return localStorage.getItem('leafai_token')
}

async function request<T = any>(url: string, options?: RequestInit): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
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

  listTasks(params?: { status?: string; page?: number; page_size?: number }): Promise<ApiResponse<{ tasks: TaskStatusResult[]; total: number }>> {
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

  listChatSessions(): Promise<ApiResponse<{ sessions: Array<{ id: string; title: string; create_time: string; update_time: string }>; total: number }>> {
    return request('/chat/sessions')
  },

  getChatSessionMessages(sessionId: string): Promise<ApiResponse<Array<{ id: number; session_id: string; role: string; content: string; create_time: string }>>> {
    return request(`/chat/sessions/${sessionId}/messages`)
  },

  getModels(category?: string): Promise<ApiResponse<any>> {
    const query = category ? `?category=${category}` : ''
    return request(`/admin/models${query}`)
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

  getMe(): Promise<ApiResponse<{ id: number; user_id: string; username: string; email: string | null; is_active: boolean; is_superuser: boolean }>> {
    return request('/auth/me')
  },
}