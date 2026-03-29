<template>
  <div v-loading="loading">
    <el-page-header @back="$router.push({ name: 'teacher-classes' })">
      <template #content>
        <span class="title">{{ info?.name || '班级详情' }}</span>
      </template>
    </el-page-header>

    <el-descriptions v-if="info" :column="2" border class="desc" title="基本信息">
      <el-descriptions-item label="班级码">{{ info.class_code }}</el-descriptions-item>
      <el-descriptions-item label="学生人数">{{ info.student_count }}</el-descriptions-item>
      <el-descriptions-item label="测试数量">{{ info.assessment_count }}</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ info.created_at }}</el-descriptions-item>
      <el-descriptions-item label="描述" :span="2">{{ info.description || '—' }}</el-descriptions-item>
    </el-descriptions>

    <div class="actions" v-if="cid">
      <el-button type="primary" @click="goAssessments">测试列表</el-button>
      <el-button @click="goCreateAssessment">创建测试</el-button>
      <el-button @click="goCheckins">签到记录</el-button>
      <el-button type="success" plain @click="goClassStats">班级统计</el-button>
      <el-button @click="openEdit">编辑班级</el-button>
      <el-button type="danger" plain @click="removeClass">删除班级</el-button>
    </div>

    <h3>学生列表</h3>
    <el-table :data="students" stripe size="small" style="width: 100%">
      <el-table-column prop="real_name" label="姓名" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="student_id" label="学号" />
      <el-table-column prop="joined_at" label="加入时间" width="170" />
    </el-table>

    <h3>测试概览</h3>
    <el-table :data="assessments" stripe size="small" style="width: 100%">
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="question_count" label="题目数" width="90" />
      <el-table-column label="发布" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_published ? 'success' : 'info'" size="small">
            {{ row.is_published ? '已发布' : '草稿' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button link type="primary" @click="goStats(row.id)">统计</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="editVisible" title="编辑班级" width="480px">
      <el-form ref="editRef" :model="editForm" :rules="editRules" label-width="88px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="editForm.description" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSaving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchClassDetail, updateClass, deleteClass } from '@/api/teacher'

const props = defineProps({
  id: { type: [String, Number], required: true }
})

const router = useRouter()
const loading = ref(false)
const info = ref(null)
const students = ref([])
const assessments = ref([])
const editVisible = ref(false)
const editSaving = ref(false)
const editRef = ref()
const editForm = reactive({ name: '', description: '' })
const editRules = { name: [{ required: true, message: '请输入名称', trigger: 'blur' }] }

const cid = computed(() => Number(props.id))

async function load() {
  if (!cid.value) return
  loading.value = true
  try {
    const res = await fetchClassDetail(cid.value)
    const d = res.data
    info.value = d?.class_info ?? null
    students.value = d?.students ?? []
    assessments.value = d?.assessments ?? []
  } catch (e) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function goAssessments() {
  router.push({ name: 'teacher-assessment-list', params: { id: cid.value } })
}
function goCreateAssessment() {
  router.push({ name: 'teacher-assessment-create', params: { id: cid.value } })
}
function goCheckins() {
  router.push({ name: 'teacher-checkins', params: { id: cid.value } })
}
function goClassStats() {
  router.push({ name: 'teacher-class-statistics', params: { id: cid.value } })
}
function goStats(aid) {
  router.push({ name: 'teacher-statistics', params: { id: aid } })
}

function openEdit() {
  if (!info.value) return
  editForm.name = info.value.name
  editForm.description = info.value.description || ''
  editVisible.value = true
}

async function saveEdit() {
  await editRef.value?.validate()
  editSaving.value = true
  try {
    await updateClass(cid.value, { name: editForm.name, description: editForm.description })
    ElMessage.success('已保存')
    editVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    editSaving.value = false
  }
}

async function removeClass() {
  await ElMessageBox.confirm('删除后不可恢复，确定删除该班级？', '确认', { type: 'warning' })
  try {
    await deleteClass(cid.value)
    ElMessage.success('已删除')
    router.push({ name: 'teacher-classes' })
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
.desc {
  margin: 16px 0;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
}
h3 {
  margin: 20px 0 12px;
  font-size: 16px;
}
</style>
