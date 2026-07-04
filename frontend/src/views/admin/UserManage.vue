<template>
  <div class="user-manage-page">
    <el-card shadow="never" class="workspace-card">
      <template #header>
        <div class="section-heading">
          <div>
            <h3>用户管理</h3>
            <p>检索平台用户并维护账号使用状态</p>
          </div>
        </div>
      </template>

      <div class="search-bar">
        <el-input
          v-model="search"
          class="search-input"
          placeholder="搜索用户名 / 姓名"
          clearable
          @change="fetchData"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <span class="search-bar__spacer"></span>
        <span class="result-count">共 {{ total }} 位用户</span>
      </div>

      <el-table :data="users" stripe class="management-table">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" min-width="150" />
        <el-table-column prop="real_name" label="姓名" min-width="130" />
        <el-table-column prop="role" label="角色" width="110">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'teacher' ? 'warning' : 'primary'" effect="plain">
              {{ row.role === 'admin' ? '管理员' : row.role === 'teacher' ? '教师' : '学生' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'" effect="plain">
              {{ row.status === 'active' ? '正常' : '已冻结' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="注册时间" width="180" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.role !== 'admin'"
              size="small"
              :type="row.status === 'active' ? 'danger' : 'primary'"
              @click="toggleStatus(row)"
            >
              {{ row.status === 'active' ? '冻结' : '启用' }}
            </el-button>
            <el-button v-if="row.role !== 'admin'" size="small" @click="resetPw(row)">重置密码</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-row">
        <span>共 {{ total }} 条用户记录</span>
        <el-pagination
          v-model:current-page="page"
          :total="total"
          :page-size="10"
          layout="prev,pager,next"
          background
          @current-change="fetchData"
        />
      </div>
    </el-card>
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

<style scoped>
.user-manage-page {
  width: 100%;
  max-width: 1480px;
  margin: 0 auto;
}

.workspace-card :deep(.el-card__header) {
  min-height: 74px;
  padding: 16px 24px;
  border-bottom-color: var(--library-border);
}

.workspace-card :deep(.el-card__body) {
  padding: 22px 24px 18px;
}

.section-heading,
.search-bar,
.pagination-row {
  display: flex;
  align-items: center;
}

.section-heading h3 {
  margin: 0;
  color: var(--library-text);
  font-size: 17px;
  font-weight: 700;
}

.section-heading p {
  margin: 5px 0 0;
  color: var(--library-muted);
  font-size: 12px;
}

.search-bar {
  gap: 12px;
  padding: 16px;
  margin-bottom: 18px;
  border: 1px solid var(--library-border);
  border-radius: 14px;
  background: #f9fbfd;
}

.search-input {
  width: min(420px, 42%);
}

.search-bar__spacer {
  flex: 1;
}

.result-count,
.pagination-row > span {
  color: var(--library-muted);
  font-size: 13px;
}

.management-table {
  width: 100%;
  border: 1px solid var(--library-border);
  border-radius: 14px;
  overflow: hidden;
}

.management-table :deep(.cell) {
  padding-inline: 16px;
}

.pagination-row {
  min-height: 58px;
  justify-content: space-between;
  gap: 20px;
  padding-top: 18px;
}
</style>
