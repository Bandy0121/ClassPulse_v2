<template>
  <div v-loading="loading">
    <h2>学习概览</h2>
    <el-row v-if="overview" :gutter="16" class="row">
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover"><div class="n">{{ overview.total_checkins }}</div><div class="l">签到次数</div></el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover"><div class="n">{{ overview.completed_assessments }}</div><div class="l">完成测试</div></el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover"><div class="n">{{ overview.average_score }}%</div><div class="l">平均得分率</div></el-card>
      </el-col>
      <el-col :xs="12" :sm="6">
        <el-card shadow="hover">
          <el-button type="success" @click="$router.push({ name: 'student-classes' })">我的班级</el-button>
        </el-card>
      </el-col>
    </el-row>
    <el-card v-if="subjects?.length" shadow="never" class="mt">
      <template #header>按班级</template>
      <el-table :data="subjects" size="small">
        <el-table-column prop="class_name" label="班级" />
        <el-table-column prop="assessment_count" label="测试数" width="90" />
        <el-table-column prop="average_score" label="平均得分率%" width="120" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchStudentStatistics } from '@/api/stats'

const loading = ref(false)
const overview = ref(null)
const subjects = ref([])

onMounted(async () => {
  loading.value = true
  try {
    const res = await fetchStudentStatistics()
    overview.value = res.data?.overview ?? null
    subjects.value = res.data?.subjects ?? []
  } catch (e) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
h2 {
  margin-top: 0;
}
.row {
  margin-bottom: 8px;
}
.n {
  font-size: 24px;
  font-weight: 700;
  color: #67c23a;
}
.l {
  font-size: 13px;
  color: #909399;
}
.mt {
  margin-top: 16px;
}
</style>
