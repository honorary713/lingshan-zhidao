<template>
  <div class="page-container">
    <PageHeader title="操作日志" />
    <div class="toolbar">
      <el-input v-model="filterAction" placeholder="搜索操作类型..." clearable @change="loadData" style="width:200px" />
      <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD" @change="loadData" />
    </div>
    <el-table :data="items" v-loading="loading" stripe border>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="admin_name" label="操作人" width="140">
        <template #default="{row}"><span v-if="row.admin_name">{{ row.admin_name }}</span><span v-else style="color:#c0c4cc">系统</span></template>
      </el-table-column>
      <el-table-column prop="action" label="操作类型" width="180">
        <template #default="{row}"><el-tag size="small">{{ row.action }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="detail" label="详情" min-width="220" show-overflow-tooltip />
      <el-table-column prop="ip_address" label="IP地址" width="140" />
      <el-table-column prop="created_at" label="时间" width="170">
        <template #default="{row}">{{ row.created_at?.slice(0,19) }}</template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="pageSize" layout="total, prev, pager, next" @current-change="loadData" style="margin-top:16px;justify-content:flex-end" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import { getLogs } from '../api/system'

const items = ref([]); const loading = ref(false); const page = ref(1); const total = ref(0); const pageSize = 30
const filterAction = ref(''); const dateRange = ref([])

onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (filterAction.value) params.action = filterAction.value
    if (dateRange.value?.length === 2) { params.date_from = dateRange.value[0]; params.date_to = dateRange.value[1] }
    const data = await getLogs(params); items.value = data.items; total.value = data.total
  } catch { /* */ }
  loading.value = false
}
</script>
