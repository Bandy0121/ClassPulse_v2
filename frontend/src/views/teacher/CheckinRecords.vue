<template>
  <div>
    <el-page-header @back="$router.push({ name: 'teacher-class-detail', params: { id: cid } })">
      <template #content>
        <span class="title">签到记录</span>
      </template>
    </el-page-header>
    <el-table v-loading="loading" :data="rows" stripe style="width: 100%; margin-top: 16px">
      <el-table-column prop="real_name" label="姓名" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="student_no" label="学号" width="120" />
      <el-table-column prop="timestamp" label="签到时间" width="170" />
      <el-table-column prop="location_hash" label="位置摘要" min-width="120" />
      <el-table-column prop="ip_address" label="IP" width="140" />
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchClassCheckins } from '@/api/teacher'

const props = defineProps({
  id: { type: [String, Number], required: true }
})

const loading = ref(false)
const rows = ref([])
const cid = computed(() => Number(props.id))

async function load() {
  if (!cid.value) return
  loading.value = true
  try {
    const res = await fetchClassCheckins(cid.value)
    rows.value = res.data?.checkins ?? []
  } catch (e) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

watch(() => props.id, load, { immediate: true })
</script>

<style scoped>
.title {
  font-size: 18px;
  font-weight: 600;
}
</style>
