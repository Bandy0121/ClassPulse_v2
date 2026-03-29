<template>
  <div>
    <h2>随堂测试</h2>
    <el-tabs>
      <el-tab-pane label="进行中 / 未开始">
        <el-table :data="available" stripe>
          <el-table-column prop="title" label="测试" />
          <el-table-column prop="class_name" label="班级" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'in_progress' ? 'success' : 'warning'" size="small">
                {{ row.status === 'in_progress' ? '进行中' : '未开始' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="start_time" label="开始" width="160" />
          <el-table-column prop="end_time" label="结束" width="160" />
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'in_progress'"
                type="primary"
                link
                @click="goTake(row.id)"
              >去答题</el-button>
              <span v-else class="muted">未到时间</span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="已结束">
        <el-table :data="completed" stripe>
          <el-table-column prop="title" label="测试" />
          <el-table-column prop="class_name" label="班级" />
          <el-table-column label="得分" width="120">
            <template #default="{ row }">
              <span v-if="row.score != null">{{ row.score }} / {{ row.max_score }}</span>
              <span v-else class="muted">未参加</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.score != null"
                type="primary"
                link
                @click="goResult(row.id)"
              >查看结果</el-button>
              <span v-else class="muted">—</span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchAssessments } from '@/api/student'

const router = useRouter()
const available = ref([])
const completed = ref([])

async function load() {
  try {
    const res = await fetchAssessments()
    available.value = res.data?.available ?? []
    completed.value = res.data?.completed ?? []
  } catch (e) {
    ElMessage.error(e?.message || '加载失败')
  }
}

function goTake(id) {
  router.push({ name: 'student-assessment-take', params: { id } })
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
.muted {
  color: #909399;
  font-size: 13px;
}
</style>
