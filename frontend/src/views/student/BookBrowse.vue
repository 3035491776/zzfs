<template>
  <div class="book-browse">
    <section class="stats-grid" aria-label="图书馆数据概览">
      <article class="stat-card">
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

      <article class="stat-card">
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

      <article class="stat-card">
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

      <article class="stat-card">
        <div class="stat-icon">
          <el-icon><Message /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-label">未读消息</span>
          <div class="stat-value">
            <strong>1</strong>
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
          <el-option
            v-for="c in categories"
            :key="c.id"
            :label="c.name"
            :value="c.id"
          />
        </el-select>
      </div>

      <div class="table-wrap">
        <el-table
          :data="books"
          v-loading="loading"
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
              <el-tag class="category-tag" effect="plain">
                {{ row.category_name }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="stock" label="库存" min-width="100">
            <template #default="{ row }">
              <span :class="['stock-value', { empty: row.stock <= 0 }]">
                {{ row.stock }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="location" label="位置" min-width="150">
            <template #default="{ row }">
              <span class="location-cell">
                <el-icon><Location /></el-icon>
                {{ row.location }}
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
                {{ row.stock > 0 ? '借阅' : '暂无库存' }}
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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { bookApi, categoryApi, borrowApi } from '../../api/auth'

const books = ref([])
const categories = ref([])
const search = ref('')
const categoryId = ref(0)
const page = ref(1)
const total = ref(0)
const loading = ref(false)

onMounted(() => { fetchData(); categoryApi.list().then(r => categories.value = r.data.list) })

async function fetchData() {
  loading.value = true
  try {
    const r = await bookApi.list({ page: page.value, search: search.value, category_id: categoryId.value })
    books.value = r.data.list; total.value = r.data.total
  } catch (e) { /* */ }
  loading.value = false
}

async function borrow(row) {
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

.table-wrap {
  width: 100%;
  overflow-x: auto;
}

.books-table {
  width: 100%;
  min-width: 820px;
}

.book-title {
  color: #111827;
  font-weight: 500;
}

.category-tag {
  height: 28px;
  padding: 0 12px;
  border: 0;
  border-radius: 999px;
  color: #52627a;
  background: #f1f4f8;
  line-height: 28px;
}

.stock-value {
  color: #111827;
  font-weight: 600;
}

.stock-value.empty {
  color: #9aa6b6;
}

.location-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #62738a;
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
</style>
