<template>
  <div v-loading="loading">
    <el-page-header @back="$router.push({ name: 'teacher-class-detail', params: { id: cid } })">
      <template #content>
        <span class="title">班级综合统计</span>
      </template>
    </el-page-header>

    <el-descriptions v-if="classInfo" :column="2" border class="desc" :title="classInfo.name">
      <el-descriptions-item label="学生人数">{{ classInfo.student_count }}</el-descriptions-item>
    </el-descriptions>

    <el-row v-if="checkin" :gutter="16" class="cards">
      <el-col :xs="24" :sm="6">
        <el-card shadow="hover">
          <div class="card-title">累计签到人次</div>
          <div class="card-num">{{ checkin.total }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="6">
        <el-card shadow="hover">
          <div class="card-title">曾签到学生数</div>
          <div class="card-num">{{ checkin.checked_in }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="6">
        <el-card shadow="hover">
          <div class="card-title">历史覆盖率</div>
          <div class="card-num">{{ checkin.rate }}%</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="6">
        <el-card shadow="hover">
          <div class="card-title">今日本班签到 / 覆盖率</div>
          <div class="card-num sub">{{ checkin.today_count ?? 0 }} / {{ checkin.today_rate ?? 0 }}%</div>
        </el-card>
      </el-col>
    </el-row>

    <template v-if="checkinByDay.length">
      <h3>近14日签到人次（本班，按东八区自然日）</h3>
      <el-table :data="checkinByDay" size="small" stripe max-height="280" class="day-table">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="count" label="人次" width="100" />
      </el-table>
    </template>

    <el-row v-if="assessment" :gutter="16" class="cards">
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover">
          <div class="card-title">测试数量</div>
          <div class="card-num">{{ assessment.total }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover">
          <div class="card-title">有成绩记录人次</div>
          <div class="card-num">{{ assessment.completed }}</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="8">
        <el-card shadow="hover">
          <div class="card-title">平均分 / 及格率</div>
          <div class="card-num sub">{{ assessment.average_score }} / {{ assessment.pass_rate }}%</div>
        </el-card>
      </el-col>
    </el-row>

    <h3>成绩分布</h3>
    <div ref="chartRef" class="chart" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { fetchClassStatistics } from '@/api/stats'

const props = defineProps({
  id: { type: [String, Number], required: true }
})

const loading = ref(false)
const classInfo = ref(null)
const checkin = ref(null)
const assessment = ref(null)
const distribution = ref([])

const checkinByDay = computed(() => {
  const rows = checkin.value?.by_day
  return Array.isArray(rows) ? rows : []
})

const cid = computed(() => Number(props.id))

const chartRef = ref()
let chart

function onResize() {
  chart?.resize()
}

async function load() {
  if (!cid.value) return
  loading.value = true
  try {
    const res = await fetchClassStatistics(cid.value)
    const d = res.data
    classInfo.value = d?.class_info ?? null
    checkin.value = d?.checkin_stats ?? null
    assessment.value = d?.assessment_stats ?? null
    distribution.value = d?.score_distribution ?? []
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
  const labels = distribution.value.map((x) => x.range)
  const counts = distribution.value.map((x) => x.count)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        type: 'bar',
        data: counts,
        itemStyle: { color: '#67c23a' },
        label: { show: true, position: 'top' }
      }
    ]
  })
}

watch(() => props.id, load, { immediate: true })

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
.cards {
  margin-bottom: 16px;
}
.card-title {
  font-size: 13px;
  color: #909399;
}
.card-num {
  font-size: 26px;
  font-weight: 700;
  color: #409eff;
  margin-top: 8px;
}
.card-num.sub {
  font-size: 20px;
}
h3 {
  margin: 20px 0 12px;
  font-size: 16px;
}
.chart {
  width: 100%;
  height: 300px;
}
</style>
