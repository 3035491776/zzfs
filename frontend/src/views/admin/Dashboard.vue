<template>
  <div class="dashboard-page">
    <el-row :gutter="16" class="stat-grid">
      <el-col :span="6" v-for="(card, index) in cards" :key="card.label">
        <el-card shadow="never" class="stat-card">
          <div class="stat-card__top">
            <span class="stat-index">0{{ index + 1 }}</span>
            <span class="stat-label">{{ card.label }}</span>
          </div>
          <strong class="stat-value">{{ card.value }}</strong>
          <span class="stat-note">{{ card.note }}</span>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="dashboard-grid">
      <el-col :span="12" class="panel-col">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-heading">
              <div>
                <h3>借阅趋势</h3>
                <p>馆藏图书月度借阅变化</p>
              </div>
              <span class="panel-mark" aria-hidden="true">趋</span>
            </div>
          </template>
          <div ref="trendChart" class="chart-shell"></div>
        </el-card>
      </el-col>
      <el-col :span="12" class="panel-col">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-heading">
              <div>
                <h3>分类借阅占比</h3>
                <p>各图书分类借阅分布</p>
              </div>
              <span class="panel-mark" aria-hidden="true">类</span>
            </div>
          </template>
          <div ref="pieChart" class="chart-shell"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="dashboard-grid">
      <el-col :span="12" class="panel-col">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-heading">
              <div>
                <h3>热门图书 TOP10</h3>
                <p>近期馆藏借阅热度排行</p>
              </div>
              <span class="panel-mark" aria-hidden="true">榜</span>
            </div>
          </template>
          <el-table :data="popularBooks" stripe size="small" height="320">
            <el-table-column prop="title" label="书名" />
            <el-table-column prop="author" label="作者" width="150" />
            <el-table-column prop="borrow_count" label="借阅次数" width="100" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12" class="panel-col">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-heading">
              <div>
                <h3>座位使用情况</h3>
                <p>当前自习座位实时状态</p>
              </div>
              <span class="panel-mark panel-mark--success" aria-hidden="true">座</span>
            </div>
          </template>
          <div ref="seatChart" class="chart-shell"></div>
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
  { label: '馆藏册数', value: 0, note: '等待 V2 数据' },
  { label: '周期借阅', value: 0, note: '等待 V2 数据' },
  { label: '期末逾期', value: 0, note: '等待 V2 数据' },
  { label: '座位利用率', value: '—', note: '等待 V2 数据' },
])

const popularBooks = ref([])
const trendChart = ref(null)
const pieChart = ref(null)
const seatChart = ref(null)

onMounted(async () => {
  // Stats
  const stats = await dashboardApi.stats()
  const s = stats.data
  const sourceNote = s.source === 'snapshot'
    ? `V2 Snapshot · ${String(s.period_start || '').slice(0, 10)}`
    : '实时兼容数据'
  cards[0].value = s.total_stock
  cards[1].value = s.total_borrowed
  cards[2].value = s.total_overdue
  cards[3].value = s.seat_utilization_rate == null
    ? '—'
    : `${Number(s.seat_utilization_rate).toFixed(1)}%`
  cards.forEach(card => { card.note = sourceNote })

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

<style scoped>
.dashboard-page {
  width: 100%;
  max-width: 1480px;
  margin: 0 auto;
}

.stat-grid {
  margin-bottom: 20px;
}

.stat-card :deep(.el-card__body) {
  min-height: 154px;
  padding: 22px 24px;
}

.stat-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.stat-index {
  display: inline-flex;
  height: 26px;
  align-items: center;
  padding: 0 9px;
  border-radius: 8px;
  color: var(--library-primary);
  background: #edf3ff;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.stat-label {
  color: var(--library-muted);
  font-size: 14px;
  font-weight: 500;
}

.stat-value {
  display: block;
  margin-top: 17px;
  color: var(--library-primary);
  font-size: 34px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.03em;
}

.stat-note {
  display: block;
  margin-top: 9px;
  color: #9aa5b5;
  font-size: 12px;
}

.stat-grid :deep(.el-col:nth-child(3)) .stat-index {
  color: var(--library-danger);
  background: #fff0f0;
}

.stat-grid :deep(.el-col:nth-child(3)) .stat-value {
  color: var(--library-danger);
}

.stat-grid :deep(.el-col:nth-child(4)) .stat-index {
  color: var(--library-success);
  background: #eafaf4;
}

.stat-grid :deep(.el-col:nth-child(4)) .stat-value {
  color: var(--library-success);
}

.dashboard-grid {
  margin-top: 20px;
}

.panel-col {
  display: flex;
}

.panel-card {
  width: 100%;
}

.panel-card :deep(.el-card__header) {
  min-height: 74px;
  padding: 16px 22px;
  border-bottom-color: var(--library-border);
}

.panel-card :deep(.el-card__body) {
  padding: 18px 22px 22px;
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.panel-heading h3 {
  margin: 0;
  color: var(--library-text);
  font-size: 17px;
  font-weight: 700;
}

.panel-heading p {
  margin: 5px 0 0;
  color: var(--library-muted);
  font-size: 12px;
}

.panel-mark {
  display: grid;
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  place-items: center;
  border-radius: 11px;
  color: var(--library-primary);
  background: #edf3ff;
  font-size: 13px;
  font-weight: 700;
}

.panel-mark--success {
  color: var(--library-success);
  background: #eafaf4;
}

.chart-shell {
  width: 100%;
  height: 320px;
}
</style>
