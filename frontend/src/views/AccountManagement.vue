<template>
  <div class="page-container">
    <PageHeader title="管理员账号">
      <el-button type="primary" @click="openDialog()">添加管理员</el-button>
    </PageHeader>

    <el-table :data="items" v-loading="loading" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="140" />
      <el-table-column prop="nickname" label="昵称" width="140" />
      <el-table-column prop="role" label="角色" width="120">
        <template #default="{ row }">
          <el-tag :type="row.role==='super_admin'?'danger':'primary'">
            {{ row.role === 'super_admin' ? '超级管理员' : '普通管理员' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active?'success':'info'">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ row.created_at?.slice(0,19) }}</template>
      </el-table-column>
      <el-table-column label="操作" min-width="220">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="warning" @click="openPassword(row)">重置密码</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)" :disabled="row.id===authStore.user?.id">禁用</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="page" :total="total" :page-size="pageSize" layout="total, prev, pager, next" @current-change="loadData" style="margin-top:16px;justify-content:flex-end" />

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑管理员':'添加管理员'" width="480px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名" required><el-input v-model="form.username" :disabled="isEdit" /></el-form-item>
        <el-form-item v-if="!isEdit" label="密码" required><el-input v-model="form.password" type="password" /></el-form-item>
        <el-form-item label="昵称" required><el-input v-model="form.nickname" /></el-form-item>
        <el-form-item label="角色"><el-select v-model="form.role"><el-option label="普通管理员" value="admin" /><el-option label="超级管理员" value="super_admin" /></el-select></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码弹窗 -->
    <el-dialog v-model="pwdVisible" title="重置密码" width="400px">
      <el-form><el-form-item label="新密码"><el-input v-model="newPassword" type="password" /></el-form-item></el-form>
      <template #footer><el-button @click="pwdVisible=false">取消</el-button><el-button type="primary" @click="handleResetPwd">确认</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import PageHeader from '../components/PageHeader.vue'
import { getAdmins, createAdmin, updateAdmin, deleteAdmin, resetPassword } from '../api/admins'

const authStore = useAuthStore()
const items = ref([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)
const pageSize = 20

const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const form = reactive({ username: '', password: '', nickname: '', role: 'admin' })

const pwdVisible = ref(false)
const pwdTargetId = ref(null)
const newPassword = ref('')

onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    const data = await getAdmins({ page: page.value, page_size: pageSize })
    items.value = data.items
    total.value = data.total
  } catch { /* empty */ }
  loading.value = false
}

function openDialog(row) {
  if (row) {
    isEdit.value = true; editId.value = row.id
    form.username = row.username; form.nickname = row.nickname; form.role = row.role; form.password = ''
  } else {
    isEdit.value = false; editId.value = null
    form.username = ''; form.nickname = ''; form.role = 'admin'; form.password = ''
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.username || (!isEdit.value && !form.password) || !form.nickname) {
    return ElMessage.warning('请填写必填项')
  }
  try {
    if (isEdit.value) {
      await updateAdmin(editId.value, { nickname: form.nickname, role: form.role })
    } else {
      await createAdmin({ username: form.username, password: form.password, nickname: form.nickname, role: form.role })
    }
    ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
    dialogVisible.value = false
    loadData()
  } catch { /* empty */ }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定禁用管理员 "${row.username}" 吗？`, '确认操作', { type: 'warning' })
    await deleteAdmin(row.id)
    ElMessage.success('已禁用')
    loadData()
  } catch { /* cancelled */ }
}

function openPassword(row) {
  pwdTargetId.value = row.id; newPassword.value = ''; pwdVisible.value = true
}

async function handleResetPwd() {
  if (!newPassword.value) return ElMessage.warning('请输入新密码')
  await resetPassword(pwdTargetId.value, newPassword.value)
  ElMessage.success('密码已重置')
  pwdVisible.value = false
}
</script>
