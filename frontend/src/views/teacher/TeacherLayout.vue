<template>
  <el-container style="height:100vh">
    <el-aside width="200px" style="background:#1f2d3d">
      <div class="logo">智慧图书馆</div>
      <el-menu :default-active="activeMenu" background-color="#1f2d3d" text-color="#bfcbd9" active-text-color="#409EFF" router>
        <el-menu-item index="/teacher/books"><el-icon><Reading /></el-icon> 图书浏览</el-menu-item>
        <el-menu-item index="/teacher/my-borrows"><el-icon><Collection /></el-icon> 我的借阅</el-menu-item>
        <el-menu-item index="/teacher/seat-reserve"><el-icon><OfficeBuilding /></el-icon> 自习室预约</el-menu-item>
        <el-menu-item index="/teacher/ai-assistant"><el-icon><MagicStick /></el-icon> AI助手</el-menu-item>
        <el-menu-item index="/teacher/library-map"><el-icon><MapLocation /></el-icon> 图书馆地图</el-menu-item>
        <el-menu-item index="/teacher/notifications">
          <div class="menu-item-row">
            <span class="menu-item-left"><el-icon><Bell /></el-icon> 消息通知</span>
            <el-badge :value="unreadCount" :hidden="unreadCount===0" />
          </div>
        </el-menu-item>
        <el-menu-item index="/teacher/profile"><el-icon><Setting /></el-icon> 个人中心</el-menu-item>
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
.logo { color: #fff; font-size: 18px; text-align: center; padding: 20px 0; font-weight: bold; }
.menu-item-row { display: flex; align-items: center; justify-content: space-between; width: 100%; }
.menu-item-left { display: flex; align-items: center; gap: 4px; }
</style>
