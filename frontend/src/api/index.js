/**
 * FinGuard API 网关
 *
 * 双模式设计：
 * 1. 后端在线 → 代理到 FastAPI
 * 2. 后端离线 → 自动 fallback 到 Mock 数据
 *
 * 首次请求检测后端状态，之后缓存结果。
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'
import { mockApis } from './mock'

// ========== 后端状态检测 ==========

let _backendAvailable = null  // null=未检测, true=在线, false=离线
let _detecting = false
let _detectQueue = []

async function detectBackend() {
  if (_backendAvailable !== null) return _backendAvailable
  if (_detecting) {
    // 排队等待检测结果
    return new Promise((resolve) => {
      _detectQueue.push(resolve)
    })
  }
  _detecting = true
  try {
    const resp = await axios.get('/api/health', { timeout: 3000 })
    _backendAvailable = resp.status === 200
  } catch {
    _backendAvailable = false
    console.log('[FinGuard] 后端未检测到，启用 Mock 数据模式')
  }
  _detecting = false
  _detectQueue.forEach(r => r(_backendAvailable))
  _detectQueue = []
  return _backendAvailable
}

// ========== 真正的 Axios 实例 ==========

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('fg_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('fg_token')
      window.location.href = '/login'
    }
    // Mock 模式不报错（由调用方处理 fallback）
    return Promise.reject(error)
  }
)

// ========== 带 Mock Fallback 的统一调用 ==========

async function withFallback(mockFn, ...args) {
  const available = await detectBackend()
  if (available) {
    try {
      // 构造匹配真实 API 的调用
      const [method, url, ...rest] = args
      const response = await api[method](url, ...rest)
      return response
    } catch {
      // 真实 API 失败，fallback 到 mock
      console.log('[FinGuard] API 请求失败，fallback 到 Mock')
    }
  }
  // Mock 模式
  const result = await mockFn(...args.slice(1))
  return result
}

// 特殊处理 upload（FormData，需用 post）
async function withFallbackUpload(mockFn, url, formData) {
  const available = await detectBackend()
  if (available) {
    try {
      return await api.post(url, formData)
    } catch { /* fallback */ }
  }
  return await mockFn(formData)
}

// ========== API 方法 ==========

export const documentApi = {
  upload: (formData) => withFallbackUpload(mockApis.uploadDocument, '/documents/upload', formData),
  list: (params) => withFallback(mockApis.listDocuments, 'get', '/documents', { params }),
  get: (id) => withFallback(mockApis.getDocument, 'get', `/documents/${id}`, id),
}

export const reviewApi = {
  create: (data) => withFallback(mockApis.createReview, 'post', '/reviews', {}, { params: data }),
  start: (id) => withFallback(mockApis.startReview, 'post', `/reviews/${id}/start`, id),
  list: (params) => withFallback(mockApis.listReviews, 'get', '/reviews', { params }),
  get: (id) => withFallback(mockApis.getReview, 'get', `/reviews/${id}`, id),
  confirm: (id, action, comment) =>
    withFallback(mockApis.confirmReview, 'post', `/reviews/${id}/confirm`, id, action, comment),
}

export const knowledgeApi = {
  upload: (formData) => withFallbackUpload(mockApis.uploadRegulation, '/knowledge/regulations/upload', formData),
  list: (params) => withFallback(mockApis.listRegulations, 'get', '/knowledge/regulations', { params }),
  search: (query, top_k = 5) =>
    withFallback(mockApis.searchRegulations, 'post', '/knowledge/search', query, top_k),
}

export const healthApi = {
  check: () => detectBackend(),
}

export default api
