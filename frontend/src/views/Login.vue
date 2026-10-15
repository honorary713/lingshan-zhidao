<template>
  <div class="login-scene">
    <!-- 背景层 -->
    <div class="bg-layer">
      <div class="bg-mist"></div>
    </div>

    <div class="login-card">
      <div class="card-seal">石</div>
      <h1 class="card-brand">校园智导</h1>
      <p class="card-sub">AI 数字人校园导览 · 管理后台</p>
      <div class="card-rule"></div>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="账号" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">
            {{ loading ? '验证中…' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="card-footer">
        <span>演示账号 admin / admin123</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const formRef = ref(null)
const form = reactive({ username: 'admin', password: 'admin123' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/admin/dashboard')
  } catch {
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-scene {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--paper);
  position: relative;
  overflow: hidden;
}

/* 背景：微妙墨色渐变 */
.bg-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.bg-mist {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 320px;
  background:
    radial-gradient(ellipse 600px 180px at 20% 100%, rgba(160,132,76,0.04) 0%, transparent 50%),
    radial-gradient(ellipse 500px 140px at 55% 100%, rgba(160,132,76,0.03) 0%, transparent 50%),
    radial-gradient(ellipse 400px 100px at 80% 100%, rgba(160,132,76,0.04) 0%, transparent 50%);
}

/* 登录卡片 */
.login-card {
  width: 380px;
  padding: 48px 40px 36px;
  background: var(--paper-surface);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  position: relative;
  z-index: 1;
  animation: card-in 0.6s ease;
}

@keyframes card-in {
  from { opacity: 0; transform: translateY(24px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* 卍字印 */
.card-seal {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  border-radius: 50%;
  background: rgba(160, 132, 76, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--patina);
  font-family: var(--font-song);
  font-weight: 700;
}

/* 品牌标题 — 宋体 */
.card-brand {
  font-family: var(--font-song);
  font-size: 26px;
  font-weight: 700;
  color: var(--ink-text);
  letter-spacing: 0.25em;
  text-align: center;
  margin: 0 0 8px;
}

.card-sub {
  text-align: center;
  font-size: 12px;
  color: var(--ink-text-tertiary);
  letter-spacing: 0.06em;
  margin: 0 0 20px;
  font-weight: 300;
}

.card-rule {
  width: 20px;
  height: 1px;
  background: var(--patina);
  margin: 0 auto 28px;
  opacity: 0.5;
}

.login-btn {
  width: 100%;
  height: 46px;
  font-size: 15px;
  letter-spacing: 0.3em;
  border-radius: var(--radius-md);
  border: none;
  margin-top: 4px;
}

.card-footer {
  text-align: center;
  margin-top: 12px;
}

.card-footer span {
  font-size: 11px;
  color: var(--ink-text-disabled);
  letter-spacing: 0.03em;
  font-weight: 300;
}
</style>
