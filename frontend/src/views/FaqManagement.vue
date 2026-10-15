<template>
  <div class="page-container">
    <!-- 标题+按钮左右分开，两个按钮用flex容器包裹紧贴排列 -->
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <PageHeader title="FAQ 问答管理" />
      <div style="display:flex; gap: 12px;">
        <el-button type="primary" @click="openDialog()">添加 FAQ</el-button>
        <el-button type="success" :loading="syncLoading" @click="handleSyncVector">同步FAQ向量库</el-button>
      </div>
    </div>

    <div class="toolbar" style="display:flex;gap:12px;margin-bottom:16px">
      <el-input v-model="keyword" placeholder="搜索问题..." clearable @change="loadData" style="width:240px" />
      <el-select v-model="filterCategory" placeholder="分类筛选" clearable @change="loadData" style="width:160px">
        <el-option label="通用" value="general" />
        <el-option label="门票" value="tickets" />
        <el-option label="交通" value="transport" />
        <el-option label="景点" value="spots" />
        <el-option label="住宿" value="accommodation" />
      </el-select>
    </div>
    <el-table :data="items" v-loading="loading" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="question" label="问题" min-width="220" show-overflow-tooltip />
      <el-table-column prop="answer" label="答案" min-width="280" show-overflow-tooltip />
      <el-table-column prop="category" label="分类" width="100">
        <template #default="{row}">
          <el-tag size="small">{{ row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{row}">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      v-model:current-page="page"
      :total="total"
      :page-size="pageSize"
      layout="total, prev, pager, next"
      @current-change="loadData"
      style="margin-top:16px;justify-content:flex-end"
    />

    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑 FAQ':'添加 FAQ'" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="问题" required>
          <el-input v-model="form.question" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="答案" required>
          <el-input v-model="form.answer" type="textarea" :rows="5" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category">
            <el-option label="通用" value="general" />
            <el-option label="门票" value="tickets" />
            <el-option label="交通" value="transport" />
            <el-option label="景点" value="spots" />
            <el-option label="住宿" value="accommodation" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
// 新增导入重建向量接口
import { getFaqs, createFaq, updateFaq, deleteFaq, rebuildFaqIndex } from '../api/faq'

const items = ref([])
const loading = ref(false)
// 同步向量按钮加载状态
const syncLoading = ref(false)
const page = ref(1)
const total = ref(0)
const pageSize = 20
const keyword = ref('')
const filterCategory = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = reactive({
  question: '',
  answer: '',
  category: 'general',
  sort_order: 0
})

onMounted(() => loadData())

// 加载FAQ列表（后端自动过滤is_active=true有效数据）
async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (keyword.value) params.keyword = keyword.value
    if (filterCategory.value) params.category = filterCategory.value
    const data = await getFaqs(params)
    items.value = data.items
    total.value = data.total
  } catch (err) {
    ElMessage.error('加载列表失败：' + (err.msg || '网络异常'))
  } finally {
    loading.value = false
  }
}

// 打开新增/编辑弹窗
function openDialog(row) {
  if (row) {
    isEdit.value = true
    editId.value = row.id
    form.question = row.question
    form.answer = row.answer
    form.category = row.category
    form.sort_order = row.sort_order
  } else {
    isEdit.value = false
    editId.value = null
    form.question = ''
    form.answer = ''
    form.category = 'general'
    form.sort_order = 0
  }
  dialogVisible.value = true
}

// 保存新增/编辑FAQ
async function handleSave() {
  if (!form.question.trim()) return ElMessage.warning('问题不能为空')
  if (!form.answer.trim()) return ElMessage.warning('答案不能为空')
  const submitData = isEdit.value
    ? Object.fromEntries(Object.entries(form).filter(([_, v]) => v !== '' && v !== null))
    : { ...form }
  try {
    isEdit.value ? await updateFaq(editId.value, submitData) : await createFaq(submitData)
    ElMessage.success(isEdit.value ? '更新成功，向量库已自动同步' : '创建成功，向量库已自动同步')
    dialogVisible.value = false
    loadData()
  } catch (err) {
    ElMessage.error('保存失败：' + (err.msg || '接口异常'))
  }
}

// 删除FAQ
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除该FAQ吗？删除后知识库不再读取本条内容`, '删除确认', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消'
    })
    await deleteFaq(row.id)
    ElMessage.success('删除成功，向量库已自动同步')
    loadData()
  } catch (err) {
    if (err && err.message !== 'cancel') {
      ElMessage.error('删除失败，请稍后重试')
    }
  }
}

// 手动同步FAQ向量库函数
async function handleSyncVector() {
  syncLoading.value = true
  try {
    await rebuildFaqIndex()
    ElMessage.success('FAQ向量库同步完成，游客聊天可匹配所有有效问答')
  } catch (err) {
    ElMessage.error('同步向量库失败：' + (err.msg || '后端服务异常'))
  } finally {
    syncLoading.value = false
  }
}
</script>