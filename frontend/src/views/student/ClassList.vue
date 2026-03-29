<template>
  <div>
    <h2>我的班级</h2>
    <el-card shadow="never" class="join-card">
      <template #header>加入班级</template>
      <el-input v-model="code" placeholder="输入教师提供的班级码" style="max-width: 280px; margin-right: 8px" clearable />
      <el-button type="success" :loading="joining" @click="doJoin">加入</el-button>
    </el-card>
    <el-table v-loading="loading" :data="classes" stripe>
      <el-table-column prop="name" label="班级名称" />
      <el-table-column prop="class_code" label="班级码" width="120" />
      <el-table-column label="教师">
        <template #default="{ row }">{{ row.teacher?.real_name || row.teacher?.username }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="danger" @click="doLeave(row)">退出</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchStudentClasses, joinClass, leaveClass } from '@/api/student'

const loading = ref(false)
const joining = ref(false)
const classes = ref([])
const code = ref('')

async function load() {
  loading.value = true
  try {
    const res = await fetchStudentClasses()
    classes.value = res.data?.classes ?? []
  } catch (e) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function doJoin() {
  const c = code.value.trim()
  if (!c) {
    ElMessage.warning('请输入班级码')
    return
  }
  joining.value = true
  try {
    await joinClass(c)
    ElMessage.success('加入成功')
    code.value = ''
    await load()
  } catch (e) {
    ElMessage.error(e?.message || '加入失败')
  } finally {
    joining.value = false
  }
}

async function doLeave(row) {
  await ElMessageBox.confirm(`确定退出「${row.name}」？`, '确认', { type: 'warning' })
  try {
    await leaveClass(row.id)
    ElMessage.success('已退出')
    await load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.message || '操作失败')
  }
}

onMounted(load)
</script>

<style scoped>
h2 {
  margin-top: 0;
}
.join-card {
  margin-bottom: 16px;
}
</style>
