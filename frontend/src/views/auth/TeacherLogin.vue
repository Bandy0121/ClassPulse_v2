<template>
  <div class="login-container">
    <el-card class="login-card" shadow="hover">
      <!-- 登录表单 -->
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        size="large"
      >
        <div class="login-header">
          <h2>教师登录</h2>
          <p>ClassPulse - 学生课堂测试反馈系统</p>
        </div>

        <!-- 用户名输入框 -->
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            clearable
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <!-- 密码输入框 -->
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <!-- 登录按钮 -->
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            plain
            round
            size="large"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>

        <!-- 底部链接 -->
        <div class="login-footer">
          <span>还没有账号？</span>
          <el-link type="primary" @click="goToRegister">
            立即注册
          </el-link>
        </div>
      </el-form>

      <!-- 快速导航 -->
      <div class="quick-nav">
        <el-link type="info" @click="goToStudentLogin">
          学生登录
        </el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
/**
 * TeacherLogin.vue - 教师登录页面
 *
 * 本页面提供教师用户登录功能
 */

import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ElIcon } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

// ==================== 表单数据 ====================
// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
})

// 表单引用（用于验证）
const loginFormRef = ref()

// ==================== 验证规则 ====================
// 用户名验证规则
const usernameRules = [
  {
    required: true,
    message: '请输入用户名',
    trigger: 'blur'
  },
  {
    min: 3,
    max: 50,
    message: '用户名长度在 3 到 50 个字符之间',
    trigger: 'blur'
  }
]

// 密码验证规则
const passwordRules = [
  {
    required: true,
    message: '请输入密码',
    trigger: 'blur'
  },
  {
    min: 6,
    max: 128,
    message: '密码长度在 6 到 128 个字符之间',
    trigger: 'blur'
  }
]

// 验证规则集合
const loginRules = {
  username: usernameRules,
  password: passwordRules
}

// ==================== 状态 ====================
// 加载状态
const loading = ref(false)

// ==================== 方法 ====================
/**
 * 处理登录
 */
const handleLogin = async () => {
  const form = loginFormRef.value
  if (!form) return

  try {
    await form.validate()

    loading.value = true

    const result = await auth.teacherLogin(loginForm)

    if (result.success) {
      ElMessage.success('登录成功')
      const redirect = router.currentRoute.value.query.redirect
      await router.push(typeof redirect === 'string' && redirect ? redirect : { name: 'teacher-dashboard' })
    } else {
      // 登录失败
      ElMessage.error(result.message || '登录失败，请检查用户名和密码')
    }
  } catch (error) {
    console.error('登录验证错误:', error)
    ElMessage.error('表单验证失败')
  } finally {
    // 清除加载状态
    loading.value = false
  }
}

/**
 * 跳转到注册页面
 */
const goToRegister = () => {
  router.push({ name: 'teacher-register' })
}

/**
 * 跳转到学生登录页面
 */
const goToStudentLogin = () => {
  router.push({ name: 'student-login' })
}
</script>

<style scoped>
/* ==================== 样式 ==================== */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #66b7ff 0%, #3285ff 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.login-header h2 {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 10px;
}

.login-header p {
  font-size: 14px;
  color: #909399;
}

.login-form {
  margin-top: 20px;
}

.login-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  font-size: 14px;
  color: #606266;
}

.quick-nav {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
  color: #909399;
}

:deep(.el-link) {
  margin-left: 5px;
}
</style>
