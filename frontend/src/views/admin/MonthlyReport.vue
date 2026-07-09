<template>
  <div v-loading="loading" class="monthly-report-page">
    <el-card shadow="never" class="report-toolbar">
      <div class="toolbar-copy">
        <el-tag :type="isFallbackData ? 'warning' : 'success'" effect="plain">
          {{ isFallbackData ? '演示数据' : '真实数据' }}
        </el-tag>
        <div>
          <h2>月度运营报告</h2>
          <p>{{ toolbarDescription }}</p>
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
        <el-button type="primary" :loading="loading" @click="generateReport">
          <el-icon><DataAnalysis /></el-icon>
          <span>生成报告</span>
        </el-button>
        <el-button class="export-button" disabled title="导出功能暂未开放，当前仅为前端占位">
          <el-icon><Download /></el-icon>
          <span>导出报告（占位）</span>
        </el-button>
      </div>
    </el-card>

    <el-row :gutter="16" class="stat-grid">
      <el-col v-for="(card, index) in statCards" :key="card.label" :span="statCardSpan">
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

          <el-table :data="popularBooks" stripe class="report-table" height="420" empty-text="暂无热门图书数据">
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
            <el-table-column prop="borrow_count" label="借阅" width="100" />
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

          <el-empty v-if="stockRiskBooks.length === 0" description="暂无断货风险图书" />
          <div v-else class="risk-list">
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
                <strong>{{ seatInsight.hotSeats }}</strong>
              </section>
              <section>
                <span>热门自习室</span>
                <strong>{{ seatInsight.hotRooms }}</strong>
              </section>
              <section>
                <span>高峰时段</span>
                <strong>{{ seatInsight.peakHours }}</strong>
              </section>
              <section>
                <span>功能偏好</span>
                <strong>{{ seatInsight.featurePreference }}</strong>
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
                <p>基于当前月份真实统计数据生成，不影响原始统计展示。</p>
              </div>
              <div class="ai-heading-actions">
                <el-button type="primary" plain :loading="aiLoading" @click="generateAiAnalysis">
                  <el-icon><MagicStick /></el-icon>
                  <span>生成 AI 分析</span>
                </el-button>
                <span class="panel-mark">AI</span>
              </div>
            </div>
          </template>

          <div v-loading="aiLoading" class="ai-summary">
            <el-alert
              v-if="aiError"
              :title="aiError"
              type="warning"
              show-icon
              :closable="false"
              class="ai-alert"
            />
            <el-tag :type="aiAnalysis ? 'success' : 'warning'" effect="light">
              {{ aiAnalysis ? 'AI 分析' : '默认提示' }}
            </el-tag>
            <p v-if="aiAnalysis" class="ai-report-text">{{ aiAnalysis }}</p>
            <template v-else>
              <p v-for="tip in defaultAiSuggestions" :key="tip">{{ tip }}</p>
            </template>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { reportApi } from '../../api/report'

const selectedMonth = ref(getPreviousMonth())
const loading = ref(false)
const aiLoading = ref(false)
const aiAnalysis = ref('')
const aiError = ref('')
const reportData = ref(createEmptyReport(selectedMonth.value))
const categoryChartRef = ref(null)
const seatChartRef = ref(null)
const userChartRef = ref(null)
const chartInstances = []

const isFallbackData = computed(() => reportData.value.is_mock === true)
const coreStats = computed(() => reportData.value.core_stats || {})
const bookAnalysis = computed(() => reportData.value.book_analysis || {})
const seatAnalysis = computed(() => reportData.value.seat_analysis || {})
const userBehavior = computed(() => reportData.value.user_behavior || {})

const toolbarDescription = computed(() => {
  if (isFallbackData.value) {
    return '统计接口请求失败，当前显示 devFallbackMock 演示数据；AI 分析以服务端真实统计为准，导出功能暂未开放。'
  }
  return `${reportData.value.range?.start || selectedMonth.value} 至 ${reportData.value.range?.end || selectedMonth.value} 的真实数据库统计；可按需生成 AI 运营分析，导出功能暂未开放。`
})

const statCards = computed(() => [
  {
    label: '上月借阅总数',
    value: formatNumber(coreStats.value.borrow_count),
    trend: hasValue(coreStats.value.borrow_count) ? '真实统计' : '暂无数据',
    tagType: hasValue(coreStats.value.borrow_count) ? 'success' : 'info',
    note: '按借阅审核通过时间统计',
  },
  {
    label: '活跃用户',
    value: formatNumber(coreStats.value.active_user_count),
    trend: '去重用户',
    tagType: 'primary',
    note: '借阅、预约、荐购用户去重',
  },
  {
    label: '座位预约',
    value: formatNumber(coreStats.value.reservation_count),
    trend: hasValue(coreStats.value.reservation_count) ? '真实统计' : '暂无数据',
    tagType: hasValue(coreStats.value.reservation_count) ? 'warning' : 'info',
    note: '按预约日期统计有效预约',
  },
  {
    label: '逾期数量',
    value: formatNumber(coreStats.value.overdue_count),
    trend: hasValue(coreStats.value.overdue_count) ? '需跟进' : '暂无逾期',
    tagType: hasValue(coreStats.value.overdue_count) ? 'danger' : 'success',
    note: '按到期时间落在当月统计',
  },
  {
    label: '荐购数量',
    value: formatNumber(coreStats.value.book_request_count),
    trend: hasValue(coreStats.value.book_request_count) ? '有需求' : '暂无数据',
    tagType: hasValue(coreStats.value.book_request_count) ? 'success' : 'info',
    note: '学生/教师荐购申请数',
  },
])

const statCardSpan = computed(() => (statCards.value.length >= 5 ? 4 : 6))
const popularBooks = computed(() => bookAnalysis.value.popular_books || [])
const stockRiskBooks = computed(() => bookAnalysis.value.stock_risk_books || [])

const seatInsight = computed(() => {
  const seats = seatAnalysis.value.popular_seats || []
  const rooms = seatAnalysis.value.popular_rooms || []
  const hours = seatAnalysis.value.peak_hours || []
  const preference = seatAnalysis.value.feature_preference || {}

  return {
    hotSeats: seats.length ? seats.slice(0, 2).map(item => item.seat_number).join('、') : '暂无数据',
    hotRooms: rooms.length ? rooms.slice(0, 2).map(item => item.room_name).join('、') : '暂无数据',
    peakHours: hours.length ? hours[0].label : '暂无数据',
    featurePreference: hasValue(preference.with_power_count) || hasValue(preference.without_power_count)
      ? `带电源座位预约占比 ${preference.with_power_ratio || 0}%`
      : '暂无数据',
  }
})

const behaviorMetrics = computed(() => {
  const roleDistribution = userBehavior.value.role_distribution || []
  const teacher = roleDistribution.find(item => item.role === 'teacher')

  return [
    {
      label: '续借次数',
      value: formatNumber(userBehavior.value.renew_count),
      note: '当月借阅记录中的续借次数合计',
    },
    {
      label: '荐购申请',
      value: formatNumber(userBehavior.value.book_request_count),
      note: '当月新增图书荐购申请',
    },
    {
      label: '教师活跃占比',
      value: `${teacher?.ratio || 0}%`,
      note: '基于借阅、预约、荐购活跃用户计算',
    },
  ]
})

const defaultAiSuggestions = computed(() => {
  if (isFallbackData.value) {
    return [
      '当前接口请求失败，以下仅为前端演示建议，不代表真实 AI 分析结果。',
      '恢复后端接口后，页面会自动展示数据库统计数据；本阶段仍不会调用真实 AI。',
      '导出功能仍为占位按钮，后续阶段再单独接入。',
    ]
  }

  const riskNames = stockRiskBooks.value.map(book => book.title).slice(0, 3).join('、')
  const hotRoom = seatInsight.value.hotRooms

  return [
    riskNames ? `可优先关注 ${riskNames} 的补采计划，这些书借阅热度较高且库存偏低。` : '当前月份暂无断货风险图书，可继续观察热门图书趋势。',
    hotRoom !== '暂无数据' ? `${hotRoom} 预约热度较高，可结合高峰时段优化座位开放策略。` : '当前月份暂无座位预约数据，座位运营建议暂不生成。',
    '以上为前端占位运营建议，不是由真实 AI 生成。',
  ]
})

async function generateReport() {
  await loadMonthlyReport()
}

async function generateAiAnalysis() {
  aiLoading.value = true
  aiError.value = ''

  try {
    const response = await reportApi.aiAnalysis(selectedMonth.value)
    aiAnalysis.value = response.data?.analysis || ''
    if (!aiAnalysis.value) {
      aiError.value = 'AI 未返回分析内容，已保留默认提示。'
      ElMessage.warning(aiError.value)
      return
    }
    ElMessage.success(`${selectedMonth.value} AI 运营分析已生成`)
  } catch (error) {
    aiAnalysis.value = ''
    aiError.value = error.response?.data?.message || 'AI 分析暂时不可用，已保留当前统计数据和默认提示。'
    ElMessage.warning(aiError.value)
  } finally {
    aiLoading.value = false
  }
}

function createChart(el, options) {
  if (!el) return
  const chart = echarts.init(el)
  chart.setOption(options)
  chartInstances.push(chart)
}

function initCharts() {
  chartInstances.forEach(chart => chart.dispose())
  chartInstances.length = 0

  const categories = bookAnalysis.value.categories || []
  const peakHours = seatAnalysis.value.peak_hours || []
  const roleDistribution = userBehavior.value.role_distribution || []

  createChart(categoryChartRef.value, {
    color: ['#3366ff', '#059669', '#d97706', '#7c3aed', '#dc2626'],
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, icon: 'circle' },
    title: buildEmptyTitle(categories.length === 0),
    series: [{
      type: 'pie',
      radius: ['46%', '70%'],
      center: ['50%', '44%'],
      label: { formatter: '{b}\\n{d}%' },
      data: categories.map(item => ({ name: item.name, value: item.value })),
    }],
  })

  createChart(seatChartRef.value, {
    color: ['#3366ff', '#059669', '#d97706'],
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 18, top: 24, bottom: 34 },
    title: buildEmptyTitle(peakHours.length === 0),
    xAxis: { type: 'category', data: peakHours.map(item => item.label) },
    yAxis: { type: 'value' },
    series: [{
      name: '预约次数',
      type: 'bar',
      barWidth: 22,
      data: peakHours.map(item => item.reservation_count),
      itemStyle: { borderRadius: [8, 8, 0, 0] },
    }],
  })

  createChart(userChartRef.value, {
    color: ['#3366ff', '#059669'],
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, icon: 'circle' },
    title: buildEmptyTitle(roleDistribution.every(item => !item.count)),
    series: [{
      type: 'pie',
      radius: ['50%', '72%'],
      center: ['50%', '44%'],
      label: { formatter: '{b} {d}%' },
      data: roleDistribution.map(item => ({ name: item.name, value: item.count })),
    }],
  })
}

function resizeCharts() {
  chartInstances.forEach(chart => chart.resize())
}

onMounted(async () => {
  await nextTick()
  window.addEventListener('resize', resizeCharts)
  await loadMonthlyReport()
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  chartInstances.forEach(chart => chart.dispose())
})

async function loadMonthlyReport() {
  loading.value = true
  aiAnalysis.value = ''
  aiError.value = ''
  try {
    const response = await reportApi.monthly(selectedMonth.value)
    reportData.value = normalizeReport(response.data || createEmptyReport(selectedMonth.value))
    await nextTick()
    initCharts()
    ElMessage.success(`${selectedMonth.value} 月度报告已加载真实统计数据`)
  } catch (error) {
    reportData.value = createDevFallbackMock(selectedMonth.value)
    await nextTick()
    initCharts()
    ElMessage.warning('月度报告接口暂不可用，当前显示演示数据')
  } finally {
    loading.value = false
  }
}

function getPreviousMonth() {
  const now = new Date()
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
  firstDay.setMonth(firstDay.getMonth() - 1)
  return `${firstDay.getFullYear()}-${String(firstDay.getMonth() + 1).padStart(2, '0')}`
}

function createEmptyReport(month) {
  return {
    month,
    range: { start: '', end: '' },
    data_source: 'database',
    is_mock: false,
    core_stats: {
      borrow_count: 0,
      active_user_count: 0,
      reservation_count: 0,
      overdue_count: 0,
      book_request_count: 0,
    },
    book_analysis: {
      popular_books: [],
      categories: [],
      stock_risk_books: [],
    },
    seat_analysis: {
      popular_seats: [],
      popular_rooms: [],
      peak_hours: [],
      feature_preference: {
        with_power_count: 0,
        without_power_count: 0,
        with_power_ratio: 0,
        without_power_ratio: 0,
      },
    },
    user_behavior: {
      role_distribution: [
        { role: 'student', name: '学生', count: 0, ratio: 0 },
        { role: 'teacher', name: '教师', count: 0, ratio: 0 },
      ],
      renew_count: 0,
      book_request_count: 0,
      overdue_count: 0,
    },
  }
}

function normalizeReport(data) {
  const empty = createEmptyReport(data.month || selectedMonth.value)
  return {
    ...empty,
    ...data,
    core_stats: { ...empty.core_stats, ...(data.core_stats || {}) },
    book_analysis: { ...empty.book_analysis, ...(data.book_analysis || {}) },
    seat_analysis: { ...empty.seat_analysis, ...(data.seat_analysis || {}) },
    user_behavior: { ...empty.user_behavior, ...(data.user_behavior || {}) },
  }
}

function createDevFallbackMock(month) {
  const fallback = createEmptyReport(month)
  return {
    ...fallback,
    data_source: 'devFallbackMock',
    is_mock: true,
    range: { start: `${month}-01`, end: `${month}-末` },
    core_stats: {
      borrow_count: 1286,
      active_user_count: 842,
      reservation_count: 2418,
      overdue_count: 37,
      book_request_count: 43,
    },
    book_analysis: {
      popular_books: [
        { title: '《算法导论》', author: 'Thomas H. Cormen', category: '计算机', borrow_count: 96, stock: 2 },
        { title: '《人工智能》', author: 'Stuart Russell', category: '人工智能', borrow_count: 88, stock: 3 },
        { title: '《计算机网络》', author: '谢希仁', category: '计算机', borrow_count: 83, stock: 4 },
      ],
      categories: [
        { name: '计算机', value: 38 },
        { name: '人工智能', value: 24 },
        { name: '数据库', value: 14 },
      ],
      stock_risk_books: [
        { title: '《算法导论》', stock: 2, borrow_count: 96, reason: '演示数据：借阅 96 次，当前库存 2 本' },
        { title: '《数据库系统概念》', stock: 2, borrow_count: 76, reason: '演示数据：借阅 76 次，当前库存 2 本' },
      ],
    },
    seat_analysis: {
      popular_seats: [
        { seat_number: 'B201-01', reservation_count: 128 },
        { seat_number: 'B201-02', reservation_count: 117 },
      ],
      popular_rooms: [
        { room_name: 'B201 自习室', reservation_count: 486 },
      ],
      peak_hours: [
        { label: '19:00 - 21:00', reservation_count: 586 },
        { label: '16:00 - 18:00', reservation_count: 402 },
        { label: '14:00 - 16:00', reservation_count: 318 },
      ],
      feature_preference: {
        with_power_count: 1644,
        without_power_count: 774,
        with_power_ratio: 68,
        without_power_ratio: 32,
      },
    },
    user_behavior: {
      role_distribution: [
        { role: 'student', name: '学生', count: 706, ratio: 82 },
        { role: 'teacher', name: '教师', count: 136, ratio: 18 },
      ],
      renew_count: 214,
      book_request_count: 43,
      overdue_count: 37,
    },
  }
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString('zh-CN')
}

function hasValue(value) {
  return Number(value || 0) > 0
}

function buildEmptyTitle(isEmpty) {
  return isEmpty
    ? {
        text: '暂无数据',
        left: 'center',
        top: '42%',
        textStyle: { color: '#9aa5b5', fontSize: 14, fontWeight: 500 },
      }
    : undefined
}
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

.ai-heading-actions {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  gap: 10px;
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

.ai-alert {
  border-radius: 12px;
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

.ai-report-text {
  white-space: pre-line;
}
</style>
