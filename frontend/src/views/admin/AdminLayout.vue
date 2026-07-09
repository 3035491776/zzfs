<template>
  <el-container class="student-shell admin-shell">
    <el-aside class="student-sidebar" width="280px">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true">
          <el-icon><Reading /></el-icon>
        </div>
        <div class="brand-copy">
          <strong>智慧图书馆</strong>
          <span>Admin Console</span>
        </div>
      </div>

      <el-menu
        class="student-menu admin-menu"
        :default-active="activeMenu"
        background-color="transparent"
        text-color="#94A3B8"
        active-text-color="#FFFFFF"
        router
      >
        <el-menu-item index="/admin/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据大屏</span>
        </el-menu-item>
        <el-menu-item index="/admin/monthly-report">
          <el-icon><TrendCharts /></el-icon>
          <span>月度报告</span>
        </el-menu-item>
        <el-menu-item index="/admin/books">
          <div class="menu-item-row">
            <span class="menu-item-left">
              <el-icon><Reading /></el-icon>
              <span>图书管理</span>
            </span>
            <span v-if="counts.pending_book_requests > 0" class="menu-count">
              {{ counts.pending_book_requests > 99 ? '99+' : counts.pending_book_requests }}
            </span>
          </div>
        </el-menu-item>
        <el-menu-item index="/admin/categories">
          <el-icon><Grid /></el-icon>
          <span>分类管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/borrow-review">
          <el-icon><Checked /></el-icon>
          <span>借阅审核</span>
        </el-menu-item>
        <el-menu-item index="/admin/return-review">
          <el-icon><RefreshLeft /></el-icon>
          <span>归还管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/users">
          <el-icon><UserFilled /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/seats">
          <div class="menu-item-row">
            <span class="menu-item-left">
              <el-icon><OfficeBuilding /></el-icon>
              <span>座位管理</span>
            </span>
            <span v-if="counts.pending_seat_repairs > 0" class="menu-count">
              {{ counts.pending_seat_repairs > 99 ? '99+' : counts.pending_seat_repairs }}
            </span>
          </div>
        </el-menu-item>
        <el-menu-item index="/admin/broadcast">
          <el-icon><Bell /></el-icon>
          <span>系统通知广播</span>
        </el-menu-item>
        <el-menu-item index="/admin/profile">
          <el-icon><Setting /></el-icon>
          <span>个人中心</span>
        </el-menu-item>
      </el-menu>

      <div class="admin-role-card">
        <div class="admin-role-icon" aria-hidden="true">
          <el-icon><UserFilled /></el-icon>
        </div>
        <div>
          <strong>管理工作台</strong>
          <span>系统运行中</span>
        </div>
        <i aria-hidden="true"></i>
      </div>
    </el-aside>

    <el-container class="student-workspace">
      <el-header class="student-header" height="72px">
        <div class="page-heading">
          <h1>{{ route.meta.title || '管理工作台' }}</h1>
          <p>智慧图书馆后台管理中心</p>
        </div>

        <div class="header-actions">
          <div class="user-card">
            <span class="user-avatar">{{ userStore.userName?.charAt(0) || '管' }}</span>
            <span class="user-copy">
              <strong>{{ userStore.userName }}</strong>
              <small>系统管理员</small>
            </span>
          </div>

          <el-button class="logout-button" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            <span>退出</span>
          </el-button>
        </div>
      </el-header>

      <el-main class="student-main admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../../store/user'
import { adminApi } from '../../api/auth'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const activeMenu = computed(() => route.path)
const counts = reactive({ pending_book_requests: 0, pending_seat_repairs: 0 })
let timer = null

onMounted(async () => { await fetchCounts(); timer = setInterval(fetchCounts, 30000) })
onUnmounted(() => { if (timer) clearInterval(timer) })

async function fetchCounts() {
  try { const r = await adminApi.pendingCounts(); Object.assign(counts, r.data) } catch (e) { /* */ }
}

async function handleLogout() {
  await userStore.logout(); router.push('/login')
}
</script>

<style scoped>
.admin-menu :deep(.el-menu-item) {
  height: 48px;
  margin-block: 2px;
  line-height: 48px;
}

.admin-role-card {
  display: flex;
  min-height: 74px;
  flex-shrink: 0;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid rgba(148, 163, 184, 0.08);
  border-radius: 14px;
  color: #94a3b8;
  background: #17233b;
}

.admin-role-icon {
  display: grid;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  place-items: center;
  border-radius: 10px;
  color: #7ea1ff;
  background: rgba(51, 102, 255, 0.14);
}

.admin-role-card > div:nth-child(2) {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
}

.admin-role-card strong {
  color: #f8fafc;
  font-size: 14px;
  font-weight: 600;
}

.admin-role-card span {
  margin-top: 4px;
  font-size: 12px;
}

.admin-role-card > i {
  width: 8px;
  height: 8px;
  flex: 0 0 8px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 0 4px rgba(52, 211, 153, 0.1);
}
</style>
