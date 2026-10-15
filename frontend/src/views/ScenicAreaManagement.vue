<template>
  <div class="page-container">
    <PageHeader title="景区管理"><el-button type="primary" @click="openDialog()">添加景区</el-button></PageHeader>
    <el-table :data="items" v-loading="loading" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="景区名称" width="160" />
      <el-table-column prop="description" label="简介" min-width="200" show-overflow-tooltip />
      <el-table-column prop="hours" label="开放时间" width="160" />
      <el-table-column prop="ticket_info" label="门票信息" width="160" show-overflow-tooltip />
      <el-table-column prop="spot_count" label="景点数" width="80" />
      <el-table-column label="操作" width="200">
        <template #default="{row}">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="50" layout="total, prev, pager, next" @current-change="loadData" style="margin-top:16px;justify-content:flex-end" />

    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑景区':'添加景区'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="简介"><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="开放时间"><el-input v-model="form.hours" placeholder="如：08:00-17:30" /></el-form-item>
        <el-form-item label="门票信息"><el-input v-model="form.ticket_info" type="textarea" :rows="2" placeholder="票价、优惠政策等" /></el-form-item>
        <el-form-item label="交通信息"><el-input v-model="form.transport_info" type="textarea" :rows="2" placeholder="公交、自驾路线等" /></el-form-item>
        <el-form-item label="图片URL"><el-input v-model="form.image_url" placeholder="图片链接地址" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort_order" :min="0" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="handleSave">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import { getScenicAreas, createScenicArea, updateScenicArea, deleteScenicArea } from '../api/scenic'

const items = ref([]); const loading = ref(false); const page = ref(1); const total = ref(0)
const dialogVisible = ref(false); const isEdit = ref(false); const editId = ref(null)
const form = reactive({ name: '', description: '', hours: '', ticket_info: '', transport_info: '', image_url: '', sort_order: 0 })

onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try { const data = await getScenicAreas({ page: page.value, page_size: 50 }); items.value = data.items; total.value = data.total } catch { /* */ }
  loading.value = false
}

function openDialog(row) {
  if (row) {
    isEdit.value = true; editId.value = row.id
    Object.keys(form).forEach(k => form[k] = row[k] !== undefined ? row[k] : form[k])
  } else {
    isEdit.value = false; editId.value = null
    Object.keys(form).forEach(k => form[k] = k === 'sort_order' ? 0 : '')
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.name) return ElMessage.warning('请输入景区名称')
  // cbh修改: 编辑时过滤空字符串，避免覆盖已有数据
  const data = isEdit.value ? Object.fromEntries(Object.entries(form).filter(([_,v]) => v !== '' && v !== null)) : form
  isEdit.value ? await updateScenicArea(editId.value, data) : await createScenicArea(data)
  ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
  dialogVisible.value = false; loadData()
}

async function handleDelete(row) {
  try { await ElMessageBox.confirm(`确定删除"${row.name}"吗？`, '确认', { type: 'warning' }); await deleteScenicArea(row.id); ElMessage.success('已删除'); loadData() } catch { /* */ }
}
</script>
