<template>
  <div v-loading="loading">
    <el-page-header @back="$router.push({ name: 'student-assessments' })">
      <template #content>
        <span class="title">测试结果</span>
      </template>
    </el-page-header>

    <el-result
      v-if="summary"
      icon="success"
      :title="summary.assessment?.title || '测验'"
      :sub-title="`得分 ${summary.score} / ${summary.max_score} · 正确 ${summary.correct_count} · 错误 ${summary.wrong_count}`"
    />

    <el-table v-if="rows.length" :data="rows" stripe size="small" class="mt">
      <el-table-column prop="content" label="题目" min-width="200" />
      <el-table-column prop="selected_option" label="你的答案" width="100" />
      <el-table-column v-if="showCorrect" prop="correct_answer" label="正确答案" width="100" />
      <el-table-column label="结果" width="88">
        <template #default="{ row }">
          <el-tag :type="row.is_correct ? 'success' : 'danger'" size="small">
            {{ row.is_correct ? '正确' : '错误' }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchAssessmentResult } from '@/api/student'

const props = defineProps({
  id: { type: [String, Number], required: true }
})

const router = useRouter()
const loading = ref(false)
const summary = ref(null)

const rows = computed(() => summary.value?.answers ?? [])
const showCorrect = computed(() => summary.value?.show_correct_after_submit)

const aid = () => Number(props.id)

async function load() {
  if (!aid()) return
  loading.value = true
  try {
    const res = await fetchAssessmentResult(aid())
    summary.value = res.data ?? null
  } catch (e) {
    ElMessage.error(e?.message || '暂无结果（可能尚未提交）')
    router.push({ name: 'student-assessments' })
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
.mt {
  margin-top: 16px;
}
</style>
