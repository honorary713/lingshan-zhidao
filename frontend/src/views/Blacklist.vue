<template>
  <div class="page-container">
    <PageHeader title="黑名单管理"><el-button type="primary" @click="dialogVisible=true">添加黑名单</el-button></PageHeader>
    <el-table :data="items" v-loading="loading" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="user_identifier" label="用户标识" width="200" />
      <el-table-column prop="reason" label="原因" min-width="200" show-overflow-tooltip />
      <el-table-column prop="admin_name" label="操作人" width="120" />
      <el-table-column prop="created_at" label="添加时间" width="170">
        <template #default="{row}">{{ row.created_at?.slice(0,19) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{row}"><el-button size="small" type="danger" @click="handleRemove(row)">移除</el-button></template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="50" layout="total, prev, pager, next" @current-change="loadData" style="margin-top:16px;justify-content:flex-end" />

    <el-dialog v-model="dialogVisible" title="添加黑名单" width="440px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户标识" required><el-input v-model="form.user_identifier" placeholder="IP地址或设备ID" /></el-form-item>
        <el-form-item label="原因"><el-input v-model="form.reason" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="handleAdd">确认添加</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import { getBlacklist, addBlacklist, removeBlacklist } from '../api/blacklist'

const items = ref([]); const loading = ref(false); const page = ref(1); const total = ref(0)
const dialogVisible = ref(false)
const form = reactive({ user_identifier: '', reason: '' })

onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try { const data = await getBlacklist({ page: page.value, page_size: 50 }); items.value = data.items; total.value = data.total } catch { /* */ }
  loading.value = false
}

async function handleAdd() {
  if (!form.user_identifier) return ElMessage.warning('请输入用户标识')
  await addBlacklist({ user_identifier: form.user_identifier, reason: form.reason })
  ElMessage.success('已加入黑名单')
  dialogVisible.value = false; form.user_identifier = ''; form.reason = ''; loadData()
}

async function handleRemove(row) {
  try { await ElMessageBox.confirm('确定移出黑名单吗？', '确认', { type: 'warning' }); await removeBlacklist(row.id); ElMessage.success('已移除'); loadData() } catch { /* */ }
}
</script>
