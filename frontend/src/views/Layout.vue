<template>
  <el-container class="layout-root">
    <!-- 侧边栏 · 砚台 -->
    <el-aside :width="appStore.sidebarCollapsed ? '60px' : '224px'" class="layout-sidebar">
      <div class="eave"></div>

      <div class="sidebar-brand">
        <span class="brand-seal">石</span>
        <span v-if="!appStore.sidebarCollapsed" class="brand-title">校园智导</span>
      </div>

      <el-menu
        :default-active="route.path"
        :collapse="appStore.sidebarCollapsed"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/admin/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>看板</span>
        </el-menu-item>

        <el-sub-menu v-if="authStore.isSuperAdmin" index="accounts-group">
          <template #title>
            <el-icon><UserFilled /></el-icon>
            <span>账号</span>
          </template>
          <el-menu-item index="/admin/accounts">管理员</el-menu-item>
          <el-menu-item index="/admin/logs">操作日志</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="dh-group">
          <template #title>
            <el-icon><Monitor /></el-icon>
            <span>数字人</span>
          </template>
          <el-menu-item index="/admin/digital-human">基础配置</el-menu-item>
          <el-menu-item index="/admin/sensitive-words">敏感词</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="kb-group">
          <template #title>
            <el-icon><Collection /></el-icon>
            <span>知识库</span>
          </template>
          <el-menu-item index="/admin/scenic-areas">知识源</el-menu-item>
          <el-menu-item index="/admin/scenic-spots">地标</el-menu-item>
          <el-menu-item index="/admin/faqs">FAQ</el-menu-item>
          <el-menu-item index="/admin/unresolved-questions">待答</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="interact-group">
          <template #title>
            <el-icon><ChatDotRound /></el-icon>
            <span>交互</span>
          </template>
          <el-menu-item index="/admin/conversations">对话</el-menu-item>
          <el-menu-item index="/admin/blacklist">黑名单</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/admin/statistics">
          <el-icon><TrendCharts /></el-icon>
          <span>统计</span>
        </el-menu-item>

        <el-menu-item index="/admin/report">
          <el-icon><Document /></el-icon>
          <span>报告</span>
        </el-menu-item>

        <el-menu-item index="/admin/system">
          <el-icon><Setting /></el-icon>
          <span>系统</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-toggle" @click="appStore.toggleSidebar()">
        <el-icon :size="16">
          <Fold v-if="!appStore.sidebarCollapsed" /><Expand v-else />
        </el-icon>
      </div>
    </el-aside>

    <!-- 主区域 · 宣纸 -->
    <el-container class="layout-main">
      <el-header class="layout-header">
        <div class="header-left">
          <span class="header-crumb">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand" trigger="click">
            <div class="user-chip">
              <span class="user-avatar">{{ (authStore.user?.nickname || '管')[0] }}</span>
              <span class="user-name">{{ authStore.user?.nickname || '管理员' }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="visitor">
                  <el-icon><View /></el-icon> 游客端
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon> 退出
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="layout-body">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useAppStore } from '../stores/app'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis, UserFilled, Monitor, Collection, ChatDotRound,
  TrendCharts, Setting, Fold, Expand, SwitchButton,
  Document, View
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

const pageTitle = computed(() => route.meta?.title || '')

function handleCommand(cmd) {
  if (cmd === 'logout') {
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }
  if (cmd === 'visitor') {
    window.open('/visitor', '_blank')
  }
}
</script>

<style scoped>
/* ============================================
   管理后台 · 书斋
   Study Layout
   ============================================ */

.layout-root { height: 100vh; }

/* ===== 侧边栏 · 砚台 ===== */
.layout-sidebar {
  background: var(--inkstone);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.28s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

/* 铜色飞檐线 */
.eave {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--patina) 15%,
    rgba(160, 132, 76, 0.7) 50%,
    var(--patina) 85%,
    transparent 100%
  );
  z-index: 10;
  opacity: 0.8;
}

/* 品牌区 */
.sidebar-brand {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 18px;
  gap: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  overflow: hidden;
  white-space: nowrap;
}

.brand-seal {
  font-size: 18px;
  color: var(--patina);
  font-family: var(--font-song);
  font-weight: 700;
  flex-shrink: 0;
}

.brand-title {
  font-family: var(--font-song);
  font-size: 16px;
  font-weight: 700;
  color: var(--mist-text);
  letter-spacing: 0.15em;
}

/* Menu */
.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: none;
  padding: 8px 0;
}

.sidebar-menu:not(.el-menu--collapse) { width: 100%; }

.sidebar-menu .el-menu-item.is-active {
  color: #fff;
  background: rgba(160, 132, 76, 0.1);
  border-left: 2px solid var(--patina);
  padding-left: 18px;
}

/* Toggle */
.sidebar-toggle {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-top: 1px solid rgba(255,255,255,0.04);
  flex-shrink: 0;
  color: var(--mist-text-faint);
  cursor: pointer;
  transition: color 0.2s;
}

.sidebar-toggle:hover { color: var(--patina); }

/* ===== 主区域 · 宣纸 ===== */
.layout-main {
  background: var(--paper);
}

/* Header */
.layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 28px;
  height: 52px;
  background: rgba(250,247,242,0.85);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--rule-light);
}

.header-crumb {
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-text-tertiary);
  letter-spacing: 0.03em;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
}

.user-chip:hover { background: rgba(0,0,0,0.03); }

.user-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--patina-bg);
  color: #7a6535;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-name {
  font-size: 13px;
  color: var(--ink-text);
  font-weight: 400;
}

/* Body */
.layout-body {
  background: var(--paper);
  min-height: calc(100vh - 52px);
  overflow-y: auto;
}
</style>
