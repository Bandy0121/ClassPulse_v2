/**
 * Axios 实例与通用请求封装（Vite ESM 环境）
 */
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

httpClient.interceptors.request.use(
  (config) => {
    const store = useAuthStore()
    const token = store.user?.token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

httpClient.interceptors.response.use(
  (response) => {
    const result = response.data
    if (result.code === 200 || result.code === 201) {
      return result
    }
    if (result.code === 401) {
      handleUnauthorized()
      return Promise.reject(result)
    }
    return Promise.reject(result)
  },
  (error) => {
    if (!error.response) {
      return Promise.reject({ message: '网络错误，请检查网络连接' })
    }
    const body = error.response.data
    const backendMsg = body && typeof body === 'object' && body.message
    if (backendMsg) {
      return Promise.reject({ message: backendMsg, code: body.code, data: body.data })
    }
    const status = error.response.status
    const messages = {
      400: '请求参数错误',
      403: '没有权限访问此资源',
      404: '请求的资源不存在',
      500: '服务器内部错误'
    }
    return Promise.reject({ message: messages[status] || '请求失败' })
  }
)

function handleUnauthorized() {
  const store = useAuthStore()
  if (store.user?.refreshToken) {
    store.refreshAccessToken().then((ok) => {
      if (!ok) {
        store.logout()
      }
    })
  } else {
    store.logout()
  }
}

export function get(url, params = {}, config = {}) {
  return httpClient.get(url, { params, ...config })
}

export function post(url, data = {}, config = {}) {
  return httpClient.post(url, data, config)
}

export function put(url, data = {}, config = {}) {
  return httpClient.put(url, data, config)
}

export function del(url, params = {}, config = {}) {
  return httpClient.delete(url, { params, ...config })
}

export function patch(url, data = {}, config = {}) {
  return httpClient.patch(url, data, config)
}

export { httpClient }

export default {
  get,
  post,
  put,
  del,
  patch
}
