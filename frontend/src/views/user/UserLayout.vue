<template>
  <el-container class="student-shell">
    <el-aside class="student-sidebar" width="280px">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true">
          <el-icon><Reading /></el-icon>
        </div>
        <div class="brand-copy">
          <strong>智慧图书馆</strong>
          <span>Smart Library</span>
        </div>
      </div>

      <el-menu
        class="student-menu"
        :default-active="activeMenu"
        background-color="transparent"
        text-color="#607086"
        active-text-color="#243B66"
        router
      >
        <el-menu-item :index="`${portalBase}/books`">
          <el-icon><Reading /></el-icon>
          <span>图书浏览</span>
        </el-menu-item>
        <el-menu-item :index="`${portalBase}/my-borrows`">
          <el-icon><Collection /></el-icon>
          <span>我的借阅</span>
        </el-menu-item>
        <el-menu-item :index="`${portalBase}/seat-reserve`">
          <el-icon><OfficeBuilding /></el-icon>
          <span>自习室预约</span>
        </el-menu-item>
        <el-menu-item :index="`${portalBase}/ai-assistant`">
          <el-icon><MagicStick /></el-icon>
          <span>AI 助手</span>
        </el-menu-item>
        <el-menu-item :index="`${portalBase}/library-map`">
          <el-icon><MapLocation /></el-icon>
          <span>图书馆地图</span>
        </el-menu-item>
        <el-menu-item :index="`${portalBase}/notifications`">
          <div class="menu-item-row">
            <span class="menu-item-left">
              <el-icon><Bell /></el-icon>
              <span>消息通知</span>
            </span>
            <span v-if="unreadCount > 0" class="menu-count">
              {{ unreadCount > 99 ? '99+' : unreadCount }}
            </span>
          </div>
        </el-menu-item>
        <el-menu-item :index="`${portalBase}/profile`">
          <el-icon><Setting /></el-icon>
          <span>个人中心</span>
        </el-menu-item>
      </el-menu>

      <div class="opening-card">
        <div class="opening-icon" aria-hidden="true">
          <el-icon><Clock /></el-icon>
        </div>
        <div>
          <strong>开馆时间</strong>
          <span>周一至周日</span>
          <time>08:00 — 22:00</time>
        </div>
      </div>
    </el-aside>

    <el-container class="student-workspace">
      <el-header class="student-header" height="72px">
        <div class="page-heading">
          <h1>{{ pageInfo.title }}</h1>
          <p>{{ pageInfo.subtitle }}</p>
        </div>

        <div class="header-actions">
          <el-badge
            class="notification-badge"
            :is-dot="unreadCount > 0"
            :hidden="unreadCount === 0"
          >
            <button
              class="icon-button"
              type="button"
              aria-label="查看消息通知"
              @click="router.push(`${portalBase}/notifications`)"
            >
              <el-icon><Bell /></el-icon>
            </button>
          </el-badge>

          <div class="user-card">
            <span class="user-avatar">{{ userInitial }}</span>
            <span class="user-copy">
              <strong>{{ displayName }}</strong>
              <small>{{ userDescription }}</small>
            </span>
          </div>

          <el-button class="logout-button" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            <span>退出</span>
          </el-button>
        </div>
      </el-header>

      <el-main class="student-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, provide, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../../store/user'
import { notificationApi } from '../../api/auth'

const roleConfig = {
  student: {
    nameSuffix: '同学',
    identityText: '本科生 · 计算机学院',
    aiTitle: 'AI 学习助手',
    aiSubtitle: '智能荐书与学习咨询',
    platformSubtitle: '智慧图书馆学生服务平台',
  },
  teacher: {
    nameSuffix: '老师',
    identityText: '教师 · 计算机学院',
    aiTitle: 'AI 教研助手',
    aiSubtitle: '教学参考与学科资源推荐',
    platformSubtitle: '智慧图书馆教师服务平台',
  },
}

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const activeMenu = computed(() => route.path)
const unreadCount = ref(0)
provide('unreadCount', unreadCount)
let timer = null

const portalRole = computed(() => {
  if (route.path.startsWith('/teacher')) return 'teacher'
  if (route.path.startsWith('/student')) return 'student'
  return userStore.userRole === 'teacher' ? 'teacher' : 'student'
})

const portalBase = computed(() => (portalRole.value === 'teacher' ? '/teacher' : '/student'))
const currentRoleConfig = computed(() => roleConfig[portalRole.value] || roleConfig.student)

const pageSubtitles = computed(() => ({
  books: '查找并借阅馆藏图书',
  'my-borrows': '查看借阅记录与到期提醒',
  'seat-reserve': '预约座位与自习空间',
  'ai-assistant': currentRoleConfig.value.aiSubtitle,
  'library-map': '楼层分布与馆藏定位',
  notifications: '系统消息与借阅提醒',
  profile: '账户信息与安全设置',
}))

const routeKey = computed(() => {
  const parts = route.path.split('/').filter(Boolean)
  return parts[parts.length - 1] || 'books'
})

const pageInfo = computed(() => ({
  title: routeKey.value === 'ai-assistant' ? currentRoleConfig.value.aiTitle : route.meta.title || '智慧图书馆',
  subtitle: pageSubtitles.value[routeKey.value] || currentRoleConfig.value.platformSubtitle,
}))

const userInitial = computed(() => userStore.userName?.charAt(0) || '用')
const displayName = computed(() => {
  const name = userStore.userName || '用户'
  const suffix = currentRoleConfig.value.nameSuffix
  return name.endsWith(suffix) ? name : `${name}${suffix}`
})
const userDescription = computed(() => currentRoleConfig.value.identityText)

onMounted(async () => { await fetchUnread(); timer = setInterval(fetchUnread, 30000) })
onUnmounted(() => { if (timer) clearInterval(timer) })

async function fetchUnread() {
  try { const r = await notificationApi.unreadCount(); unreadCount.value = r.data.count } catch (e) { /* */ }
}

async function handleLogout() {
  await userStore.logout(); router.push('/login')
}
</script>
