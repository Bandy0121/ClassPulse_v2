<template>
  <div>
    <div class="toolbar">
      <h2>我的班级</h2>
      <el-button type="primary" @click="openCreate">创建班级</el-button>
    </div>
    <el-table v-loading="loading" :data="classes" stripe style="width: 100%">
      <el-table-column prop="name" label="班级名称" min-width="160" />
      <el-table-column prop="class_code" label="班级码" width="120" />
      <el-table-column prop="student_count" label="人数" width="80" />
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="goDetail(row.id)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="创建班级" width="480px" @closed="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：高等数学 A 班" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" rows="3" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitCreate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchClasses, createClass } from '@/api/teacher'

const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const classes = ref([])
const dialogVisible = ref(false)
const formRef = ref()
const form = reactive({ name: '', description: '' })
const rules = {
  name: [{ required: true, message: '请输入班级名称', trigger: 'blur' }]
}

async function load() {
  loading.value = true
  try {
    const res = await fetchClasses()
    classes.value = res.data?.classes ?? []
  } catch (e) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialogVisible.value = true
}

function resetForm() {
  form.name = ''
  form.description = ''
  formRef.value?.resetFields()
}

async function submitCreate() {
  await formRef.value?.validate()
  saving.value = true
  try {
    await createClass({ name: form.name, description: form.description })
    ElMessage.success('创建成功')
    dialogVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e?.message || '创建失败')
  } finally {
    saving.value = false
  }
}

function goDetail(id) {
  router.push({ name: 'teacher-class-detail', params: { id } })
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
h2 {
  margin: 0;
}
</style>
