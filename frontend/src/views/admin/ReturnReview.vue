<template>
  <div class="return-review-page">
    <el-card shadow="never" class="workspace-card">
      <template #header>
        <div class="section-heading">
          <div>
            <h3>归还管理</h3>
            <p>核对当前在借记录并完成图书归还入库</p>
          </div>
        </div>
      </template>

      <el-table :data="borrows" stripe class="management-table">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="student_name" label="借阅人" width="120" />
        <el-table-column prop="book_title" label="图书" min-width="220" show-overflow-tooltip />
        <el-table-column prop="status_text" label="状态" width="110">
          <template #default="{ row }">
            <el-tag type="primary" effect="plain">{{ row.status_text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="due_time" label="到期日" width="140" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="returnBook(row)">确认归还</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-row">
        <span>共 {{ total }} 条待归还记录</span>
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

onMounted(() => fetchData())

async function fetchData() {
  const r = await borrowApi.list({ page: page.value, status: 'borrowed', scope: 'all' })
  borrows.value = r.data.list
  total.value = r.data.total
}

async function returnBook(row) { try { await borrowApi.return(row.id); ElMessage.success('已归还'); fetchData() } catch (e) { /* handled */ } }
</script>

<style scoped>
.return-review-page {
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
