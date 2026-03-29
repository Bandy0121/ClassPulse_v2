<template>
  <div>
    <h2>测试历史</h2>
    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column prop="title" label="测试" />
      <el-table-column prop="class_name" label="班级" />
      <el-table-column label="得分" width="120">
        <template #default="{ row }">{{ row.score }} / {{ row.max_score }}</template>
      </el-table-column>
      <el-table-column prop="correct_count" label="正确" width="72" />
      <el-table-column prop="wrong_count" label="错误" width="72" />
      <el-table-column prop="submitted_at" label="提交时间" width="170" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="goResult(row.assessment_id)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchHistory } from '@/api/student'

const router = useRouter()
const loading = ref(false)
const list = ref([])

async function load() {
  loading.value = true
  try {
    const res = await fetchHistory()
    list.value = res.data?.history ?? []
  } catch (e) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function goResult(id) {
  router.push({ name: 'student-assessment-result', params: { id } })
}

onMounted(load)
</script>

<style scoped>
h2 {
  margin-top: 0;
}
</style>
