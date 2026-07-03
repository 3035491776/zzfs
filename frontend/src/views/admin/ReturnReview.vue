<template>
  <div>
    <h2>归还管理</h2>
    <el-table :data="borrows" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="student_name" label="借阅人" width="100" />
      <el-table-column prop="book_title" label="图书" />
      <el-table-column prop="status_text" label="状态" width="80" />
      <el-table-column prop="due_time" label="到期日" width="100" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }"><el-button size="small" type="primary" @click="returnBook(row)">确认归还</el-button></template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="10" layout="prev,pager,next" @current-change="fetchData" style="margin-top:20px" />
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
