<template>
  <div>
    <h2>图书管理</h2>

    <el-tabs v-model="activeTab" style="margin-top:20px">
      <!-- ============================================================ -->
      <!-- Tab 1: 图书列表 -->
      <!-- ============================================================ -->
      <el-tab-pane label="图书列表" name="books">
        <el-row :gutter="10" style="margin-bottom:16px">
          <el-col :span="6"><el-input v-model="search" placeholder="搜索书名/作者/ISBN" clearable @change="fetchBooks" /></el-col>
          <el-col :span="4"><el-select v-model="categoryId" placeholder="分类筛选" clearable @change="fetchBooks"><el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-col>
          <el-col :span="4"><el-button type="primary" @click="showDialog(null)">新增图书</el-button></el-col>
        </el-row>
        <el-table :data="books" stripe border v-loading="loading">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="title" label="书名" />
          <el-table-column prop="author" label="作者" width="150" />
          <el-table-column prop="isbn" label="ISBN" width="140" />
          <el-table-column prop="category_name" label="分类" width="100" />
          <el-table-column prop="stock" label="库存" width="80" />
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button size="small" @click="showDialog(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">下架</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="bookPage" :total="bookTotal" :page-size="10" layout="prev,pager,next" @current-change="fetchBooks" style="margin-top:20px" />
      </el-tab-pane>

      <!-- ============================================================ -->
      <!-- Tab 2: 图书荐购审核 -->
      <!-- ============================================================ -->
      <el-tab-pane label="荐购审核" name="requests">
        <el-radio-group v-model="reqStatus" @change="fetchRequests" style="margin-bottom:16px">
          <el-radio-button value="pending">待审核</el-radio-button>
          <el-radio-button value="approved">已采纳</el-radio-button>
          <el-radio-button value="rejected">已驳回</el-radio-button>
        </el-radio-group>
        <el-table :data="requests" stripe border v-loading="reqLoading">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="applicant_name" label="申请人" width="100" />
          <el-table-column prop="title" label="书名" min-width="160" />
          <el-table-column prop="author" label="作者" width="120" />
          <el-table-column prop="publisher" label="出版社" width="140" />
          <el-table-column prop="isbn" label="ISBN" width="140" />
          <el-table-column prop="reason" label="荐购理由" min-width="180" show-overflow-tooltip />
          <el-table-column prop="status_text" label="状态" width="80">
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
              <span v-else style="color:#909399;font-size:13px">{{ row.review_comment || '已处理' }}</span>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="reqPage" :total="reqTotal" :page-size="10" layout="prev,pager,next" @current-change="fetchRequests" style="margin-top:20px" />
      </el-tab-pane>
    </el-tabs>

    <!-- 新增/编辑图书弹窗 -->
    <el-dialog :title="editing ? '编辑图书' : '新增图书'" v-model="dialogVisible" width="500px" @close="editing=null">
      <el-form :model="form" label-width="80px">
        <el-form-item label="书名"><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="作者"><el-input v-model="form.author" /></el-form-item>
        <el-form-item label="ISBN"><el-input v-model="form.isbn" /></el-form-item>
        <el-form-item label="出版社"><el-input v-model="form.publisher" /></el-form-item>
        <el-form-item label="出版年份"><el-input-number v-model="form.publish_year" :min="1900" :max="2030" /></el-form-item>
        <el-form-item label="库存"><el-input-number v-model="form.stock" :min="0" /></el-form-item>
        <el-form-item label="分类"><el-select v-model="form.category_id"><el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" /></el-select></el-form-item>
        <el-form-item label="馆藏位置"><el-input v-model="form.location" /></el-form-item>
        <el-form-item label="简介"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="handleSave">保存</el-button></template>
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
