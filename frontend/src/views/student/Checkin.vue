<template>
  <div>
    <h2>课堂签到</h2>
    <p class="hint">
      选择班级后签到。同一班级在每个自然日（按北京时间）仅可签到一次；当天仍可在其他已加入的班级分别签到。系统将尝试获取您的地理位置（可选）。
    </p>
    <el-form label-width="88px" style="max-width: 480px">
      <el-form-item label="班级">
        <el-select v-model="classId" placeholder="请选择" filterable style="width: 100%">
          <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="success" :loading="loading" @click="doCheckin">签到</el-button>
      </el-form-item>
    </el-form>

    <h3>我的签到记录</h3>
    <el-table v-loading="histLoading" :data="checkins" size="small" stripe>
      <el-table-column prop="class_name" label="班级" />
      <el-table-column prop="timestamp" label="时间" width="170" />
      <el-table-column prop="location_hash" label="位置摘要" />
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchStudentClasses, checkin, fetchCheckinHistory } from '@/api/student'

const classes = ref([])
const classId = ref(null)
const loading = ref(false)
const histLoading = ref(false)
const checkins = ref([])

async function loadClasses() {
  try {
    const res = await fetchStudentClasses()
    classes.value = res.data?.classes ?? []
  } catch (e) {
    ElMessage.error(e?.message || '加载班级失败')
  }
}

async function loadHistory() {
  histLoading.value = true
  try {
    const res = await fetchCheckinHistory()
    checkins.value = res.data?.checkins ?? []
  } catch {
    checkins.value = []
  } finally {
    histLoading.value = false
  }
}

async function doCheckin() {
  if (!classId.value) {
    ElMessage.warning('请选择班级')
    return
  }
  loading.value = true
  let latitude = null
  let longitude = null
  if (navigator.geolocation) {
    try {
      const pos = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 8000 })
      })
      latitude = pos.coords.latitude
      longitude = pos.coords.longitude
    } catch {
      /* 忽略定位失败 */
    }
  }
  try {
    await checkin({
      class_id: classId.value,
      latitude,
      longitude
    })
    ElMessage.success('签到成功')
    await loadHistory()
  } catch (e) {
    ElMessage.error(e?.message || '签到失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadClasses()
  await loadHistory()
})
</script>

<style scoped>
h2 {
  margin-top: 0;
}
.hint {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 16px;
  max-width: 640px;
}
h3 {
  margin: 24px 0 12px;
  font-size: 16px;
}
</style>
