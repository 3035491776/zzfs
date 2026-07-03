<template>
  <div>
    <h2>数据大屏</h2>
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="6" v-for="card in cards" :key="card.label">
        <el-card shadow="hover">
          <div style="text-align:center">
            <div style="font-size:14px;color:#909399">{{ card.label }}</div>
            <div style="font-size:32px;font-weight:bold;color:#409EFF;margin:8px 0">{{ card.value }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="12">
        <el-card><template #header>借阅趋势</template><div ref="trendChart" style="height:300px"></div></el-card>
      </el-col>
      <el-col :span="12">
        <el-card><template #header>分类借阅占比</template><div ref="pieChart" style="height:300px"></div></el-card>
      </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="12">
        <el-card><template #header>热门图书 TOP10</template>
          <el-table :data="popularBooks" stripe size="small">
            <el-table-column prop="title" label="书名" />
            <el-table-column prop="author" label="作者" width="150" />
            <el-table-column prop="borrow_count" label="借阅次数" width="100" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card><template #header>座位使用情况</template>
          <div ref="seatChart" style="height:300px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import * as echarts from 'echarts'
import { dashboardApi } from '../../api/auth'

const cards = reactive([
  { label: '图书种类', value: 0 },
  { label: '在借图书', value: 0 },
  { label: '逾期图书', value: 0 },
  { label: '可用座位', value: 0 },
])

const popularBooks = ref([])
const trendChart = ref(null)
const pieChart = ref(null)
const seatChart = ref(null)

onMounted(async () => {
  // Stats
  const stats = await dashboardApi.stats()
  const s = stats.data
  cards[0].value = s.total_books
  cards[1].value = s.total_borrowed
  cards[2].value = s.total_overdue
  cards[3].value = s.available_seats

  // Trend chart
  const trend = await dashboardApi.borrowTrend()
  const trendInstance = echarts.init(trendChart.value)
  trendInstance.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: trend.data.trend.map(t => t.month) },
    yAxis: { type: 'value' },
    series: [{ data: trend.data.trend.map(t => t.count), type: 'line', smooth: true, areaStyle: {} }],
  })

  // Pie chart
  const cat = await dashboardApi.categoryChart()
  const pieInstance = echarts.init(pieChart.value)
  pieInstance.setOption({
    tooltip: { trigger: 'item' },
    series: [{ type: 'pie', radius: ['40%', '70%'], data: cat.data.chart }],
  })

  // Popular books
  const pop = await dashboardApi.popularBooks()
  popularBooks.value = pop.data.list

  // Seat usage
  const seat = await dashboardApi.seatUsage()
  const seatInstance = echarts.init(seatChart.value)
  seatInstance.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie', radius: '70%',
      data: [
        { name: '可用', value: seat.data.available },
        { name: '已占用', value: seat.data.occupied },
        { name: '维护中', value: seat.data.maintenance },
      ],
    }],
  })
})
</script>
