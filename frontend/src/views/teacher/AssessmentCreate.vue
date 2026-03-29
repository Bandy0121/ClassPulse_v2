<template>
  <div v-loading="pageLoading">
    <el-page-header @back="$router.push({ name: 'teacher-assessment-list', params: { id: cid } })">
      <template #content>
        <span class="title">{{ assessmentId ? '编辑题目' : '创建测试' }}</span>
      </template>
    </el-page-header>

    <el-card v-if="!assessmentId" class="card" shadow="never">
      <template #header>1. 测试信息</template>
      <el-form ref="metaRef" :model="meta" :rules="metaRules" label-width="100px" style="max-width: 560px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="meta.title" placeholder="测试标题" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="meta.description" type="textarea" rows="2" />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker
            v-model="meta.start_time"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="选择开始时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="时长(分)" prop="duration_minutes">
          <el-input-number v-model="meta.duration_minutes" :min="1" :max="240" />
          <div class="field-hint">结束时间由系统根据「开始时间 + 时长」自动计算。</div>
        </el-form-item>
        <el-form-item v-if="previewEndTime" label="预计结束">
          <span class="preview-end">{{ previewEndTime }}</span>
        </el-form-item>
        <el-form-item label="提交后显示答案">
          <el-switch v-model="meta.show_correct_after_submit" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="creating" @click="createMeta">创建并添加题目</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <template v-else>
      <el-alert type="info" :closable="false" show-icon class="mb">
        测试 ID：{{ assessmentId }}。请添加题目后，到「测试列表」中点击发布。
      </el-alert>

      <el-card shadow="never" class="card">
        <template #header>添加题目</template>
        <el-form ref="qRef" :model="q" :rules="qRules" label-width="100px">
          <el-form-item label="题型" prop="question_type">
            <el-radio-group v-model="q.question_type">
              <el-radio :label="1">单选</el-radio>
              <el-radio :label="2">多选</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="题干" prop="content">
            <el-input v-model="q.content" type="textarea" rows="2" />
          </el-form-item>
          <el-form-item label="选项 A" prop="option_a">
            <el-input v-model="q.option_a" />
          </el-form-item>
          <el-form-item label="选项 B" prop="option_b">
            <el-input v-model="q.option_b" />
          </el-form-item>
          <el-form-item label="选项 C">
            <el-input v-model="q.option_c" placeholder="可选" />
          </el-form-item>
          <el-form-item label="选项 D">
            <el-input v-model="q.option_d" placeholder="可选" />
          </el-form-item>
          <el-form-item label="正确答案" prop="correct_answer">
            <el-input v-model="q.correct_answer" placeholder="如 A 或 A,C（大写、逗号分隔）" />
          </el-form-item>
          <el-form-item label="分值">
            <el-input-number v-model="q.score" :min="1" :max="100" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="adding" @click="addQ">添加题目</el-button>
            <el-button @click="goList">返回列表</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createAssessment, addQuestion } from '@/api/teacher'

const props = defineProps({
  id: { type: [String, Number], required: true }
})

const router = useRouter()
const cid = computed(() => Number(props.id))
const pageLoading = ref(false)
const creating = ref(false)
const adding = ref(false)
const assessmentId = ref(null)

const metaRef = ref()
const meta = reactive({
  title: '',
  description: '',
  start_time: '',
  duration_minutes: 45,
  show_correct_after_submit: true
})
const metaRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  duration_minutes: [
    { required: true, message: '请设置考试时长', trigger: 'change' },
    { type: 'number', min: 1, message: '时长至少 1 分钟', trigger: 'change' }
  ]
}

/** 根据开始时间与时长推算本地展示用的预计结束时间（与教师所选日期控件同一日历语义） */
function addMinutesToDateTimeString(str, minutes) {
  if (!str || minutes == null || minutes < 1) return ''
  const m = str.match(/^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$/)
  if (!m) return ''
  const dt = new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6])
  if (Number.isNaN(dt.getTime())) return ''
  dt.setMinutes(dt.getMinutes() + Number(minutes))
  const pad = (n) => String(n).padStart(2, '0')
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}:${pad(dt.getSeconds())}`
}

const previewEndTime = computed(() => addMinutesToDateTimeString(meta.start_time, meta.duration_minutes))

const qRef = ref()
const q = reactive({
  question_type: 1,
  content: '',
  option_a: '',
  option_b: '',
  option_c: '',
  option_d: '',
  correct_answer: '',
  score: 10
})
const qRules = {
  content: [{ required: true, message: '请输入题干', trigger: 'blur' }],
  option_a: [{ required: true, message: '必填', trigger: 'blur' }],
  option_b: [{ required: true, message: '必填', trigger: 'blur' }],
  correct_answer: [{ required: true, message: '请输入正确答案', trigger: 'blur' }]
}

async function createMeta() {
  await metaRef.value?.validate()
  creating.value = true
  try {
    const res = await createAssessment(cid.value, {
      title: meta.title,
      description: meta.description,
      start_time: meta.start_time,
      duration_minutes: meta.duration_minutes,
      max_attempts: 1,
      show_correct_after_submit: meta.show_correct_after_submit
    })
    assessmentId.value = res.data?.id
    ElMessage.success('已创建，请继续添加题目')
  } catch (e) {
    ElMessage.error(e?.message || '创建失败')
  } finally {
    creating.value = false
  }
}

async function addQ() {
  await qRef.value?.validate()
  adding.value = true
  try {
    await addQuestion(assessmentId.value, {
      question_type: q.question_type,
      content: q.content,
      option_a: q.option_a,
      option_b: q.option_b,
      option_c: q.option_c || undefined,
      option_d: q.option_d || undefined,
      correct_answer: q.correct_answer.toUpperCase(),
      score: q.score
    })
    ElMessage.success('题目已添加')
    q.content = ''
    q.option_a = ''
    q.option_b = ''
    q.option_c = ''
    q.option_d = ''
    q.correct_answer = ''
  } catch (e) {
    ElMessage.error(e?.message || '添加失败')
  } finally {
    adding.value = false
  }
}

function goList() {
  router.push({ name: 'teacher-assessment-list', params: { id: cid.value } })
}

watch(
  () => props.id,
  () => {
    assessmentId.value = null
  }
)
</script>

<style scoped>
.title {
  font-size: 18px;
  font-weight: 600;
}
.card {
  margin-top: 16px;
}
.mb {
  margin-top: 16px;
}
.field-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}
.preview-end {
  color: var(--el-text-color-regular);
  font-variant-numeric: tabular-nums;
}
</style>
