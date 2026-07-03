<template>
  <section class="borrow-card">
    <div class="tabs-bar">
      <el-radio-group v-model="status" class="borrow-tabs" @change="fetchData">
        <el-radio-button value="">
          全部
          <span class="tab-count">
            {{ counts.pending + counts.borrowed + counts.overdue + counts.returned + counts.rejected }}
          </span>
        </el-radio-button>
        <el-radio-button value="pending">
          待审核
          <span class="tab-count">{{ counts.pending }}</span>
        </el-radio-button>
        <el-radio-button value="borrowed">
          在借
          <span class="tab-count">{{ counts.borrowed }}</span>
        </el-radio-button>
        <el-radio-button value="overdue">
          逾期
          <span class="tab-count">{{ counts.overdue }}</span>
        </el-radio-button>
        <el-radio-button value="returned">
          已归还
          <span class="tab-count">{{ counts.returned }}</span>
        </el-radio-button>
      </el-radio-group>
    </div>

    <div class="table-wrap">
      <el-table :data="borrows" class="borrows-table" empty-text="暂无借阅记录">
        <el-table-column prop="book_title" label="图书" min-width="260">
          <template #default="{ row }">
            <span class="book-title">{{ row.book_title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status_text" label="状态" min-width="120">
          <template #default="{ row }">
            <el-tag :class="['status-tag', `status-${row.status}`]" effect="plain">
              {{ row.status_text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="borrow_time" label="借阅时间" min-width="180" />
        <el-table-column prop="due_time" label="到期日" min-width="140">
          <template #default="{ row }">
            <span :class="{ 'overdue-date': row.status === 'overdue' }">
              {{ row.due_time || '—' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="return_time" label="归还时间" min-width="180">
          <template #default="{ row }">
            <span>{{ row.return_time || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'borrowed' || row.status === 'overdue'"
              class="renew-button"
              size="small"
              @click="renew(row)"
            >
              续借
            </el-button>
            <span v-else class="no-action">—</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="table-footer">
      <span class="total-count">共 {{ total }} 条记录</span>
      <el-pagination
        v-model:current-page="page"
        :total="total"
        :page-size="10"
        layout="prev,pager,next"
        background
        @current-change="fetchData"
      />
    </div>
  </section>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { borrowApi } from '../../api/auth'

const borrows = ref([])
const page = ref(1)
const total = ref(0)
const status = ref('')
const counts = reactive({ pending: 0, borrowed: 0, overdue: 0, returned: 0, rejected: 0 })

onMounted(() => fetchData())

async function fetchData() {
  const r = await borrowApi.myBorrows({ page: page.value, status: status.value })
  borrows.value = r.data.list; total.value = r.data.total
  if (r.data.counts) Object.assign(counts, r.data.counts)
}

async function renew(row) {
  try { await borrowApi.renew(row.id); ElMessage.success('续借成功'); fetchData() } catch (e) { /* handled */ }
}
</script>

<style scoped>
.borrow-card {
  overflow: hidden;
  border: 1px solid var(--library-border);
  border-radius: 16px;
  background: #fff;
  box-shadow: var(--library-card-shadow);
}

.tabs-bar {
  display: flex;
  align-items: center;
  min-height: 88px;
  padding: 18px 24px;
  border-bottom: 1px solid #e8edf4;
}

.borrow-tabs {
  display: inline-flex;
  gap: 4px;
  padding: 5px;
  border: 1px solid var(--library-border);
  border-radius: 13px;
  background: #f4f7fb;
}

.borrow-tabs :deep(.el-radio-button__inner) {
  display: inline-flex;
  height: 40px;
  align-items: center;
  gap: 5px;
  padding: 0 17px;
  border: 0 !important;
  border-radius: 9px !important;
  color: #718096;
  background: transparent;
  box-shadow: none !important;
  font-size: 15px;
  font-weight: 500;
  transition: color 160ms ease, background-color 160ms ease, box-shadow 160ms ease;
}

.borrow-tabs :deep(.el-radio-button__inner:hover) {
  color: var(--library-primary);
}

.borrow-tabs :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  color: var(--library-primary);
  background: #fff;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08) !important;
}

.tab-count {
  color: #9aa7b8;
  font-size: 12px;
  font-weight: 600;
}

.borrow-tabs :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) .tab-count {
  color: #7d9cff;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
}

.borrows-table {
  width: 100%;
  min-width: 940px;
}

.book-title {
  color: #111827;
  font-weight: 500;
}

.status-tag {
  height: 28px;
  padding: 0 12px;
  border: 0;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 500;
  line-height: 28px;
}

.status-returned {
  color: #059669;
  background: #e8f8f1;
}

.status-borrowed {
  color: var(--library-primary);
  background: #ebf1ff;
}

.status-overdue {
  color: #dc2626;
  background: #feecec;
}

.status-pending {
  color: #d97706;
  background: #fff6dd;
}

.status-rejected {
  color: #64748b;
  background: #f1f4f8;
}

.overdue-date {
  color: #dc2626;
  font-weight: 500;
}

.renew-button {
  min-width: 64px;
  height: 34px;
  padding: 0 15px;
  border-color: #bfd0ff;
  border-radius: 9px;
  color: var(--library-primary);
  background: #fff;
  font-weight: 500;
}

.renew-button:hover,
.renew-button:focus {
  border-color: var(--library-primary);
  color: #fff;
  background: var(--library-primary);
}

.no-action {
  color: #a7b1bf;
}

.table-footer {
  display: flex;
  min-height: 72px;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  border-top: 1px solid #e8edf4;
}

.total-count {
  color: #718096;
  font-size: 14px;
}

</style>
