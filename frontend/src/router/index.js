import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  // 首页 — 校园智导展示 + 入口
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomePage.vue'),
    meta: { title: '校园智导', noAuth: true }
  },
  // 游客端数字导览
  {
    path: '/visitor',
    name: 'VisitorChat',
    component: () => import('../views/VisitorChat.vue'),
    meta: { title: 'AI 校园导览', noAuth: true }
  },
  // 校园导览地图
  {
    path: '/guide',
    name: 'VisitorGuide',
    component: () => import('../views/VisitorGuide.vue'),
    meta: { title: '校园导览地图', noAuth: true }
  },
  // 管理员登录页
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录', noAuth: true }
  },
  // 管理员后台布局（带侧边栏）
  {
    path: '/admin',
    component: () => import('../views/Layout.vue'),
    redirect: '/admin/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { title: '首页看板' } },
      { path: 'accounts', name: 'AccountManagement', component: () => import('../views/AccountManagement.vue'), meta: { title: '账号管理', requiresSuperAdmin: true } },
      { path: 'digital-human', name: 'DigitalHumanConfig', component: () => import('../views/DigitalHumanConfig.vue'), meta: { title: '数字人配置' } },
      { path: 'sensitive-words', name: 'SensitiveWords', component: () => import('../views/SensitiveWords.vue'), meta: { title: '敏感词过滤' } },
      { path: 'scenic-areas', name: 'ScenicAreaManagement', component: () => import('../views/ScenicAreaManagement.vue'), meta: { title: '景区管理' } },
      { path: 'scenic-spots', name: 'ScenicSpotManagement', component: () => import('../views/ScenicSpotManagement.vue'), meta: { title: '景点管理' } },
      { path: 'faqs', name: 'FaqManagement', component: () => import('../views/FaqManagement.vue'), meta: { title: 'FAQ 管理' } },
      { path: 'unresolved-questions', name: 'UnresolvedQuestions', component: () => import('../views/UnresolvedQuestions.vue'), meta: { title: '待解决问题' } },
      { path: 'conversations', name: 'ConversationHistory', component: () => import('../views/ConversationHistory.vue'), meta: { title: '对话记录' } },
      { path: 'blacklist', name: 'Blacklist', component: () => import('../views/Blacklist.vue'), meta: { title: '黑名单' } },
      { path: 'statistics', name: 'Statistics', component: () => import('../views/Statistics.vue'), meta: { title: '数据统计' } },
      { path: 'report', name: 'VisitorReport', component: () => import('../views/VisitorReport.vue'), meta: { title: '游客感受度报告' } },
      { path: 'system', name: 'SystemConfig', component: () => import('../views/SystemConfig.vue'), meta: { title: '系统配置' } },
      { path: 'logs', name: 'OperationLogs', component: () => import('../views/OperationLogs.vue'), meta: { title: '操作日志' } }
    ]
  },
  // 404找不到页面，跳游客首页
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({ history: createWebHistory(), routes })

let tokenVerified = false

// 导航守卫：游客页面直接放行，不需要登录校验
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 标记noAuth的页面：游客页、登录页，直接放行
  if (to.meta.noAuth) {
    return next()
  }

  // 所有后台页面路径现在以 /admin 开头，无token → 跳登录
  if (!authStore.token) return next('/login')

  // 首次验证token有效性
  if (!tokenVerified) {
    try {
      await authStore.fetchMe()
      tokenVerified = true
    } catch {
      authStore.logout()
      tokenVerified = false
      return next('/login')
    }
  }

  // 超管页面权限校验
  if (to.meta.requiresSuperAdmin && !authStore.isSuperAdmin) {
    return next('/admin/dashboard')
  }

  next()
})

export default router