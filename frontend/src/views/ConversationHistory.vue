<template>
  <div class="page-container">
    <PageHeader title="对话记录" />
    <div class="toolbar" style="display:flex;gap:12px;align-items:center;margin-bottom:16px">
      <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" @change="loadData" />
      <el-input v-model="keyword" placeholder="搜索问题..." clearable @change="loadData" style="width:240px" />
      <el-select v-model="ratingFilter" placeholder="评分筛选" clearable @change="loadData" style="width:140px">
        <el-option label="好评(4-5)" value="good" />
        <el-option label="中评(3)" value="fair" />
        <el-option label="差评(1-2)" value="poor" />
      </el-select>
    </div>
    <el-table :data="items" v-loading="loading" stripe border>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="session_id" label="会话ID" width="100" show-overflow-tooltip />
      <el-table-column prop="question" label="问题" min-width="180" show-overflow-tooltip />
      <el-table-column prop="answer" label="回答" min-width="220" show-overflow-tooltip />
      <el-table-column prop="rating" label="评分" width="80">
        <template #default="{row}">
          <span v-if="row.rating">{{ row.rating }}分</span>
          <span v-else style="color:#c0c4cc">未评</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="170">
        <template #default="{row}">{{ row.created_at?.slice(0,19) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{row}">
          <el-button size="small" @click="openDetail(row)">详情</el-button>
          <el-button
            size="small"
            type="primary"
            style="margin-left:6px"
            :disabled="row.moved_to_pending"
            @click="handleMovePending(row)"
          >移入处理</el-button>
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

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawerVisible" title="对话详情" size="560px">
      <template v-if="detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="会话ID">{{ detail.session_id }}</el-descriptions-item>
          <el-descriptions-item label="用户标识">{{ detail.user_identifier || '-' }}</el-descriptions-item>
          <el-descriptions-item label="评分">{{ detail.rating ? detail.rating+'分' : '未评分' }}</el-descriptions-item>
          <el-descriptions-item label="是否已移入待解决">{{ detail.moved_to_pending ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="敏感词拦截">{{ detail.is_sensitive_blocked ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="时间">{{ detail.created_at?.slice(0,19) }}</el-descriptions-item>
        </el-descriptions>
        <h4 style="margin:16px 0 8px">用户问题：</h4>
        <div class="detail-text">{{ detail.question }}</div>
        <h4 style="margin:16px 0 8px">AI回答：</h4>
        <div class="detail-text">{{ detail.answer }}</div>
        <h4 v-if="detail.feedback" style="margin:16px 0 8px">用户反馈：</h4>
        <div v-if="detail.feedback" class="detail-text">{{ detail.feedback }}</div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
// 新增导入移入接口
import { getConversations, getConversationDetail, moveToPending } from '../api/conversation'

const items = ref([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)
const pageSize = 20
const dateRange = ref([])
const keyword = ref('')
const ratingFilter = ref('')
const route = useRoute()

const drawerVisible = ref(false)
const detail = ref(null)

onMounted(() => {
  if (route.query.rating) {
    ratingFilter.value = route.query.rating
  }
  if (route.query.keyword) {
    keyword.value = route.query.keyword
  }
  loadData()
})


function buildParams() {
  const params = { page: page.value, page_size: pageSize }
  if (dateRange.value?.length === 2) {
    params.date_from = dateRange.value[0]
    params.date_to = dateRange.value[1]
  }
  if (keyword.value) params.keyword = keyword.value
  if (ratingFilter.value === 'good') {
    params.rating_min = 4
    params.rating_max = 5
  } else if (ratingFilter.value === 'fair') {
    params.rating_min = 3
    params.rating_max = 3
  } else if (ratingFilter.value === 'poor') {
    params.rating_min = 1
    params.rating_max = 2
  }
  return params
}

async function loadData() {
  loading.value = true
  try {
    const data = await getConversations(buildParams())
    items.value = data.items
    total.value = data.total
  } catch (e) {
    console.error('加载对话记录失败:', e)
    ElMessage.error('加载对话记录失败，请重试')
  }
  loading.value = false
}

async function openDetail(row) {
  try {
    detail.value = await getConversationDetail(row.id)
    drawerVisible.value = true
  } catch { /* */ }
}

// 新增：移入待解决问题
async function handleMovePending(row) {
  try {
    await ElMessageBox.confirm(
      `确定将该提问「${row.question.slice(0,30)}...」移入待解决问题列表吗？`,
      '移入确认',
      { type: 'warning', confirmButtonText: '确认移入' }
    )
    await moveToPending(row.id)
    ElMessage.success('移入成功，可前往待解决问题页面查看')
    loadData()
  } catch (err) {
    if (err && err.message !== 'cancel') {
      ElMessage.error('移入失败，请重试')
    }
  }
}
</script>