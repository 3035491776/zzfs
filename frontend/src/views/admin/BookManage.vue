<template>
  <div class="book-manage-page">
    <el-card shadow="never" class="workspace-card">
      <el-tabs v-model="activeTab" class="student-tabs management-tabs">
        <!-- ============================================================ -->
        <!-- Tab 1: 图书列表 -->
        <!-- ============================================================ -->
        <el-tab-pane label="图书列表" name="books">
          <div class="search-bar">
            <el-input
              v-model="search"
              class="search-input"
              placeholder="搜索书名 / 作者 / ISBN"
              clearable
              @change="fetchBooks"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-select
              v-model="categoryId"
              class="category-select"
              placeholder="全部分类"
              clearable
              @change="fetchBooks"
            >
              <el-option label="全部分类" :value="0" />
              <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <span class="search-bar__spacer"></span>
            <el-button type="primary" class="create-button" @click="showDialog(null)">
              <el-icon><Plus /></el-icon>
              <span>新增图书</span>
            </el-button>
          </div>

          <el-table :data="books" stripe v-loading="loading" class="management-table">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="title" label="书名" min-width="180" />
            <el-table-column prop="author" label="作者" width="150" />
            <el-table-column prop="isbn" label="ISBN" width="150" />
            <el-table-column prop="category_name" label="分类" width="120">
              <template #default="{ row }">
                <el-tag type="info" effect="plain">{{ row.category_name }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="stock" label="库存" width="90" />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="showDialog(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)">下架</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-row">
            <span>共 {{ bookTotal }} 条馆藏记录</span>
            <el-pagination
              v-model:current-page="bookPage"
              :total="bookTotal"
              :page-size="10"
              layout="prev,pager,next"
              background
              @current-change="fetchBooks"
            />
          </div>
        </el-tab-pane>

        <!-- ============================================================ -->
        <!-- Tab 2: 图书荐购审核 -->
        <!-- ============================================================ -->
        <el-tab-pane label="荐购审核" name="requests">
          <div class="review-filter">
            <div>
              <strong>荐购申请</strong>
              <span>审核读者提交的图书采购建议</span>
            </div>
            <el-radio-group v-model="reqStatus" @change="fetchRequests">
              <el-radio-button value="pending">待审核</el-radio-button>
              <el-radio-button value="approved">已采纳</el-radio-button>
              <el-radio-button value="rejected">已驳回</el-radio-button>
            </el-radio-group>
          </div>

          <el-table :data="requests" stripe v-loading="reqLoading" class="management-table">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="applicant_name" label="申请人" width="100" />
            <el-table-column prop="title" label="书名" min-width="160" />
            <el-table-column prop="author" label="作者" width="120" />
            <el-table-column prop="publisher" label="出版社" width="140" />
            <el-table-column prop="isbn" label="ISBN" width="140" />
            <el-table-column prop="reason" label="荐购理由" min-width="180" show-overflow-tooltip />
            <el-table-column prop="status_text" label="状态" width="100">
              <template #default="{row}">
                <el-tag :type="row.status==='approved'?'success':row.status==='rejected'?'danger':'warning'" size="small">{{row.status_text}}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <template v-if="row.status==='pending'">
                  <el-button size="small" type="success" @click="handleApprove(row)">采纳</el-button>
                  <el-button size="small" type="danger" @click="handleReject(row)">驳回</el-button>
                </template>
                <span v-else class="reviewed-text">{{ row.review_comment || '已处理' }}</span>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-row">
            <span>共 {{ reqTotal }} 条荐购记录</span>
            <el-pagination
              v-model:current-page="reqPage"
              :total="reqTotal"
              :page-size="10"
              layout="prev,pager,next"
              background
              @current-change="fetchRequests"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 新增/编辑图书弹窗 -->
    <el-dialog
      :title="editing ? '编辑图书' : '新增图书'"
      v-model="dialogVisible"
      width="560px"
      class="book-dialog"
      @close="editing=null"
    >
      <el-form :model="form" label-width="92px" class="book-form">
        <el-form-item label="书名"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="作者"><el-input v-model="form.author" /></el-form-item>
        <el-form-item label="ISBN"><el-input v-model="form.isbn" /></el-form-item>
        <el-form-item label="出版社"><el-input v-model="form.publisher" /></el-form-item>
        <el-form-item label="出版年份"><el-input-number v-model="form.publish_year" :min="1900" :max="2030" /></el-form-item>
        <el-form-item label="库存"><el-input-number v-model="form.stock" :min="0" /></el-form-item>
        <el-form-item label="分类"><el-select v-model="form.category_id"><el-option label="未分类" :value="0" /><el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item>
        <el-form-item label="馆藏位置"><el-input v-model="form.location" /></el-form-item>
        <el-form-item label="简介"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-actions">
          <el-button @click="dialogVisible=false">取消</el-button>
          <el-button type="primary" @click="handleSave">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { bookApi, categoryApi, bookRequestApi } from '../../api/auth'

const activeTab = ref('books')

// ---- 图书列表 ----
const books = ref([])
const categories = ref([])
const search = ref('')
const categoryId = ref(0)
const bookPage = ref(1)
const bookTotal = ref(0)
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref(null)
const form = ref({})

onMounted(() => { fetchBooks(); categoryApi.list().then(r => categories.value = r.data.list) })

async function fetchBooks() {
  loading.value = true
  const r = await bookApi.list({ page: bookPage.value, search: search.value, category_id: categoryId.value })
  books.value = r.data.list; bookTotal.value = r.data.total; loading.value = false
}
function showDialog(row) {
  editing.value = row
  form.value = row ? { ...row } : { title: '', author: '', isbn: '', publisher: '', publish_year: null, stock: 0, category_id: 0, location: '', description: '' }
  dialogVisible.value = true
}
async function handleSave() {
  try {
    editing.value ? await bookApi.update(editing.value.id, form.value) : await bookApi.add(form.value)
    ElMessage.success(editing.value ? '已更新' : '已添加')
    dialogVisible.value = false; fetchBooks()
  } catch (e) { /* handled */ }
}
async function handleDelete(row) {
  await ElMessageBox.confirm(`确定下架《${row.title}》？`, '确认')
  try { await bookApi.delete(row.id); ElMessage.success('已下架'); fetchBooks() } catch (e) { /* handled */ }
}

// ---- 图书荐购审核 ----
const requests = ref([])
const reqPage = ref(1)
const reqTotal = ref(0)
const reqStatus = ref('pending')
const reqLoading = ref(false)

async function fetchRequests() {
  reqLoading.value = true
  try {
    const r = await bookRequestApi.all({ page: reqPage.value, status: reqStatus.value })
    requests.value = r.data.list; reqTotal.value = r.data.total
  } catch (e) { /* */ }
  reqLoading.value = false
}

async function handleApprove(row) {
  try {
    const { value } = await ElMessageBox.prompt('审核意见（选填）', '采纳荐购', { inputValue: '已采纳，将尽快采购入库', confirmButtonText: '确认采纳' })
    await bookRequestApi.approve(row.id, { comment: value || '' })
    ElMessage.success(`已采纳《${row.title}》`); fetchRequests()
  } catch (e) { /* cancel */ }
}

async function handleReject(row) {
  try {
    const { value } = await ElMessageBox.prompt('驳回理由（选填）', '驳回荐购', { inputValue: '暂不收录', confirmButtonText: '确认驳回' })
    await bookRequestApi.reject(row.id, { comment: value || '' })
    ElMessage.success(`已驳回《${row.title}》`); fetchRequests()
  } catch (e) { /* cancel */ }
}
</script>

<style scoped>
.book-manage-page {
  width: 100%;
  max-width: 1480px;
  margin: 0 auto;
}

.workspace-card :deep(.el-card__body) {
  padding: 0 24px 24px;
}

.management-tabs :deep(.el-tabs__header) {
  margin-bottom: 22px;
}

.search-bar,
.review-filter,
.pagination-row {
  display: flex;
  align-items: center;
}

.search-bar {
  gap: 12px;
  padding: 16px;
  margin-bottom: 18px;
  border: 1px solid var(--library-border);
  border-radius: 14px;
  background: #f9fbfd;
}

.search-input {
  width: min(420px, 42%);
}

.category-select {
  width: 190px;
}

.search-bar__spacer {
  flex: 1;
}

.create-button {
  min-width: 118px;
  height: 40px;
}

.create-button .el-icon {
  margin-right: 6px;
}

.management-table {
  width: 100%;
  border: 1px solid var(--library-border);
  border-radius: 14px;
  overflow: hidden;
}

.management-table :deep(.cell) {
  padding-inline: 16px;
}

.pagination-row {
  min-height: 58px;
  justify-content: space-between;
  gap: 20px;
  padding-top: 18px;
}

.pagination-row > span {
  color: var(--library-muted);
  font-size: 13px;
}

.review-filter {
  min-height: 72px;
  justify-content: space-between;
  gap: 24px;
  padding: 14px 16px;
  margin-bottom: 18px;
  border: 1px solid var(--library-border);
  border-radius: 14px;
  background: #f9fbfd;
}

.review-filter > div {
  display: flex;
  flex-direction: column;
}

.review-filter strong {
  color: var(--library-text);
  font-size: 15px;
  font-weight: 700;
}

.review-filter span {
  margin-top: 4px;
  color: var(--library-muted);
  font-size: 12px;
}

.review-filter :deep(.el-radio-group) {
  width: auto;
  flex-shrink: 0;
  flex-direction: row;
  flex-wrap: nowrap;
}

.review-filter :deep(.el-radio-button__inner) {
  min-width: 76px;
  border-color: var(--library-border);
  color: #667085;
  font-weight: 600;
}

.review-filter :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  border-color: var(--library-primary);
  color: #fff;
  background: var(--library-primary);
  box-shadow: -1px 0 0 0 var(--library-primary);
}

.reviewed-text {
  color: var(--library-muted);
  font-size: 13px;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:global(.book-dialog) {
  border-radius: var(--library-radius);
  overflow: hidden;
}

:global(.book-dialog .el-dialog__header) {
  padding: 20px 24px 16px;
  margin-right: 0;
  border-bottom: 1px solid var(--library-border);
}

:global(.book-dialog .el-dialog__title) {
  color: var(--library-text);
  font-size: 18px;
  font-weight: 700;
}

:global(.book-dialog .el-dialog__body) {
  max-height: 66vh;
  padding: 22px 24px 8px;
  overflow-y: auto;
}

:global(.book-dialog .el-dialog__footer) {
  padding: 16px 24px 20px;
  border-top: 1px solid var(--library-border);
}

:global(.book-dialog .el-form-item) {
  margin-bottom: 18px;
}

:global(.book-dialog .el-form-item__label) {
  color: #5f6f85;
  font-weight: 500;
}

:global(.book-dialog .el-input__wrapper),
:global(.book-dialog .el-select__wrapper),
:global(.book-dialog .el-textarea__inner) {
  border-radius: 12px;
}

:global(.book-dialog .el-input-number),
:global(.book-dialog .el-select) {
  width: 100%;
}

:global(.book-dialog .el-button) {
  border-radius: var(--library-control-radius);
  font-weight: 600;
}

:global(.book-dialog .el-button--primary) {
  border-color: var(--library-primary);
  background: var(--library-primary);
}
</style>
