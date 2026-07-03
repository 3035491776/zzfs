<template>
  <div>
    <h2>借阅审核</h2>
    <el-radio-group v-model="status" @change="fetchData" style="margin:20px 0">
      <el-radio-button value="pending">待审核</el-radio-button>
      <el-radio-button value="borrowed">在借</el-radio-button>
      <el-radio-button value="overdue">逾期</el-radio-button>
      <el-radio-button value="returned">已归还</el-radio-button>
      <el-radio-button value="rejected">已驳回</el-radio-button>
    </el-radio-group>
    <el-table :data="borrows" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="student_name" label="借阅人" width="100" />
      <el-table-column prop="book_title" label="图书" />
      <el-table-column prop="status_text" label="状态" width="80" />
      <el-table-column prop="borrow_time" label="借阅时间" width="160" />
      <el-table-column prop="due_time" label="到期日" width="100" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button v-if="row.status==='pending'" size="small" type="success" @click="approve(row)">通过</el-button>
          <el-button v-if="row.status==='pending'" size="small" type="danger" @click="reject(row)">驳回</el-button>
          <el-button v-if="row.status==='borrowed'||row.status==='overdue'" size="small" type="primary" @click="returnBook(row)">确认归还</el-button>
        </template>
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
