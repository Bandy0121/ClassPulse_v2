<template>
  <div v-loading="loading">
    <el-page-header @back="goBack">
      <template #content>
        <span class="title">测试统计</span>
      </template>
    </el-page-header>

    <el-descriptions v-if="info" :column="2" border class="desc" :title="info.title">
      <el-descriptions-item label="题目数">{{ questions.length }}</el-descriptions-item>
      <el-descriptions-item label="有作答记录学生">{{ students.length }} / {{ info.total_students }}</el-descriptions-item>
    </el-descriptions>

    <h3>各题正确率</h3>
    <div ref="chartRef" class="chart" />

    <h3>学生成绩</h3>
    <el-table :data="students" stripe size="small">
      <el-table-column prop="real_name" label="姓名" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column label="得分">
        <template #default="{ row }">{{ row.score }} / {{ row.max_score }}</template>
      </el-table-column>
      <el-table-column prop="correct_count" label="正确" width="72" />
      <el-table-column prop="wrong_count" label="错误" width="72" />
    </el-table>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { fetchAssessmentStatistics } from '@/api/teacher'

const props = defineProps({
  id: { type: [String, Number], required: true }
})

const router = useRouter()
const loading = ref(false)
const info = ref(null)
const questions = ref([])
const students = ref([])
const chartRef = ref()
let chart

const aid = () => Number(props.id)

async function load() {
  if (!aid()) return
  loading.value = true
  try {
    const res = await fetchAssessmentStatistics(aid())
    const d = res.data
    info.value = d?.assessment_info ?? null
    questions.value = d?.question_statistics ?? []
    students.value = d?.student_summary ?? []
    await nextTick()
    renderChart()
  } catch (e) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value)
  }
  const labels = questions.value.map((_, i) => `第${i + 1}题`)
  const rates = questions.value.map((q) => q.correct_rate)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    series: [{ type: 'bar', data: rates, itemStyle: { color: '#409eff' } }]
  })
}

function goBack() {
  router.back()
}

watch(() => props.id, load, { immediate: true })

function onResize() {
  chart?.resize()
}

onMounted(() => {
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.title {
  font-size: 18px;
  font-weight: 600;
}
.desc {
  margin: 16px 0;
}
.chart {
  width: 100%;
  height: 320px;
  margin-bottom: 24px;
}
h3 {
  margin: 16px 0 12px;
  font-size: 16px;
}
</style>
