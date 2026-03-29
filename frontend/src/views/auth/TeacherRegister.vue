<template>
  <div class="page">
    <el-card class="card" shadow="hover">
      <h2>教师注册</h2>
      <p class="sub">ClassPulse 教师账号</p>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="88px" size="large">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="3–50 个字符" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="name@example.com" clearable />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="用于课堂展示" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="submit">注册</el-button>
        </el-form-item>
      </el-form>
      <div class="footer">
        <el-link type="primary" @click="$router.push({ name: 'teacher-login' })">返回登录</el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  email: '',
  real_name: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }]
}

async function submit() {
  await formRef.value?.validate()
  loading.value = true
  try {
    const res = await auth.teacherRegister({
      username: form.username,
      password: form.password,
      email: form.email,
      real_name: form.real_name
    })
    if (res.success) {
      ElMessage.success(res.message || '注册成功，请登录')
      await router.push({ name: 'teacher-login' })
    } else {
      ElMessage.error(res.message || '注册失败')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #66b7ff 0%, #3285ff 100%);
}
.card {
  width: 420px;
  padding: 8px 8px 16px;
}
h2 {
  margin: 0 0 4px;
  text-align: center;
}
.sub {
  text-align: center;
  color: #909399;
  font-size: 14px;
  margin-bottom: 24px;
}
.footer {
  text-align: center;
}
</style>
