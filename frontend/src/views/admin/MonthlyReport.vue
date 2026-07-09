<template>
  <div class="monthly-report-page">
    <el-card shadow="never" class="report-toolbar">
      <div class="toolbar-copy">
        <el-tag type="info" effect="plain">前端预览版</el-tag>
        <div>
          <h2>月度运营报告</h2>
          <p>使用 mock 数据预览图书馆上月运营情况，暂未接入后端与真实 AI。</p>
        </div>
      </div>

      <div class="toolbar-actions">
        <el-date-picker
          v-model="selectedMonth"
          type="month"
          value-format="YYYY-MM"
          placeholder="选择月份"
          :clearable="false"
          class="month-picker"
        />
        <el-button type="primary" @click="generateReport">
          <el-icon><DataAnalysis /></el-icon>
          <span>生成报告</span>
        </el-button>
        <el-button class="export-button" disabled>
          <el-icon><Download /></el-icon>
          <span>导出报告</span>
        </el-button>
      </div>
    </el-card>

    <el-row :gutter="16" class="stat-grid">
      <el-col v-for="(card, index) in statCards" :key="card.label" :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-card__top">
            <span class="stat-index">0{{ index + 1 }}</span>
            <el-tag :type="card.tagType" effect="light">{{ card.trend }}</el-tag>
          </div>
          <strong>{{ card.value }}</strong>
          <span>{{ card.label }}</span>
          <p>{{ card.note }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="report-grid">
      <el-col :span="14" class="panel-col">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-heading">
              <div>
                <h3>热门图书 Top10</h3>
                <p>按上月借阅次数排序，辅助采购与陈列调整。</p>
              </div>
              <span class="panel-mark">书</span>
            </div>
          </template>

          <el-table :data="popularBooks" stripe class="report-table" height="420">
            <el-table-column type="index" label="#" width="64" />
            <el-table-column prop="title" label="图书" min-width="180">
              <template #default="{ row }">
                <div class="book-title">
                  <strong>{{ row.title }}</strong>
                  <span>{{ row.author }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="130">
              <template #default="{ row }">
                <el-tag effect="plain">{{ row.category }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="borrows" label="借阅" width="100" />
            <el-table-column prop="stock" label="库存" width="90" />
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="row.stock <= 2 ? 'danger' : 'success'" effect="light">
                  {{ row.stock <= 2 ? '需关注' : '稳定' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="10" class="panel-col">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-heading">
              <div>
                <h3>热门分类</h3>
                <p>本月借阅偏好分布。</p>
              </div>
              <span class="panel-mark panel-mark--success">类</span>
            </div>
          </template>

          <div ref="categoryChartRef" class="chart-shell"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="report-grid">
      <el-col :span="10" class="panel-col">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-heading">
              <div>
                <h3>断货风险图书</h3>
                <p>借阅热度高且库存偏低的重点书目。</p>
              </div>
              <span class="panel-mark panel-mark--danger">缺</span>
            </div>
          </template>

          <div class="risk-list">
            <div v-for="book in stockRiskBooks" :key="book.title" class="risk-item">
              <div>
                <strong>{{ book.title }}</strong>
                <span>{{ book.reason }}</span>
              </div>
              <el-tag type="danger" effect="light">库存 {{ book.stock }}</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="14" class="panel-col">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-heading">
              <div>
                <h3>座位分析</h3>
                <p>热门座位、自习室、高峰时段与功能偏好。</p>
              </div>
              <span class="panel-mark">座</span>
            </div>
          </template>

          <div class="seat-analysis">
            <div class="seat-chart-wrap">
              <div ref="seatChartRef" class="chart-shell chart-shell--compact"></div>
            </div>
            <div class="seat-insights">
              <section>
                <span>热门座位</span>
                <strong>B201-01、B201-02</strong>
              </section>
              <section>
                <span>热门自习室</span>
                <strong>B201 自习室</strong>
              </section>
              <section>
                <span>高峰时段</span>
                <strong>19:00 - 21:00</strong>
              </section>
              <section>
                <span>功能偏好</span>
                <strong>带电源座位预约占比 68%</strong>
              </section>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="report-grid">
      <el-col :span="12" class="panel-col">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="panel-heading">
              <div>
                <h3>用户行为</h3>
                <p>学生/教师占比、续借与荐购活跃度。</p>
              </div>
              <span class="panel-mark panel-mark--success">人</span>
            </div>
          </template>

          <div class="behavior-layout">
            <div ref="userChartRef" class="chart-shell chart-shell--compact"></div>
            <div class="behavior-metrics">
              <div v-for="item in behaviorMetrics" :key="item.label" class="behavior-item">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
                <p>{{ item.note }}</p>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12" class="panel-col">
        <el-card shadow="never" class="panel-card ai-card">
          <template #header>
            <div class="panel-heading">
              <div>
                <h3>AI 运营建议</h3>
                <p>当前为 mock 文本，暂未调用真实 AI。</p>
              </div>
              <span class="panel-mark">AI</span>
            </div>
          </template>

          <div class="ai-summary">
            <el-tag type="warning" effect="light">Mock 建议</el-tag>
            <p v-for="tip in aiSuggestions" :key="tip">{{ tip }}</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

const selectedMonth = ref('2026-06')
const categoryChartRef = ref(null)
const seatChartRef = ref(null)
const userChartRef = ref(null)
const chartInstances = []

const statCards = [
  { label: '上月借阅总数', value: '1,286', trend: '环比 +12%', tagType: 'success', note: '计算机与人工智能类增长明显' },
  { label: '活跃用户', value: '842', trend: '活跃', tagType: 'primary', note: '学生 706 人，教师 136 人' },
  { label: '座位预约', value: '2,418', trend: '高峰稳定', tagType: 'warning', note: '晚间预约占比最高' },
  { label: '逾期数量', value: '37', trend: '需跟进', tagType: 'danger', note: '较上月减少 9 本' },
]

const popularBooks = [
  { title: '《算法导论》', author: 'Thomas H. Cormen', category: '计算机', borrows: 96, stock: 2 },
  { title: '《人工智能》', author: 'Stuart Russell', category: '人工智能', borrows: 88, stock: 3 },
  { title: '《计算机网络》', author: '谢希仁', category: '计算机', borrows: 83, stock: 4 },
  { title: '《数据库系统概念》', author: 'Abraham Silberschatz', category: '数据库', borrows: 76, stock: 2 },
  { title: '《深入理解计算机系统》', author: 'Randal E. Bryant', category: '计算机', borrows: 71, stock: 5 },
  { title: '《机器学习》', author: '周志华', category: '人工智能', borrows: 69, stock: 3 },
  { title: '《现代操作系统》', author: 'Andrew S. Tanenbaum', category: '操作系统', borrows: 64, stock: 4 },
  { title: '《软件工程》', author: 'Ian Sommerville', category: '软件工程', borrows: 58, stock: 6 },
  { title: '《Python 编程》', author: 'Eric Matthes', category: '编程语言', borrows: 53, stock: 3 },
  { title: '《数据结构》', author: '严蔚敏', category: '计算机', borrows: 49, stock: 7 },
]

const stockRiskBooks = [
  { title: '《算法导论》', stock: 2, reason: '借阅 96 次，预约排队 14 人' },
  { title: '《数据库系统概念》', stock: 2, reason: '借阅 76 次，课程周需求上升' },
  { title: '《机器学习》', stock: 3, reason: 'AI 方向持续热门，库存偏紧' },
]

const behaviorMetrics = [
  { label: '续借次数', value: '214', note: '计算机类图书续借最多' },
  { label: '荐购申请', value: '43', note: 'AI、考研、工程实践类占比高' },
  { label: '教师借阅', value: '18%', note: '教师用户更偏好教材与专业参考书' },
]

const aiSuggestions = [
  '建议优先补采《算法导论》《数据库系统概念》《机器学习》，这些图书借阅热度高且库存低。',
  'B201 自习室晚间使用率持续偏高，可考虑增加带电源座位或优化预约时段提示。',
  '荐购内容集中在 AI 与工程实践方向，建议下月采购计划向应用型技术书籍倾斜。',
]

function generateReport() {
  ElMessage.success(`${selectedMonth.value} 月度报告已使用 mock 数据刷新`)
}

function createChart(el, options) {
  if (!el) return
  const chart = echarts.init(el)
  chart.setOption(options)
  chartInstances.push(chart)
}

function initCharts() {
  createChart(categoryChartRef.value, {
    color: ['#3366ff', '#059669', '#d97706', '#7c3aed', '#dc2626'],
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, icon: 'circle' },
    series: [{
      type: 'pie',
      radius: ['46%', '70%'],
      center: ['50%', '44%'],
      label: { formatter: '{b}\\n{d}%' },
      data: [
        { name: '计算机', value: 38 },
        { name: '人工智能', value: 24 },
        { name: '数据库', value: 14 },
        { name: '软件工程', value: 13 },
        { name: '其他', value: 11 },
      ],
    }],
  })

  createChart(seatChartRef.value, {
    color: ['#3366ff', '#059669', '#d97706'],
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 18, top: 24, bottom: 34 },
    xAxis: { type: 'category', data: ['08-10', '10-12', '14-16', '16-18', '19-21'] },
    yAxis: { type: 'value' },
    series: [{
      name: '预约次数',
      type: 'bar',
      barWidth: 22,
      data: [168, 246, 318, 402, 586],
      itemStyle: { borderRadius: [8, 8, 0, 0] },
    }],
  })

  createChart(userChartRef.value, {
    color: ['#3366ff', '#059669'],
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, icon: 'circle' },
    series: [{
      type: 'pie',
      radius: ['50%', '72%'],
      center: ['50%', '44%'],
      label: { formatter: '{b} {d}%' },
      data: [
        { name: '学生', value: 82 },
        { name: '教师', value: 18 },
      ],
    }],
  })
}

function resizeCharts() {
  chartInstances.forEach(chart => chart.resize())
}

onMounted(async () => {
  await nextTick()
  initCharts()
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  chartInstances.forEach(chart => chart.dispose())
})
</script>

<style scoped>
.monthly-report-page {
  width: 100%;
  max-width: 1480px;
  margin: 0 auto;
}

.report-toolbar {
  margin-bottom: 20px;
}

.report-toolbar :deep(.el-card__body),
.toolbar-copy,
.toolbar-actions,
.stat-card__top,
.panel-heading,
.risk-item,
.seat-analysis,
.behavior-layout {
  display: flex;
  align-items: center;
}

.report-toolbar :deep(.el-card__body) {
  min-height: 104px;
  justify-content: space-between;
  gap: 24px;
  padding: 20px 24px;
}

.toolbar-copy {
  min-width: 0;
  gap: 16px;
}

.toolbar-copy h2,
.toolbar-copy p,
.panel-heading h3,
.panel-heading p,
.ai-summary p,
.risk-item strong,
.risk-item span,
.behavior-item p {
  margin: 0;
}

.toolbar-copy h2 {
  color: var(--library-text);
  font-size: 21px;
  font-weight: 700;
}

.toolbar-copy p,
.panel-heading p,
.risk-item span,
.behavior-item span,
.behavior-item p,
.seat-insights span {
  color: var(--library-muted);
  font-size: 12px;
}

.toolbar-actions {
  flex-shrink: 0;
  gap: 10px;
}

.month-picker {
  width: 150px;
}

.export-button.is-disabled {
  background: #f7f9fc;
}

.stat-grid {
  margin-bottom: 20px;
}

.stat-card :deep(.el-card__body) {
  min-height: 166px;
  padding: 22px 24px;
}

.stat-card__top {
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

.stat-card strong {
  display: block;
  margin-top: 18px;
  color: var(--library-primary);
  font-size: 34px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.03em;
}

.stat-card > :deep(.el-card__body) > span:not(.stat-index) {
  display: block;
  margin-top: 10px;
  color: var(--library-text);
  font-size: 15px;
  font-weight: 700;
}

.stat-card p {
  margin: 8px 0 0;
  color: #9aa5b5;
  font-size: 12px;
}

.report-grid {
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
  justify-content: space-between;
  gap: 18px;
}

.panel-heading h3 {
  color: var(--library-text);
  font-size: 17px;
  font-weight: 700;
}

.panel-heading p {
  margin-top: 5px;
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

.panel-mark--danger {
  color: var(--library-danger);
  background: #fff0f0;
}

.report-table {
  width: 100%;
  border: 1px solid var(--library-border);
  border-radius: 14px;
  overflow: hidden;
}

.book-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.book-title strong {
  color: var(--library-text);
  font-size: 14px;
}

.book-title span {
  color: var(--library-muted);
  font-size: 12px;
}

.chart-shell {
  width: 100%;
  height: 340px;
}

.chart-shell--compact {
  height: 276px;
}

.risk-list {
  display: grid;
  gap: 12px;
}

.risk-item {
  min-height: 78px;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
  border: 1px solid var(--library-border);
  border-radius: 14px;
  background: #fbfcfe;
}

.risk-item > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 6px;
}

.risk-item strong {
  color: var(--library-text);
  font-size: 14px;
}

.seat-analysis {
  align-items: stretch;
  gap: 22px;
}

.seat-chart-wrap {
  min-width: 0;
  flex: 1;
}

.seat-insights,
.behavior-metrics {
  display: grid;
  gap: 12px;
}

.seat-insights {
  width: 260px;
}

.seat-insights section,
.behavior-item {
  padding: 15px 16px;
  border: 1px solid var(--library-border);
  border-radius: 14px;
  background: #fbfcfe;
}

.seat-insights strong,
.behavior-item strong {
  display: block;
  margin-top: 6px;
  color: var(--library-text);
  font-size: 15px;
  font-weight: 700;
}

.behavior-layout {
  align-items: stretch;
  gap: 20px;
}

.behavior-layout .chart-shell {
  flex: 1;
  min-width: 0;
}

.behavior-metrics {
  width: 220px;
}

.behavior-item p {
  margin-top: 6px;
  line-height: 1.55;
}

.ai-card :deep(.el-card__body) {
  min-height: 320px;
}

.ai-summary {
  display: grid;
  gap: 14px;
}

.ai-summary p {
  padding: 15px 16px;
  border: 1px solid var(--library-border);
  border-radius: 14px;
  color: #52627a;
  background: #fbfcfe;
  font-size: 14px;
  line-height: 1.7;
}
</style>
