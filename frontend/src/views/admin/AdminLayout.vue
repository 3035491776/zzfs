<template>
  <el-container style="height:100vh">
    <el-aside width="220px" style="background:#1f2d3d">
      <div class="logo">智慧图书馆</div>
      <el-menu :default-active="activeMenu" background-color="#1f2d3d" text-color="#bfcbd9" active-text-color="#409EFF" router>
        <el-menu-item index="/admin/dashboard"><el-icon><DataAnalysis /></el-icon> 数据大屏</el-menu-item>
        <el-menu-item index="/admin/books">
          <div class="menu-item-row">
            <span class="menu-item-left"><el-icon><Reading /></el-icon> 图书管理</span>
            <el-badge :value="counts.pending_book_requests" :hidden="counts.pending_book_requests===0" />
          </div>
        </el-menu-item>
        <el-menu-item index="/admin/categories"><el-icon><Grid /></el-icon> 分类管理</el-menu-item>
        <el-menu-item index="/admin/borrow-review"><el-icon><Checked /></el-icon> 借阅审核</el-menu-item>
        <el-menu-item index="/admin/return-review"><el-icon><RefreshLeft /></el-icon> 归还管理</el-menu-item>
        <el-menu-item index="/admin/users"><el-icon><UserFilled /></el-icon> 用户管理</el-menu-item>
        <el-menu-item index="/admin/seats">
          <div class="menu-item-row">
            <span class="menu-item-left"><el-icon><OfficeBuilding /></el-icon> 座位管理</span>
            <el-badge :value="counts.pending_seat_repairs" :hidden="counts.pending_seat_repairs===0" />
          </div>
        </el-menu-item>
        <el-menu-item index="/admin/broadcast"><el-icon><Bell /></el-icon> 系统通知广播</el-menu-item>
        <el-menu-item index="/admin/profile"><el-icon><Setting /></el-icon> 个人中心</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="background:#fff;border-bottom:1px solid #e4e7ed;display:flex;align-items:center;justify-content:flex-end">
        <span style="margin-right:16px">{{ userStore.userName }}</span>
        <el-button @click="handleLogout" type="danger" size="small">退出</el-button>
      </el-header>
      <el-main><router-view /></el-main>
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
.logo { color: #fff; font-size: 20px; text-align: center; padding: 20px 0; font-weight: bold; letter-spacing: 2px; }
.menu-item-row { display: flex; align-items: center; justify-content: space-between; width: 100%; }
.menu-item-left { display: flex; align-items: center; gap: 4px; }
</style>
