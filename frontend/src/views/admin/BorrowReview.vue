<template>
  <div class="borrow-review-page">
    <el-card shadow="never" class="workspace-card">
      <template #header>
        <div class="section-heading">
          <div>
            <h3>借阅审核</h3>
            <p>审核借阅申请并跟踪馆藏流转状态</p>
          </div>
        </div>
      </template>

      <div class="status-filter">
        <div class="filter-copy">
          <strong>借阅状态</strong>
          <span>按当前处理状态筛选借阅记录</span>
        </div>
        <el-radio-group v-model="status" class="status-switch" @change="fetchData">
          <el-radio-button value="pending">待审核</el-radio-button>
          <el-radio-button value="borrowed">在借</el-radio-button>
          <el-radio-button value="overdue">逾期</el-radio-button>
          <el-radio-button value="returned">已归还</el-radio-button>
          <el-radio-button value="rejected">已驳回</el-radio-button>
        </el-radio-group>
      </div>

      <el-table :data="borrows" stripe class="management-table">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="student_name" label="借阅人" width="120" />
        <el-table-column prop="book_title" label="图书" min-width="180" show-overflow-tooltip />
        <el-table-column prop="status_text" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'returned' ? 'success' : row.status === 'rejected' || row.status === 'overdue' ? 'danger' : row.status === 'pending' ? 'warning' : 'primary'"
              effect="plain"
            >
              {{ row.status_text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="borrow_time" label="借阅时间" width="170" />
        <el-table-column prop="due_time" label="到期日" width="120" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" size="small" type="primary" @click="approve(row)">通过</el-button>
            <el-button v-if="row.status === 'pending'" size="small" type="danger" @click="reject(row)">驳回</el-button>
            <el-button v-if="row.status === 'borrowed' || row.status === 'overdue'" size="small" type="primary" @click="returnBook(row)">确认归还</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-row">
        <span>共 {{ total }} 条借阅记录</span>
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
import { borrowApi } from '../../api/auth'

const borrows = ref([])
const page = ref(1)
const total = ref(0)
const status = ref('pending')

onMounted(() => fetchData())

async function fetchData() {
  const r = await borrowApi.list({ page: page.value, status: status.value, scope: 'all' })
  borrows.value = r.data.list
  total.value = r.data.total
}

async function approve(row) { try { await borrowApi.approve(row.id); ElMessage.success('已通过'); fetchData() } catch (e) { /* handled */ } }
async function reject(row) { try { await borrowApi.reject(row.id); ElMessage.success('已驳回'); fetchData() } catch (e) { /* handled */ } }
async function returnBook(row) { try { await borrowApi.return(row.id); ElMessage.success('已归还'); fetchData() } catch (e) { /* handled */ } }
</script>

<style scoped>
.borrow-review-page {
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
.status-filter,
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

.status-filter {
  min-height: 72px;
  justify-content: space-between;
  gap: 24px;
  padding: 14px 16px;
  margin-bottom: 18px;
  border: 1px solid var(--library-border);
  border-radius: 14px;
  background: #f9fbfd;
}

.filter-copy {
  display: flex;
  min-width: 180px;
  flex-direction: column;
}

.filter-copy strong {
  color: var(--library-text);
  font-size: 15px;
  font-weight: 700;
}

.filter-copy span {
  margin-top: 4px;
  color: var(--library-muted);
  font-size: 12px;
}

.status-switch {
  width: auto;
  flex-shrink: 0;
}

.status-switch :deep(.el-radio-button__inner) {
  min-width: 76px;
  border-color: var(--library-border);
  color: #667085;
  font-weight: 600;
}

.status-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  border-color: var(--library-primary);
  color: #fff;
  background: var(--library-primary);
  box-shadow: -1px 0 0 0 var(--library-primary);
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

.pagination-row > span {
  color: var(--library-muted);
  font-size: 13px;
}
</style>
