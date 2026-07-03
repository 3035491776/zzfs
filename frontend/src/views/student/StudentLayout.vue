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

<style scoped>
.student-shell {
  height: 100vh;
  min-width: 1080px;
  overflow: hidden;
  background: #f7f9fc;
}

.student-sidebar {
  position: relative;
  display: flex;
  flex-direction: column;
  flex: 0 0 280px;
  width: 280px !important;
  padding: 0 16px 20px;
  overflow: hidden;
  background: #111827;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  height: 112px;
  padding: 0 8px;
  flex-shrink: 0;
}

.brand-mark {
  display: grid;
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 14px;
  color: #fff;
  background: var(--library-primary);
  box-shadow: 0 12px 28px rgba(51, 102, 255, 0.28);
}

.brand-mark .el-icon {
  font-size: 24px;
}

.brand-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.brand-copy strong {
  color: #fff;
  font-size: 20px;
  font-weight: 700;
  line-height: 1.35;
  letter-spacing: 0.02em;
}

.brand-copy span {
  margin-top: 2px;
  color: #94a3b8;
  font-size: 14px;
  line-height: 1.3;
}

.student-menu {
  flex: 1;
  border-right: 0;
}

.student-menu :deep(.el-menu-item) {
  height: 52px;
  margin: 4px 0;
  padding: 0 16px !important;
  border-radius: 12px;
  font-size: 16px;
  line-height: 52px;
  transition: color 160ms ease, background-color 160ms ease, transform 160ms ease;
}

.student-menu :deep(.el-menu-item .el-icon) {
  width: 22px;
  margin-right: 14px;
  font-size: 21px;
}

.student-menu :deep(.el-menu-item:hover) {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.06);
  transform: translateX(2px);
}

.student-menu :deep(.el-menu-item.is-active) {
  color: #fff;
  background: var(--library-primary);
  box-shadow: 0 10px 24px rgba(24, 64, 191, 0.28);
}

.menu-item-row,
.menu-item-left {
  display: flex;
  align-items: center;
}

.menu-item-row {
  width: 100%;
  justify-content: space-between;
}

.menu-item-left {
  min-width: 0;
}

.menu-count {
  display: inline-flex;
  min-width: 22px;
  height: 22px;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  border-radius: 999px;
  color: #fff;
  background: #ef4444;
  font-size: 12px;
  font-weight: 700;
  line-height: 22px;
}

.student-menu :deep(.el-menu-item.is-active) .menu-count {
  color: var(--library-primary);
  background: #fff;
}

.opening-card {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
  padding: 18px;
  border: 1px solid rgba(148, 163, 184, 0.08);
  border-radius: 14px;
  color: #94a3b8;
  background: #17233b;
}

.opening-icon {
  display: grid;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 10px;
  color: #7ea1ff;
  background: rgba(51, 102, 255, 0.14);
}

.opening-card > div:last-child {
  display: flex;
  flex-direction: column;
}

.opening-card strong {
  margin-bottom: 5px;
  color: #f8fafc;
  font-size: 14px;
  font-weight: 600;
}

.opening-card span,
.opening-card time {
  font-size: 13px;
  line-height: 1.6;
}

.student-workspace {
  min-width: 0;
  overflow: hidden;
}

.student-header {
  display: flex;
  height: 72px;
  flex: 0 0 72px;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px 0 32px;
  border-bottom: 1px solid #e5eaf2;
  background: #fff;
}

.page-heading h1 {
  margin: 0;
  color: #111827;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: -0.02em;
}

.page-heading p {
  margin: 3px 0 0;
  color: #718096;
  font-size: 14px;
  line-height: 1.3;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.notification-badge {
  display: inline-flex;
}

.notification-badge :deep(.el-badge__content.is-dot) {
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  border: 2px solid #fff;
  background: #ef4444;
}

.icon-button {
  display: grid;
  width: 40px;
  height: 40px;
  padding: 0;
  place-items: center;
  border: 0;
  border-radius: 12px;
  color: #64748b;
  background: transparent;
  cursor: pointer;
  transition: color 160ms ease, background-color 160ms ease;
}

.icon-button:hover {
  color: var(--library-primary);
  background: #f0f4ff;
}

.icon-button .el-icon {
  font-size: 22px;
}

.user-card {
  display: flex;
  height: 52px;
  align-items: center;
  gap: 10px;
  padding: 0 14px 0 10px;
  border: 1px solid var(--library-border);
  border-radius: 14px;
  background: #fff;
}

.user-avatar {
  display: grid;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 50%;
  color: var(--library-primary);
  background: #edf2ff;
  font-size: 16px;
  font-weight: 700;
}

.user-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.user-copy strong {
  overflow: hidden;
  max-width: 160px;
  color: #111827;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-copy small {
  overflow: hidden;
  max-width: 180px;
  margin-top: 1px;
  color: #718096;
  font-size: 12px;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout-button {
  height: 44px;
  padding: 0 16px;
  border-color: var(--library-border);
  border-radius: 12px;
  color: #1f2937;
  background: #fff;
  font-size: 14px;
}

.logout-button:hover,
.logout-button:focus {
  border-color: #fca5a5;
  color: #dc2626;
  background: #fff7f7;
}

.logout-button .el-icon {
  margin-right: 7px;
  font-size: 17px;
}

.student-main {
  padding: 24px;
  overflow: auto;
  background: #f7f9fc;
}
</style>
