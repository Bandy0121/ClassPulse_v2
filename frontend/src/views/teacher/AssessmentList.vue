<template>
  <div>
    <el-page-header @back="$router.push({ name: 'teacher-class-detail', params: { id: cid } })">
      <template #content>
        <span class="title">测试列表</span>
      </template>
    </el-page-header>
    <div class="toolbar">
      <el-button type="primary" @click="goCreate">创建测试</el-button>
    </div>
    <el-table v-loading="loading" :data="list" stripe>
      <el-table-column prop="title" label="标题" min-width="160" />
      <el-table-column prop="question_count" label="题目" width="72" />
      <el-table-column label="状态" width="88">
        <template #default="{ row }">
          <el-tag :type="row.is_published ? 'success' : 'info'" size="small">
            {{ row.is_published ? '已发布' : '草稿' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="start_time" label="开始" width="160" />
      <el-table-column prop="end_time" label="结束" width="160" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="goStats(row.id)">统计</el-button>
          <el-button v-if="!row.is_published" link type="success" @click="doPublish(row)">发布</el-button>
          <el-button link type="danger" @click="doDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchClassAssessments, publishAssessment, deleteAssessment } from '@/api/teacher'

const props = defineProps({
  id: { type: [String, Number], required: true }
})

const router = useRouter()
const loading = ref(false)
const list = ref([])
const cid = computed(() => Number(props.id))

async function load() {
  if (!cid.value) return
  loading.value = true
  try {
    const res = await fetchClassAssessments(cid.value)
    list.value = res.data?.assessments ?? []
  } catch (e) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function goCreate() {
  router.push({ name: 'teacher-assessment-create', params: { id: cid.value } })
}

function goStats(aid) {
  router.push({ name: 'teacher-statistics', params: { id: aid } })
}

async function doPublish(row) {
  if (row.question_count < 1) {
    ElMessage.warning('请先添加至少一道题目')
    return
  }
  try {
    await publishAssessment(row.id, true)
    ElMessage.success('已发布')
    await load()
  } catch (e) {
    ElMessage.error(e?.message || '发布失败')
  }
}

async function doDelete(row) {
  await ElMessageBox.confirm('将删除该测试及全部题目与作答记录，确定？', '确认', { type: 'warning' })
  try {
    await deleteAssessment(row.id)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.message || '删除失败')
  }
}

watch(() => props.id, load, { immediate: true })
</script>

<style scoped>
.title {
  font-size: 18px;
  font-weight: 600;
}
.toolbar {
  margin: 16px 0;
}
</style>
