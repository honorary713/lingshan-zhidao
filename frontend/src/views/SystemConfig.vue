<template>
  <div class="page-container">
    <PageHeader title="系统配置" />
    <el-tabs>
      <el-tab-pane label="API 密钥管理">
        <div style="margin-bottom:12px"><el-button type="primary" @click="openKeyDialog()">添加密钥</el-button></div>
        <el-table :data="apiKeys" v-loading="keysLoading" stripe border>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="key_name" label="名称" width="160" />
          <el-table-column prop="provider" label="服务商" width="120">
            <template #default="{row}"><el-tag>{{ row.provider }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="api_key" label="API Key" width="240"><template #default="{row}">{{ row.api_key }}</template></el-table-column>
          <el-table-column prop="base_url" label="API地址" min-width="200" show-overflow-tooltip />
          <el-table-column label="操作" width="160">
            <template #default="{row}">
              <el-button size="small" @click="openKeyDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDeleteKey(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="全局参数">
        <el-card>
          <el-form label-width="160px" style="max-width:600px">
            <el-form-item label="单次最大回答Token数">
              <el-input-number v-model="globalConfigs.max_qa_per_session" :min="64" :max="4096" />
            </el-form-item>
            <el-form-item label="知识库检索数量(K)">
              <el-input-number v-model="globalConfigs.faiss_search_k" :min="1" :max="30" />
            </el-form-item>
            <el-form-item label="游客会话超时(分钟)">
              <el-input-number v-model="globalConfigs.session_timeout" :min="5" :max="1440" />
            </el-form-item>
          </el-form>
          <el-button type="primary" :loading="cfgSaving" @click="saveGlobalConfigs">保存全局参数</el-button>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- API密钥弹窗 -->
    <el-dialog v-model="keyDialogVisible" :title="isKeyEdit?'编辑密钥':'添加密钥'" width="500px">
      <el-form :model="keyForm" label-width="100px">
        <el-form-item label="名称" required><el-input v-model="keyForm.key_name" placeholder="如：SiliconFlow主密钥" /></el-form-item>
        <el-form-item label="服务商" required><el-select v-model="keyForm.provider"><el-option label="SiliconFlow" value="siliconflow" /><el-option label="百度ASR" value="baidu_asr" /><el-option label="百度TTS" value="baidu_tts" /></el-select></el-form-item>
        <el-form-item label="API Key" required><el-input v-model="keyForm.api_key" /></el-form-item>
        <el-form-item label="Secret Key"><el-input v-model="keyForm.api_secret" /></el-form-item>
        <el-form-item label="API地址"><el-input v-model="keyForm.base_url" placeholder="如：https://api.siliconflow.cn/v1" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="keyDialogVisible=false">取消</el-button><el-button type="primary" @click="handleSaveKey">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import { getApiKeys, createApiKey, updateApiKey, deleteApiKey, getSystemConfigs, updateSystemConfigs } from '../api/system'

const apiKeys = ref([]); const keysLoading = ref(false)
const keyDialogVisible = ref(false); const isKeyEdit = ref(false); const keyEditId = ref(null)
const keyForm = reactive({ key_name: '', provider: 'siliconflow', api_key: '', api_secret: '', base_url: '' })
const globalConfigs = reactive({ max_qa_per_session: 512, faiss_search_k: 10, session_timeout: 60 })
const cfgSaving = ref(false)

onMounted(async () => {
  keysLoading.value = true
  try { apiKeys.value = (await getApiKeys({ page_size: 200 })).items } catch { /* */ }
  keysLoading.value = false
  try { const cfgs = await getSystemConfigs(); Object.keys(globalConfigs).forEach(k => { if (cfgs[k]) globalConfigs[k] = isNaN(cfgs[k]) ? cfgs[k] : Number(cfgs[k]) }) } catch { /* */ }
})

function openKeyDialog(row) {
  if (row) { isKeyEdit.value = true; keyEditId.value = row.id; keyForm.key_name = row.key_name; keyForm.provider = row.provider; keyForm.api_key = ''; keyForm.api_secret = ''; keyForm.base_url = row.base_url }
  else { isKeyEdit.value = false; keyEditId.value = null; keyForm.key_name = ''; keyForm.provider = 'siliconflow'; keyForm.api_key = ''; keyForm.api_secret = ''; keyForm.base_url = '' }
  keyDialogVisible.value = true
}

async function handleSaveKey() {
  if (!keyForm.key_name || !keyForm.provider || !keyForm.api_key) return ElMessage.warning('请填写必填项')
  isKeyEdit.value ? await updateApiKey(keyEditId.value, keyForm) : await createApiKey(keyForm)
  ElMessage.success(isKeyEdit.value ? '更新成功' : '添加成功')
  keyDialogVisible.value = false
  apiKeys.value = (await getApiKeys({ page_size: 200 })).items
}

async function handleDeleteKey(row) {
  try { await ElMessageBox.confirm('确定删除该密钥吗？', '确认', { type: 'warning' }); await deleteApiKey(row.id); ElMessage.success('已删除'); apiKeys.value = (await getApiKeys({ page_size: 200 })).items } catch { /* */ }
}

async function saveGlobalConfigs() {
  cfgSaving.value = true
  try {
    await updateSystemConfigs(Object.entries(globalConfigs).map(([key, value]) => ({ config_key: key, config_value: String(value) })))
    ElMessage.success('全局参数保存成功')
  } catch { /* */ }
  cfgSaving.value = false
}
</script>
