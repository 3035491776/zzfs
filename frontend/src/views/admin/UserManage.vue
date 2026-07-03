<template>
  <div>
    <h2>用户管理</h2>
    <el-input v-model="search" placeholder="搜索用户名/姓名" style="width:300px;margin:20px 0" @change="fetchData" />
    <el-table :data="users" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="real_name" label="姓名" width="100" />
      <el-table-column prop="role" label="角色" width="80" />
      <el-table-column prop="status" label="状态" width="80"><template #default="{ row }"><el-tag :type="row.status==='active'?'success':'danger'">{{ row.status }}</el-tag></template></el-table-column>
      <el-table-column prop="create_time" label="注册时间" width="160" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button v-if="row.role!=='admin'" size="small" @click="toggleStatus(row)">{{ row.status==='active'?'冻结':'启用' }}</el-button>
          <el-button v-if="row.role!=='admin'" size="small" type="warning" @click="resetPw(row)">重置密码</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="10" layout="prev,pager,next" @current-change="fetchData" style="margin-top:20px" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { userApi } from '../../api/auth'

const users = ref([])
const search = ref('')
const page = ref(1)
const total = ref(0)

onMounted(() => fetchData())

async function fetchData() {
  const r = await userApi.list({ page: page.value, search: search.value })
  users.value = r.data.list
  total.value = r.data.total
}

async function toggleStatus(row) { try { await userApi.toggleStatus(row.id); ElMessage.success('已更新'); fetchData() } catch (e) { /* handled */ } }
async function resetPw(row) { try { await userApi.resetPassword(row.id); ElMessage.success('密码已重置为123456') } catch (e) { /* handled */ } }
</script>
