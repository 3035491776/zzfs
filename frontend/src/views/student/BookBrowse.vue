<template>
  <div class="book-browse">
    <section class="stats-grid" aria-label="图书馆数据概览">
      <article class="stat-card stat-card-books">
        <div class="stat-icon">
          <el-icon><Collection /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-label">馆藏图书</span>
          <div class="stat-value">
            <strong>{{ Number(total).toLocaleString() }}</strong>
            <span>册</span>
          </div>
          <small>馆藏资源持续更新</small>
        </div>
      </article>

      <article class="stat-card stat-card-borrows">
        <div class="stat-icon">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-label">今日借阅</span>
          <div class="stat-value">
            <strong>1,286</strong>
            <span>次</span>
          </div>
          <small>较昨日 <b>+12%</b></small>
        </div>
      </article>

      <article class="stat-card stat-card-seats">
        <div class="stat-icon">
          <el-icon><OfficeBuilding /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-label">可用座位</span>
          <div class="stat-value">
            <strong>342</strong>
            <span>个</span>
          </div>
          <small>共 1,200 座</small>
        </div>
      </article>

      <article class="stat-card stat-card-notifications">
        <div class="stat-icon">
          <el-icon><Message /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-label">未读消息</span>
          <div class="stat-value">
            <strong>{{ unreadCount }}</strong>
            <span>条</span>
          </div>
          <small>点击侧栏查看详情</small>
        </div>
      </article>
    </section>

    <section class="book-panel">
      <div class="filter-bar">
        <el-input
          v-model="search"
          class="search-input"
          placeholder="搜索书名 / 作者"
          clearable
          @change="fetchData"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="categoryId"
          class="category-select"
          placeholder="全部分类"
          clearable
          @change="fetchData"
        >
          <el-option label="全部分类" :value="0" />
          <el-option
            v-for="c in categories"
            :key="c.id"
            :label="c.name"
            :value="c.id"
          />
        </el-select>
      </div>

      <div class="table-heading">
        <div>
          <h2>馆藏列表</h2>
          <p>根据书名、作者或分类筛选馆藏资源</p>
        </div>
        <span>共 {{ total }} 本</span>
      </div>

      <div class="table-wrap">
        <el-table
          :data="books"
          v-loading="loading"
          stripe
          class="books-table"
          empty-text="暂无馆藏图书"
        >
          <el-table-column prop="title" label="书名" min-width="240">
            <template #default="{ row }">
              <span class="book-title">{{ row.title }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="author" label="作者" min-width="130" />
          <el-table-column prop="category_name" label="分类" min-width="130">
            <template #default="{ row }">
              <el-tag :class="['category-tag', categoryTagClass(row.category_name)]" effect="plain">
                {{ row.category_name }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="stock" label="库存" min-width="100">
            <template #default="{ row }">
              <div class="stock-cell">
                <span :class="['stock-value', { empty: row.stock <= 0, low: isLowStock(row.stock) }]">
                  {{ row.stock }}
                </span>
                <el-tooltip v-if="isLowStock(row.stock)" content="库存紧张" placement="top">
                  <el-tag class="low-stock-tag" size="small" effect="plain">库存紧张</el-tag>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="location" label="位置" min-width="150">
            <template #default="{ row }">
              <span class="location-cell">
                <el-icon><Location /></el-icon>
                <span class="location-copy">
                  <span v-for="(line, index) in displayLocation(row.location).split(' · ')" :key="index">
                    {{ line }}
                  </span>
                </span>
              </span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="right">
            <template #default="{ row }">
              <el-button
                class="borrow-button"
                size="small"
                type="primary"
                :disabled="row.stock <= 0"
                @click="borrow(row)"
              >
                {{ row.stock > 0 ? '借阅' : '已借完' }}
              </el-button>
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
  </div>
</template>

<script setup>
import { inject, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { bookApi, categoryApi, borrowApi } from '../../api/auth'

const books = ref([])
const categories = ref([])
const search = ref('')
const categoryId = ref(0)
const page = ref(1)
const total = ref(0)
const loading = ref(false)
const unreadCount = inject('unreadCount', ref(0))

const examMonthLocations = {
  '考试月演示专区-计算机': '三楼 B 区 · 计算机书架',
  '考试月演示专区-数学': '三楼考研专区 · 数学资料架',
  '考试月演示专区-英语': '二楼 C 区 · 英语资料架',
  '考试月演示专区-自然科学': '二楼 A 区 · 自然科学书架',
  '考试月演示专区-文学': '二楼 B 区 · 文学书架',
  '考试月演示专区-历史': '二楼 C 区 · 历史书架',
  '考试月演示专区-哲学': '二楼 D 区 · 哲学书架',
  '考试月演示专区-经济': '三楼 A 区 · 经济管理书架',
}

const categoryTagClasses = {
  '自然科学': 'category-natural',
  '计算机': 'category-computing',
  '数学': 'category-mathematics',
  '英语': 'category-english',
  '专业课': 'category-professional',
  '经济': 'category-economics',
  '哲学': 'category-philosophy',
  '历史': 'category-history',
  '文学': 'category-literature',
}

onMounted(() => { fetchData(); categoryApi.list().then(r => categories.value = r.data.list) })

async function fetchData() {
  loading.value = true
  try {
    const r = await bookApi.list({ page: page.value, search: search.value, category_id: categoryId.value || 0 })
    books.value = r.data.list; total.value = r.data.total
  } catch (e) { /* */ }
  loading.value = false
}

function isLowStock(stock) {
  return stock > 0 && stock < 3
}

function categoryTagClass(categoryName) {
  return categoryTagClasses[categoryName] || 'category-default'
}

function displayLocation(location) {
  if (examMonthLocations[location]) return examMonthLocations[location]

  if (location?.startsWith('考试月演示专区-')) {
    const subject = location.replace('考试月演示专区-', '')
    return `三楼 B 区 · ${subject}书架`
  }

  return location
}

async function borrow(row) {
  if (row.stock <= 0) return

  try {
    await borrowApi.apply(row.id)
    ElMessage.success(`《${row.title}》借阅申请已提交，等待审核`)
  } catch (e) { /* handled */ }
}
</script>

<style scoped>
.book-browse {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 20px;
}

.stat-card {
  display: flex;
  min-width: 0;
  min-height: 176px;
  gap: 18px;
  padding: 26px 24px;
  border: 1px solid var(--library-border);
  border-radius: 16px;
  background: #fff;
  box-shadow: var(--library-card-shadow);
  transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
}

.stat-card:hover {
  border-color: #cdd9f8;
  box-shadow: 0 12px 28px rgba(30, 64, 175, 0.08);
  transform: translateY(-2px);
}

.stat-icon {
  display: grid;
  width: 54px;
  height: 54px;
  flex: 0 0 54px;
  place-items: center;
  border-radius: 15px;
  color: var(--library-primary);
  background: #edf2ff;
}

.stat-icon .el-icon {
  font-size: 26px;
}

.stat-card-borrows .stat-icon {
  color: #21835b;
  background: #e8f7ef;
}

.stat-card-seats .stat-icon {
  color: #137f98;
  background: #e7f7fa;
}

.stat-card-notifications .stat-icon {
  color: #c56b18;
  background: #fff3e5;
}

.stat-content {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
}

.stat-label {
  margin: 1px 0 8px;
  color: #718096;
  font-size: 15px;
  line-height: 1.4;
}

.stat-value {
  display: flex;
  align-items: baseline;
  gap: 5px;
  color: #111827;
}

.stat-value strong {
  overflow: hidden;
  font-size: clamp(26px, 2.3vw, 34px);
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.035em;
  text-overflow: ellipsis;
}

.stat-value span {
  color: #718096;
  font-size: 14px;
}

.stat-content small {
  margin-top: auto;
  color: var(--library-primary);
  font-size: 13px;
  line-height: 1.35;
  white-space: nowrap;
}

.stat-content small b {
  font-weight: 600;
}

.book-panel {
  overflow: hidden;
  border: 1px solid var(--library-border);
  border-radius: 16px;
  background: #fff;
  box-shadow: var(--library-card-shadow);
}

.filter-bar {
  display: flex;
  gap: 16px;
  padding: 24px;
  border-bottom: 1px solid #e8edf4;
  background: #fff;
}

.search-input {
  min-width: 260px;
  flex: 1;
}

.category-select {
  width: 240px;
  flex: 0 0 240px;
}

.filter-bar :deep(.el-input__wrapper),
.filter-bar :deep(.el-select__wrapper) {
  min-height: 48px;
  padding: 0 16px;
  border-radius: 12px;
  box-shadow: 0 0 0 1px #dbe3ee inset;
  transition: box-shadow 160ms ease;
}

.filter-bar :deep(.el-input__wrapper:hover),
.filter-bar :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #aebddd inset;
}

.filter-bar :deep(.el-input__wrapper.is-focus),
.filter-bar :deep(.el-select__wrapper.is-focused) {
  box-shadow: 0 0 0 1px var(--library-primary) inset, 0 0 0 3px rgba(51, 102, 255, 0.08);
}

.filter-bar :deep(.el-input__prefix .el-icon) {
  color: #718096;
  font-size: 18px;
}

.filter-bar :deep(.el-input__inner),
.filter-bar :deep(.el-select__placeholder),
.filter-bar :deep(.el-select__selected-item) {
  color: #344054;
  font-size: 14px;
}

.table-heading {
  display: flex;
  min-height: 88px;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 24px;
  border-bottom: 1px solid #e8edf4;
  background: #fcfdff;
}

.table-heading h2 {
  margin: 0;
  color: #24334d;
  font-size: 17px;
  font-weight: 650;
  line-height: 1.4;
}

.table-heading p {
  margin: 5px 0 0;
  color: #7b899d;
  font-size: 13px;
  line-height: 1.5;
}

.table-heading > span {
  flex: 0 0 auto;
  color: var(--library-primary);
  font-size: 14px;
  font-weight: 600;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
}

.books-table {
  width: 100%;
  min-width: 820px;
}

.books-table :deep(.el-table__body tr > td.el-table__cell) {
  transition: background-color 160ms ease;
}

.books-table :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: rgba(51, 102, 255, 0.04) !important;
  box-shadow: inset 0 1px 0 rgba(51, 102, 255, 0.1), inset 0 -1px 0 rgba(51, 102, 255, 0.1);
}

.book-title {
  color: #111827;
  font-weight: 500;
}

.category-tag {
  height: 28px;
  padding: 0 12px;
  border: 1px solid transparent;
  border-radius: 999px;
  color: #52627a;
  background: #f1f4f8;
  line-height: 28px;
}

.category-tag.category-natural {
  border-color: #c9dcf6;
  color: #3e6598;
  background: #edf5ff;
}

.category-tag.category-computing {
  border-color: #cdd7fa;
  color: #4a5eaa;
  background: #f0f3ff;
}

.category-tag.category-mathematics {
  border-color: #bfe5e8;
  color: #287783;
  background: #ebf9fa;
}

.category-tag.category-english {
  border-color: #c6e5d2;
  color: #39745a;
  background: #edf8f1;
}

.category-tag.category-professional {
  border-color: #d8d0f5;
  color: #6257a2;
  background: #f4f1ff;
}

.category-tag.category-economics {
  border-color: #f0d1b7;
  color: #ad6841;
  background: #fff4ec;
}

.category-tag.category-philosophy {
  border-color: #e0ccec;
  color: #765a95;
  background: #f9f1fc;
}

.category-tag.category-history {
  border-color: #e8d9b9;
  color: #92744b;
  background: #faf6ed;
}

.category-tag.category-literature {
  border-color: #edd1de;
  color: #a2647c;
  background: #fff2f6;
}

.stock-value {
  color: #111827;
  font-weight: 600;
}

.stock-value.empty {
  color: #9aa6b6;
}

.stock-value.low {
  color: #d97821;
}

.stock-cell {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.low-stock-tag {
  border-color: #f3c990;
  border-radius: 6px;
  color: #b96012;
  background: #fff7eb;
}

.location-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #62738a;
}

.location-copy {
  display: inline-flex;
  flex-direction: column;
  line-height: 1.45;
}

.location-cell .el-icon {
  color: #7f91aa;
  font-size: 17px;
}

.borrow-button {
  min-width: 68px;
  height: 36px;
  padding: 0 16px;
  border-radius: 10px;
  font-weight: 500;
  box-shadow: 0 6px 14px rgba(51, 102, 255, 0.18);
}

.borrow-button.is-disabled {
  min-width: 86px;
  border-color: #dce4f0;
  color: #8d9aae;
  background: #eef2f7;
  box-shadow: none;
}

.table-footer {
  display: flex;
  min-height: 72px;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  border-top: 1px solid #e8edf4;
  background: #fff;
}

.total-count {
  color: #718096;
  font-size: 14px;
}

@media (max-width: 1280px) {
  .stats-grid {
    gap: 14px;
  }

  .stat-card {
    min-height: 164px;
    gap: 12px;
    padding: 22px 16px;
  }

  .stat-icon {
    width: 46px;
    height: 46px;
    flex-basis: 46px;
  }

  .stat-icon .el-icon {
    font-size: 22px;
  }
}

@media (max-width: 720px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .filter-bar,
  .table-heading,
  .table-footer {
    padding-right: 16px;
    padding-left: 16px;
  }

  .filter-bar {
    flex-direction: column;
  }

  .search-input,
  .category-select {
    width: 100%;
    min-width: 0;
    flex-basis: auto;
  }

  .table-heading {
    min-height: 0;
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }
}
</style>
