<template>
  <div class="page-container">
    <PageHeader title="数字人配置" />
    <el-card v-loading="loading">
      <el-tabs>
        <el-tab-pane label="基本信息">
          <el-form :model="form" label-width="120px" style="max-width:600px">
            <el-form-item label="数字人名称"><el-input v-model="form.name" /></el-form-item>
            <el-form-item label="所属场景"><el-input v-model="form.scenic_area" /></el-form-item>
            <el-form-item label="运行状态">
              <el-switch v-model="isOnline" active-text="上线" inactive-text="下线" @change="form.status = isOnline ? 'online' : 'offline'" />
            </el-form-item>
            <el-form-item label="数字人形象">
              <el-select v-model="form.model_path" placeholder="请选择数字人外观" style="width:100%">
                <el-option
                  v-for="item in modelOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
              <div style="color:#909399;font-size:12px;margin-top:4px">选择后保存，游客页会自动切换对应 Live2D 模型</div>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="语音参数">
          <el-form :model="form" label-width="120px" style="max-width:600px">
            <el-form-item label="音色"><el-select v-model="form.voice_timbre" placeholder="选择音色">
                <el-option-group label="精品音库（免费额度充足，日常推荐）">
                  <el-option label="度小萌 - 甜美活泼女声（默认）" value="111" />
                  <el-option label="度小鹿 - 温柔女声" value="5118" />
                  <el-option label="度小娇 - 情感女声" value="5" />
                  <el-option label="度米朵 - 女童音" value="103" />
                  <el-option label="度博文 - 磁性男声" value="106" />
                  <el-option label="度小童 - 男童音" value="110" />
                  <el-option label="度逍遥 - 情感男声" value="5003" />
                </el-option-group>
                <el-option-group label="臻品音库（音质最自然，额度较少，建议录演示视频用）">
                  <el-option label="度灵儿 - 温柔女声" value="4105" />
                  <el-option label="度小雯 - 知性女声" value="4100" />
                  <el-option label="度小乔 - 甜美女声" value="4117" />
                  <el-option label="度姗姗 - 优雅女声" value="4144" />
                  <el-option label="度小贝 - 清亮女声" value="4278" />
                  <el-option label="度星河 - 磁性男声" value="4149" />
                  <el-option label="度清风 - 沉稳男声" value="4143" />
                  <el-option label="度小贤 - 亲和男声" value="4115" />
                </el-option-group>
              </el-select></el-form-item>
            <el-form-item label="语速"><el-slider v-model="form.voice_speed" :min="0.5" :max="3.0" :step="0.1" show-input /></el-form-item>
            <el-form-item label="语调"><el-slider v-model="form.voice_intonation" :min="0.5" :max="3.0" :step="0.1" show-input /></el-form-item>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="AI 参数">
          <el-form :model="form" label-width="120px" style="max-width:600px">
            <el-form-item label="AI 模型"><el-input v-model="form.ai_model" placeholder="deepseek-chat" /></el-form-item>
            <el-form-item label="温度(Temperature)"><el-slider v-model="form.ai_temperature" :min="0" :max="2" :step="0.05" show-input /></el-form-item>
            <el-form-item label="最大Token数"><el-input-number v-model="form.ai_max_tokens" :min="64" :max="4096" :step="64" /></el-form-item>
            <el-form-item label="回答风格"><el-input v-model="form.ai_response_style" type="textarea" :rows="2" placeholder="如：简洁明了、风趣幽默..." /></el-form-item>
            <el-form-item label="系统Prompt"><el-input v-model="form.ai_system_prompt" type="textarea" :rows="4" placeholder="自定义系统级提示词，留空使用默认导游Prompt" /></el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <el-button type="primary" :loading="saving" @click="handleSave" style="margin-top:20px">保存配置</el-button>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '../components/PageHeader.vue'
import { getConfig, updateConfig } from '../api/digitalHuman'

// 只保留你本地真实存在的两个模型
const modelOptions = [
  { label: '桃濑日和（默认少女）', value: '/live2d/hiyori/hiyori_free_t08.model3.json' },
  { label: '春 Haru（接待礼仪）', value: '/live2d/haru_greeter_t05/haru_greeter_t05.model3.json' },
]

const form = reactive({
  name: '', scenic_area: '', status: 'online',
  model_path: '',
  voice_timbre: 'zhixiaomei', voice_speed: 1.0, voice_intonation: 1.0,
  ai_model: 'deepseek-chat', ai_temperature: 0.1, ai_max_tokens: 512,
  ai_system_prompt: '', ai_response_style: ''
})
const isOnline = ref(true)
const loading = ref(false)
const saving = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const data = await getConfig()
    Object.assign(form, data)
    if (!form.model_path) form.model_path = modelOptions[0].value
    isOnline.value = data.status === 'online'
  } catch { /* empty */ }
  loading.value = false
})

async function handleSave() {
  saving.value = true
  try {
    const data = Object.fromEntries(Object.entries(form).filter(([_, v]) => v !== '' && v !== null))
    await updateConfig(data)
    ElMessage.success('配置保存成功')
  } catch { /* empty */ }
  saving.value = false
}
</script>
