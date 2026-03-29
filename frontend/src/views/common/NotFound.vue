// NotFound.vue - 404 页面

<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <h1>404</h1>
      <p>页面不存在</p>
      <p>您访问的页面可能已被删除或不存在</p>
      <el-button type="primary" @click="goBack">
        返回上一页
      </el-button>
      <el-button @click="goHome">
        回到主页
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

// 返回上一页
const goBack = () => {
  router.back()
}

// 回到主页
const goHome = () => {
  router.push({ name: 'teacher-login' })
}
</script>

<style scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f0f2f5;
}

.not-found-content {
  text-align: center;
}

.not-found-content h1 {
  font-size: 72px;
  color: #409eff;
  margin-bottom: 20px;
}

.not-found-content p {
  font-size: 18px;
  color: #606266;
  margin-bottom: 10px;
}

.not-found-content .el-button {
  margin-top: 20px;
  margin-right: 10px;
}
</style>
