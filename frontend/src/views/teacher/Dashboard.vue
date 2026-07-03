<template>
  <div>
    <h2>教师首页</h2>
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="8"><el-card shadow="hover"><div style="text-align:center"><div style="color:#909399;font-size:14px">在架图书</div><div style="font-size:36px;color:#409EFF;font-weight:bold">{{ stats.total_books }}</div></div></el-card></el-col>
      <el-col :span="8"><el-card shadow="hover"><div style="text-align:center"><div style="color:#909399;font-size:14px">我的在借</div><div style="font-size:36px;color:#67C23A;font-weight:bold">{{ myBorrowCount }}</div></div></el-card></el-col>
      <el-col :span="8"><el-card shadow="hover"><div style="text-align:center"><div style="color:#909399;font-size:14px">可用座位</div><div style="font-size:36px;color:#E6A23C;font-weight:bold">{{ stats.available_seats }}</div></div></el-card></el-col>
    </el-row>
    <el-card style="margin-top:20px"><template #header>最近图书</template>
      <el-table :data="recentBooks" stripe><el-table-column prop="title" label="书名" /><el-table-column prop="author" label="作者" /><el-table-column prop="category_name" label="分类" /></el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { dashboardApi, bookApi, borrowApi } from '../../api/auth'

const stats = ref({ total_books: 0, available_seats: 0 })
const recentBooks = ref([])
const myBorrowCount = ref(0)

onMounted(async () => {
  const s = await dashboardApi.stats(); stats.value = s.data
  const b = await bookApi.list({ page: 1 }); recentBooks.value = b.data.list.slice(0, 5)
  const br = await borrowApi.myBorrows({ status: 'borrowed' }); myBorrowCount.value = br.data.total
})
</script>
