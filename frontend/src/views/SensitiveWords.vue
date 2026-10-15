<template>
  <div class="page-container">
    <PageHeader title="敏感词过滤">
      <div style="display:flex;gap:8px">
        <el-button @click="batchVisible=true">批量导入</el-button>
        <el-button type="primary" @click="openAddDialog">添加敏感词</el-button>
      </div>
    </PageHeader>
    <div class="toolbar">
      <el-select v-model="filterCategory" placeholder="分类筛选" clearable @change="loadData">
        <el-option label="通用" value="general" /><el-option label="政治" value="politics" /><el-option label="广告" value="ad" /><el-option label="辱骂" value="abuse" />
      </el-select>
    </div>
    <el-table :data="items" v-loading="loading" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="word" label="敏感词" />
      <el-table-column prop="category" label="分类" width="100">
        <template #default="{row}"><el-tag size="small">{{ row.category }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{row}"><el-tag :type="row.is_active?'success':'info'">{{ row.is_active?'启用':'禁用' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{row}">
          <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="50" layout="total, prev, pager, next" @current-change="loadData" style="margin-top:16px;justify-content:flex-end" />

    <!-- 添加/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑敏感词':'添加敏感词'" width="420px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="敏感词"><el-input v-model="form.word" /></el-form-item>
        <el-form-item label="分类"><el-select v-model="form.category"><el-option label="通用" value="general" /><el-option label="政治" value="politics" /><el-option label="广告" value="ad" /><el-option label="辱骂" value="abuse" /></el-select></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="handleSave">保存</el-button></template>
    </el-dialog>

    <!-- 批量导入弹窗 -->
    <el-dialog v-model="batchVisible" title="批量导入敏感词" width="500px">
      <el-form label-width="80px">
        <el-form-item label="分类"><el-select v-model="batchCategory"><el-option label="通用" value="general" /><el-option label="政治" value="politics" /><el-option label="广告" value="ad" /><el-option label="辱骂" value="abuse" /></el-select></el-form-item>
        <el-form-item label="敏感词"><el-input v-model="batchWords" type="textarea" :rows="8" placeholder="每行一个敏感词" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="batchVisible=false">取消</el-button><el-button type="primary" @click="handleBatchImport">导入</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import { getSensitiveWords, addSensitiveWord, updateSensitiveWord, deleteSensitiveWord, batchImportSensitiveWords } from '../api/digitalHuman'

const items = ref([]); const loading = ref(false); const page = ref(1); const total = ref(0)
const filterCategory = ref('')
const dialogVisible = ref(false); const isEdit = ref(false); const editId = ref(null)
const form = reactive({ word: '', category: 'general' })
const batchVisible = ref(false); const batchCategory = ref('general'); const batchWords = ref('')

onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: 50 }
    if (filterCategory.value) params.category = filterCategory.value
    const data = await getSensitiveWords(params)
    items.value = data.items; total.value = data.total
  } catch { /* empty */ }
  loading.value = false
}

function openAddDialog() { isEdit.value = false; editId.value = null; form.word = ''; form.category = 'general'; dialogVisible.value = true }
function openEditDialog(row) { isEdit.value = true; editId.value = row.id; form.word = row.word; form.category = row.category; dialogVisible.value = true }

async function handleSave() {
  if (!form.word) return ElMessage.warning('请输入敏感词')
  isEdit.value ? await updateSensitiveWord(editId.value, { word: form.word, category: form.category }) : await addSensitiveWord({ word: form.word, category: form.category })
  ElMessage.success(isEdit.value ? '更新成功' : '添加成功')
  dialogVisible.value = false; loadData()
}

async function handleDelete(row) {
  try { await ElMessageBox.confirm(`确定删除"${row.word}"吗？`, '确认', { type: 'warning' }); await deleteSensitiveWord(row.id); ElMessage.success('已删除'); loadData() } catch { /* */ }
}

async function handleBatchImport() {
  if (!batchWords.value.trim()) return ElMessage.warning('请输入敏感词')
  const result = await batchImportSensitiveWords({ words: batchWords.value, category: batchCategory.value })
  ElMessage.success(`成功导入 ${result.added_count} 个敏感词`)
  batchVisible.value = false; batchWords.value = ''; loadData()
}
</script>
