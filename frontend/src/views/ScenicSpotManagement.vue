<template>
  <div class="page-container">
    <PageHeader title="景点管理"><el-button type="primary" @click="openDialog()">添加景点</el-button></PageHeader>
    <div class="toolbar">
      <el-select v-model="filterAreaId" placeholder="按景区筛选" clearable @change="loadData" style="width:200px">
        <el-option v-for="a in areas" :key="a.id" :label="a.name" :value="a.id" />
      </el-select>
    </div>
    <el-table :data="items" v-loading="loading" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="景点名称" width="160" />
      <el-table-column prop="area_name" label="所属景区" width="140" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column label="操作" width="200">
        <template #default="{row}">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="50" layout="total, prev, pager, next" @current-change="loadData" style="margin-top:16px;justify-content:flex-end" />

    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑景点':'添加景点'" width="560px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="所属景区" required><el-select v-model="form.scenic_area_id" style="width:100%"><el-option v-for="a in areas" :key="a.id" :label="a.name" :value="a.id" /></el-select></el-form-item>
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="图片URL"><el-input v-model="form.image_url" /></el-form-item>
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
import { getScenicAreas, getScenicSpots, createScenicSpot, updateScenicSpot, deleteScenicSpot } from '../api/scenic'

const items = ref([]); const areas = ref([]); const loading = ref(false)
const page = ref(1); const total = ref(0); const filterAreaId = ref(null)
const dialogVisible = ref(false); const isEdit = ref(false); const editId = ref(null)
const form = reactive({ scenic_area_id: null, name: '', description: '', image_url: '', sort_order: 0 })

onMounted(async () => {
  // cbh修改: 添加 try-catch，防止景区列表加载失败导致整个页面崩溃
  try {
    const d = await getScenicAreas({ page_size: 200 })
    areas.value = d.items
  } catch { /* 加载失败时使用空列表，不影响景点数据加载 */ }
  loadData()
})

async function loadData() {
  loading.value = true
  try { const params = { page: page.value, page_size: 50 }; if (filterAreaId.value) params.area_id = filterAreaId.value; const data = await getScenicSpots(params); items.value = data.items; total.value = data.total } catch { /* */ }
  loading.value = false
}

function openDialog(row) {
  if (row) {
    isEdit.value = true; editId.value = row.id
    form.scenic_area_id = row.scenic_area_id; form.name = row.name; form.description = row.description; form.image_url = row.image_url; form.sort_order = row.sort_order
  } else {
    isEdit.value = false; editId.value = null
    form.scenic_area_id = areas.value[0]?.id || null; form.name = ''; form.description = ''; form.image_url = ''; form.sort_order = 0
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.name || !form.scenic_area_id) return ElMessage.warning('请填写必填项')
  // cbh修改: 编辑时过滤空字符串
  const data = isEdit.value ? Object.fromEntries(Object.entries(form).filter(([_,v]) => v !== '' && v !== null)) : form
  isEdit.value ? await updateScenicSpot(editId.value, data) : await createScenicSpot(data)
  ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
  dialogVisible.value = false; loadData()
}

async function handleDelete(row) {
  try { await ElMessageBox.confirm(`确定删除"${row.name}"吗？`, '确认', { type: 'warning' }); await deleteScenicSpot(row.id); ElMessage.success('已删除'); loadData() } catch { /* */ }
}
</script>
