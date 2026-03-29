<template>
  <div class="dashboard">
    <el-row :gutter="16">
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover">
          <div class="stat">
            <span class="num">{{ classCount }}</span>
            <span class="label">我的班级</span>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="16">
        <el-card shadow="hover">
          <h3>快速开始</h3>
          <p class="hint">创建班级后会生成班级码，学生凭班级码加入后即可发布随堂测试。</p>
          <el-button type="primary" @click="$router.push({ name: 'teacher-classes' })">进入班级管理</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchClasses } from '@/api/teacher'

const classCount = ref(0)

onMounted(async () => {
  try {
    const res = await fetchClasses()
    classCount.value = res.data?.classes?.length ?? 0
  } catch {
    classCount.value = 0
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 960px;
}
.stat {
  text-align: center;
  padding: 8px 0;
}
.num {
  display: block;
  font-size: 32px;
  font-weight: 700;
  color: #409eff;
}
.label {
  color: #606266;
  font-size: 14px;
}
h3 {
  margin-top: 0;
}
.hint {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 16px;
}
</style>
