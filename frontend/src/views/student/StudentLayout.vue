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
        text-color="#94A3B8"
        active-text-color="#FFFFFF"
        router
      >
        <el-menu-item index="/student/books">
          <el-icon><Reading /></el-icon>
          <span>图书浏览</span>
        </el-menu-item>
        <el-menu-item index="/student/my-borrows">
          <el-icon><Collection /></el-icon>
          <span>我的借阅</span>
        </el-menu-item>
        <el-menu-item index="/student/seat-reserve">
          <el-icon><OfficeBuilding /></el-icon>
          <span>自习室预约</span>
        </el-menu-item>
        <el-menu-item index="/student/ai-assistant">
          <el-icon><MagicStick /></el-icon>
          <span>AI 助手</span>
        </el-menu-item>
        <el-menu-item index="/student/library-map">
          <el-icon><MapLocation /></el-icon>
          <span>图书馆地图</span>
        </el-menu-item>
        <el-menu-item index="/student/notifications">
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
        <el-menu-item index="/student/profile">
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
              @click="router.push('/student/notifications')"
            >
              <el-icon><Bell /></el-icon>
            </button>
          </el-badge>

          <div class="user-card">
            <span class="user-avatar">{{ userInitial }}</span>
            <span class="user-copy">
              <strong>{{ userStore.userName }}</strong>
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
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../../store/user'
import { notificationApi } from '../../api/auth'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const activeMenu = computed(() => route.path)
const unreadCount = ref(0)
let timer = null

const pageSubtitles = {
  '/student/books': '查找并借阅馆藏图书',
  '/student/my-borrows': '查看借阅记录与到期提醒',
  '/student/seat-reserve': '预约座位与自习空间',
  '/student/ai-assistant': '智能荐书与咨询问答',
  '/student/library-map': '楼层分布与馆藏定位',
  '/student/notifications': '系统消息与借阅提醒',
  '/student/profile': '账户信息与安全设置',
}

const pageInfo = computed(() => ({
  title: route.meta.title || '智慧图书馆',
  subtitle: pageSubtitles[route.path] || '智慧图书馆学生服务平台',
}))

const userInitial = computed(() => userStore.userName?.charAt(0) || '用')
const userDescription = computed(() => {
  const college = userStore.user?.college || userStore.user?.department || '计算机学院'
  return `本科生 · ${college}`
})

onMounted(async () => { await fetchUnread(); timer = setInterval(fetchUnread, 30000) })
onUnmounted(() => { if (timer) clearInterval(timer) })

async function fetchUnread() {
  try { const r = await notificationApi.unreadCount(); unreadCount.value = r.data.count } catch (e) { /* */ }
}

async function handleLogout() {
  await userStore.logout(); router.push('/login')
}
</script>
