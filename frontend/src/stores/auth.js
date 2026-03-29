/**
 * 认证状态管理 (Pinia Store)
 *
 * 本文件用于管理应用的认证状态，包括：
 * 1. 用户登录状态
 * 2. 用户信息
 * 3. AccessToken 和 RefreshToken
 *
 * Pinia 是 Vue 3 的官方状态管理库，用于替代 Vuex
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// 从 localStorage 获取存储的数据
function getStorageItem(key) {
  try {
    const item = localStorage.getItem(key)
    return item ? JSON.parse(item) : null
  } catch (e) {
    console.error('获取存储数据失败:', e)
    return null
  }
}

// 将数据存储到 localStorage
function setStorageItem(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch (e) {
    console.error('存储数据失败:', e)
  }
}

// 从 localStorage 移除数据
function removeStorageItem(key) {
  try {
    localStorage.removeItem(key)
  } catch (e) {
    console.error('移除存储数据失败:', e)
  }
}

/**
 * 使用 defineStore 定义认证 store
 *
 * 第一个参数：store 的唯一 ID（在应用中必须唯一）
 * 第二个参数：包含 state 和 actions 的配置对象
 */
export const useAuthStore = defineStore('auth', () => {
  // ==================== 状态 (State) ====================
  // 使用 ref 定义响应式状态

  // 用户信息
  // 结构：{ id, username, email, realName, userType, token, refreshToken }
  const user = ref(null)

  // 是否正在加载
  const loading = ref(false)

  // ==================== 计算属性 (Getters) ====================
  // 使用 computed 计算派生状态

  // 检查用户是否已登录
  const isLoggedIn = computed(() => {
    return user.value !== null && !!user.value.token
  })

  // 获取当前用户类型
  const userType = computed(() => {
    return user.value ? user.value.userType : null
  })

  // 获取当前用户 ID
  const userId = computed(() => {
    return user.value ? user.value.id : null
  })

  // ==================== 动作 (Actions) ====================
  // 定义可异步的操作

  /**
   * 处理登录成功
   *
   * @param {Object} data - 登录返回的数据
   * @param {String} data.token - 访问令牌
   * @param {String} data.refreshToken - 刷新令牌
   * @param {Object} data.user - 用户信息
   */
  function handleLoginSuccess(data) {
    // 设置用户信息
    user.value = {
      id: data.user.id,
      username: data.user.username,
      email: data.user.email,
      realName: data.user.real_name,
      userType: data.userType || (data.user.student_id ? 'student' : 'teacher'),
      token: data.token,
      refreshToken: data.refresh_token || data.refreshToken
    }

    // 保存到 localStorage（持久化登录状态）
    setStorageItem('user', user.value)
  }

  /**
   * 教师登录
   *
   * @param {Object} formData - 登录表单数据
   * @param {String} formData.username - 用户名
   * @param {String} formData.password - 密码
   * @returns {Promise} - 登录结果
   */
  async function teacherLogin(formData) {
    loading.value = true
    try {
      const response = await fetch('/api/auth/teacher/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      const result = await response.json()

      if (result.code === 200) {
        handleLoginSuccess({
          ...result.data,
          userType: 'teacher'
        })
        return { success: true }
      } else {
        return { success: false, message: result.message }
      }
    } catch (error) {
      console.error('登录失败:', error)
      return { success: false, message: '网络错误，请稍后重试' }
    } finally {
      loading.value = false
    }
  }

  /**
   * 学生登录
   *
   * @param {Object} formData - 登录表单数据
   * @param {String} formData.username - 用户名
   * @param {String} formData.password - 密码
   * @returns {Promise} - 登录结果
   */
  async function studentLogin(formData) {
    loading.value = true
    try {
      const response = await fetch('/api/auth/student/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      const result = await response.json()

      if (result.code === 200) {
        handleLoginSuccess({
          ...result.data,
          userType: 'student'
        })
        return { success: true }
      } else {
        return { success: false, message: result.message }
      }
    } catch (error) {
      console.error('登录失败:', error)
      return { success: false, message: '网络错误，请稍后重试' }
    } finally {
      loading.value = false
    }
  }

  /**
   * 教师注册
   *
   * @param {Object} formData - 注册表单数据
   * @returns {Promise} - 注册结果
   */
  async function teacherRegister(formData) {
    loading.value = true
    try {
      const response = await fetch('/api/auth/teacher/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      const result = await response.json()

      if (result.code === 201) {
        return { success: true, message: result.message }
      } else {
        return { success: false, message: result.message }
      }
    } catch (error) {
      console.error('注册失败:', error)
      return { success: false, message: '网络错误，请稍后重试' }
    } finally {
      loading.value = false
    }
  }

  /**
   * 学生注册
   *
   * @param {Object} formData - 注册表单数据
   * @returns {Promise} - 注册结果
   */
  async function studentRegister(formData) {
    loading.value = true
    try {
      const response = await fetch('/api/auth/student/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      })

      const result = await response.json()

      if (result.code === 201) {
        return { success: true, message: result.message }
      } else {
        return { success: false, message: result.message }
      }
    } catch (error) {
      console.error('注册失败:', error)
      return { success: false, message: '网络错误，请稍后重试' }
    } finally {
      loading.value = false
    }
  }

  /**
   * 检查认证状态
   *
   * 从 localStorage 恢复登录状态
   */
  function checkAuthStatus() {
    const storedUser = getStorageItem('user')

    if (storedUser && storedUser.token) {
      user.value = storedUser
    }
  }

  /**
   * 退出登录
   *
   * 清除用户信息和令牌
   */
  async function logout() {
    loading.value = true
    try {
      // 调用后端退出接口（可选）
      if (user.value && user.value.token) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${user.value.token}`
          }
        }).catch(() => {})
      }
    } catch (error) {
      console.error('退出登录失败:', error)
    } finally {
      user.value = null
      removeStorageItem('user')
      removeStorageItem('token')
      removeStorageItem('refreshToken')
      loading.value = false
    }
  }

  /**
   * 刷新访问令牌
   *
   * 使用刷新令牌获取新的访问令牌
   * @returns {Promise<Boolean>} - 是否成功
   */
  async function refreshAccessToken() {
    const storedUser = getStorageItem('user')

    if (!storedUser || !storedUser.refreshToken) {
      return false
    }

    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${storedUser.refreshToken}`
        }
      })

      const result = await response.json()

      if (result.code === 200) {
        // 更新存储的用户信息
        storedUser.token = result.data.token
        setStorageItem('user', storedUser)
        user.value = storedUser
        return true
      } else {
        // 刷新失败，退出登录
        await logout()
        return false
      }
    } catch (error) {
      console.error('刷新令牌失败:', error)
      return false
    }
  }

  /**
   * 获取当前用户信息
   * @returns {Promise<Object|null>} - 用户信息
   */
  async function getCurrentUserProfile() {
    const storedUser = getStorageItem('user')

    if (!storedUser || !storedUser.token) {
      return null
    }

    try {
      const endpoint = storedUser.userType === 'teacher'
        ? '/api/auth/teacher/me'
        : '/api/auth/student/me'

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${storedUser.token}`
        }
      })

      const result = await response.json()

      if (result.code === 200) {
        // 更新存储的用户信息
        storedUser.email = result.data.email
        storedUser.realName = result.data.real_name
        setStorageItem('user', storedUser)
        user.value = storedUser
        return result.data
      } else {
        return null
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
      return null
    }
  }

  // ==================== 返回 Store 的公共成员 ====================
  return {
    // State
    user,
    loading,

    // Getters
    isLoggedIn,
    userType,
    userId,

    // Actions
    teacherLogin,
    studentLogin,
    teacherRegister,
    studentRegister,
    checkAuthStatus,
    logout,
    refreshAccessToken,
    getCurrentUserProfile
  }
})
