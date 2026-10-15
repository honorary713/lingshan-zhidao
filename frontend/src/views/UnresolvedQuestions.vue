<template>
  <div class="page-container">
    <!-- 标题修改：未解决问题 → 待解决问题 -->
    <PageHeader title="待解决问题">
      <el-button type="primary" @click="handleRebuild" :loading="rebuilding">重建知识库</el-button>
    </PageHeader>
    <div class="toolbar">
      <el-select v-model="filterStatus" placeholder="状态筛选" clearable @change="loadData">
        <el-option label="待处理" value="pending" /><el-option label="已解决" value="resolved" /><el-option label="已忽略" value="ignored" />
      </el-select>
    </div>
    <el-table :data="items" v-loading="loading" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="question" label="问题" min-width="250" show-overflow-tooltip />
      <el-table-column prop="ask_count" label="询问次数" width="90" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{row}">
          <el-tag :type="row.status==='pending'?'warning':row.status==='resolved'?'success':'info'">
            {{ row.status==='pending'?'待处理':row.status==='resolved'?'已解决':'已忽略' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240">
        <template #default="{row}">
          <el-button v-if="row.status==='pending'" size="small" type="primary" @click="openResolve(row)">转为FAQ</el-button>
          <el-button v-if="row.status==='pending'" size="small" type="warning" @click="handleIgnore(row)">忽略</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="50" layout="total, prev, pager, next" @current-change="loadData" style="margin-top:16px;justify-content:flex-end" />

    <!-- 转为FAQ弹窗 -->
    <el-dialog v-model="resolveVisible" title="转为 FAQ" width="560px">
      <el-form :model="resolveForm" label-width="80px">
        <el-form-item label="问题"><el-input :model-value="selectedQuestion" disabled type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="答案" required><el-input v-model="resolveForm.answer" type="textarea" :rows="5" /></el-form-item>
        <el-form-item label="分类"><el-select v-model="resolveForm.category"><el-option label="通用" value="general" /><el-option label="门票" value="tickets" /><el-option label="交通" value="transport" /><el-option label="景点" value="spots" /></el-select></el-form-item>
      </el-form>
      <template #footer><el-button @click="resolveVisible=false">取消</el-button><el-button type="primary" @click="handleResolve">确认并创建FAQ</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import { getUnresolvedQuestions, resolveQuestion, ignoreQuestion, deleteUnresolvedQuestion, rebuildKnowledgeBase } from '../api/faq'

const items = ref([]); const loading = ref(false); const page = ref(1); const total = ref(0)
const filterStatus = ref('')
const resolveVisible = ref(false); const resolveId = ref(null); const selectedQuestion = ref('')
const resolveForm = ref({ answer: '', category: 'general' })
const rebuilding = ref(false)

onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try { const params = { page: page.value, page_size: 50 }; if (filterStatus.value) params.status = filterStatus.value; const data = await getUnresolvedQuestions(params); items.value = data.items; total.value = data.total } catch { /* */ }
  loading.value = false
}

function openResolve(row) { resolveId.value = row.id; selectedQuestion.value = row.question; resolveForm.value = { answer: '', category: 'general' }; resolveVisible.value = true }

async function handleResolve() {
  if (!resolveForm.value.answer) return ElMessage.warning('请输入答案')
  await resolveQuestion(resolveId.value, resolveForm.value)
  ElMessage.success('已转为 FAQ'); resolveVisible.value = false; loadData()
}

async function handleIgnore(row) {
  try { await ElMessageBox.confirm('确定忽略该问题吗？', '确认', { type: 'warning' }); await ignoreQuestion(row.id); ElMessage.success('已忽略'); loadData() } catch { /* */ }
}

async function handleDelete(row) {
  try { await ElMessageBox.confirm('确定删除该问题吗？', '确认', { type: 'warning' }); await deleteUnresolvedQuestion(row.id); ElMessage.success('已删除'); loadData() } catch { /* */ }
}

async function handleRebuild() {
  try {
    await ElMessageBox.confirm('将从数据库重新生成FAISS知识库索引，确认继续？', '重建知识库', { type: 'info' })
    rebuilding.value = true
    const result = await rebuildKnowledgeBase()
    ElMessage.success(result.message || '知识库重建成功')
  } catch (err) {
    if (err && err.message !== 'cancel') {
      ElMessage.error('知识库重建失败：' + (err.msg || '后端服务异常'))
    }
  } finally {
    rebuilding.value = false
  }
}
</script>