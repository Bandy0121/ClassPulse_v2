<template>
  <div v-loading="loading">
    <el-page-header @back="$router.push({ name: 'student-assessments' })">
      <template #content>
        <span class="title">{{ assessment?.title || '答题' }}</span>
      </template>
    </el-page-header>
    <p v-if="assessment" class="meta">{{ assessment.description }}</p>

    <el-form v-if="questions.length" label-position="top" class="form">
      <el-form-item v-for="q in questions" :key="q.id" :label="`${q.content}（${q.score} 分）`">
        <el-radio-group v-if="q.question_type === 1" v-model="answers[q.id]">
          <el-radio v-for="(text, key) in q.options" :key="key" :label="key">{{ key }}. {{ text }}</el-radio>
        </el-radio-group>
        <el-checkbox-group v-else v-model="multi[q.id]">
          <el-checkbox v-for="(text, key) in q.options" :key="key" :label="key">{{ key }}. {{ text }}</el-checkbox>
        </el-checkbox-group>
      </el-form-item>
      <el-button type="success" size="large" :loading="submitting" @click="submit">提交答卷</el-button>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchAssessmentDetail, submitAssessment } from '@/api/student'

const props = defineProps({
  id: { type: [String, Number], required: true }
})

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const assessment = ref(null)
const questions = ref([])
const answers = reactive({})
const multi = reactive({})

const aid = computed(() => Number(props.id))

function initMulti() {
  questions.value.forEach((q) => {
    if (q.question_type !== 1) {
      multi[q.id] = []
    }
  })
}

async function load() {
  if (!aid.value) return
  loading.value = true
  try {
    const res = await fetchAssessmentDetail(aid.value)
    assessment.value = res.data?.assessment ?? null
    questions.value = res.data?.questions ?? []
    Object.keys(answers).forEach((k) => delete answers[k])
    Object.keys(multi).forEach((k) => delete multi[k])
    initMulti()
  } catch (e) {
    ElMessage.error(e?.message || '无法加载试卷（可能未开始或已结束）')
    router.push({ name: 'student-assessments' })
  } finally {
    loading.value = false
  }
}

function formatSelected(q) {
  if (q.question_type === 1) {
    return (answers[q.id] || '').toString().toUpperCase()
  }
  const arr = [...(multi[q.id] || [])].map((x) => x.toString().toUpperCase()).sort()
  return arr.join(',')
}

async function submit() {
  for (const q of questions.value) {
    const sel = formatSelected(q)
    if (!sel) {
      ElMessage.warning('请完成所有题目')
      return
    }
  }
  const payload = questions.value.map((q) => ({
    question_id: q.id,
    selected_option: formatSelected(q),
    response_time: 0
  }))
  submitting.value = true
  try {
    await submitAssessment(aid.value, payload)
    ElMessage.success('提交成功')
    await router.push({ name: 'student-assessment-result', params: { id: aid.value } })
  } catch (e) {
    ElMessage.error(e?.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

watch(() => props.id, load, { immediate: true })
</script>

<style scoped>
.title {
  font-size: 18px;
  font-weight: 600;
}
.meta {
  color: #606266;
  margin: 8px 0 16px;
}
.form {
  max-width: 720px;
}
</style>
