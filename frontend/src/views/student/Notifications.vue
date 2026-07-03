<template>
  <div class="notifications-page">
    <el-tabs v-model="activeTab" class="notification-tabs student-tabs">
      <!-- ============================================================ -->
      <!-- Tab 1: 消息通知 -->
      <!-- ============================================================ -->
      <el-tab-pane label="消息通知" name="notifications">
        <div class="notification-toolbar">
          <span>共 {{ notifTotal }} 条消息</span>
          <el-button @click="markAll">✓ 全部已读</el-button>
        </div>

        <div v-if="notifications.length" class="notification-list">
          <article v-for="row in notifications" :key="row.id" :class="['notification-item', { unread: !row.is_read }]">
            <span class="unread-dot" aria-hidden="true"></span>
            <div class="notification-content">
              <div class="notification-title">
                <strong>{{ row.title }}</strong>
                <el-tag size="small" effect="light" round>{{ row.type_text }}</el-tag>
                <el-tag v-if="!row.is_read" type="danger" size="small" effect="light" round>未读</el-tag>
              </div>
              <p>{{ row.content }}</p>
              <time>{{ row.create_time }}</time>
            </div>
            <div class="notification-action">
              <el-button v-if="!row.is_read" size="small" type="primary" @click="readOne(row)">已读</el-button>
              <span v-else>已读</span>
            </div>
          </article>
        </div>
        <el-empty v-else description="暂无消息" :image-size="80" />

        <div class="pagination-row">
          <el-pagination v-model:current-page="notifPage" :total="notifTotal" :page-size="10"
            layout="prev,pager,next" @current-change="fetchNotifications" />
        </div>
      </el-tab-pane>

      <!-- ============================================================ -->
      <!-- Tab 2: 图书荐购 -->
      <!-- ============================================================ -->
      <el-tab-pane label="图书荐购" name="requests">
        <!-- 新建荐购 -->
        <el-card shadow="never" class="request-card">
          <template #header>
            <div class="card-title">
              <strong>希望图书馆收录什么书？</strong>
              <span>填写图书信息与推荐理由</span>
            </div>
          </template>
          <el-form :model="reqForm" label-width="80px" size="default">
            <el-row :gutter="16">
              <el-col :xs="24" :sm="12">
                <el-form-item label="书名" required><el-input v-model="reqForm.title" placeholder="必填" /></el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="作者"><el-input v-model="reqForm.author" placeholder="选填" /></el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :xs="24" :sm="12">
                <el-form-item label="出版社"><el-input v-model="reqForm.publisher" placeholder="选填" /></el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="ISBN"><el-input v-model="reqForm.isbn" placeholder="选填" /></el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="荐购理由" required>
              <el-input v-model="reqForm.reason" type="textarea" :rows="3" placeholder="请说明为什么推荐这本书（如：课程需要、科研参考、经典著作等）" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitRequest" :loading="submitting">提交荐购</el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 我的荐购记录 -->
        <el-card shadow="never" class="request-card request-records">
          <template #header>
            <div class="card-title">
              <strong>我的荐购记录</strong>
              <span>查看荐购申请的审核进度</span>
            </div>
          </template>
          <el-table :data="myRequests" stripe v-loading="reqLoading">
            <el-table-column prop="title" label="书名" min-width="150" />
            <el-table-column prop="author" label="作者" width="120" />
            <el-table-column prop="publisher" label="出版社" width="140" />
            <el-table-column prop="reason" label="荐购理由" min-width="160" show-overflow-tooltip />
            <el-table-column prop="status_text" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status==='approved'?'success':row.status==='rejected'?'danger':'warning'" size="small">
                  {{ row.status_text }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="review_comment" label="审核意见" min-width="120" show-overflow-tooltip />
            <el-table-column prop="create_time" label="提交时间" width="160" />
          </el-table>
          <div class="pagination-row">
            <el-pagination v-model:current-page="reqPage" :total="reqTotal" :page-size="10"
              layout="prev,pager,next" @current-change="fetchMyRequests" />
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { notificationApi, bookRequestApi } from '../../api/auth'

const activeTab = ref('notifications')

// ---- 消息通知 ----
const notifications = ref([])
const notifPage = ref(1)
const notifTotal = ref(0)

onMounted(() => fetchNotifications())

async function fetchNotifications() {
  const r = await notificationApi.list({ page: notifPage.value })
  notifications.value = r.data.list; notifTotal.value = r.data.total
}

async function readOne(row) { try { await notificationApi.markRead(row.id); fetchNotifications() } catch (e) { /* */ } }
async function markAll() { try { await notificationApi.markAllRead(); fetchNotifications(); ElMessage.success('全部已读') } catch (e) { /* */ } }

// ---- 图书荐购 ----
const reqForm = reactive({ title: '', author: '', publisher: '', isbn: '', reason: '' })
const submitting = ref(false)
const myRequests = ref([])
const reqPage = ref(1)
const reqTotal = ref(0)
const reqLoading = ref(false)

async function submitRequest() {
  if (!reqForm.title.trim()) { ElMessage.warning('请输入书名'); return }
  if (!reqForm.reason.trim()) { ElMessage.warning('请输入荐购理由'); return }
  submitting.value = true
  try {
    await bookRequestApi.submit({ ...reqForm })
    ElMessage.success('荐购请求已提交，感谢您的推荐！管理员审核后会通知您')
    resetForm()
    fetchMyRequests()
  } catch (e) { /* handled */ }
  submitting.value = false
}

function resetForm() {
  reqForm.title = ''; reqForm.author = ''; reqForm.publisher = ''
  reqForm.isbn = ''; reqForm.reason = ''
}

async function fetchMyRequests() {
  reqLoading.value = true
  try {
    const r = await bookRequestApi.my({ page: reqPage.value })
    myRequests.value = r.data.list; reqTotal.value = r.data.total
  } catch (e) { /* */ }
  reqLoading.value = false
}
</script>

<style scoped>
.notifications-page {
  min-height: 100%;
}

.notification-tabs {
  overflow: hidden;
  background: #fff;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  box-shadow: var(--library-card-shadow);
}

.notifications-page :deep(.notification-tabs > .el-tabs__header) {
  margin: 0;
  padding: 10px 24px 0;
}

.notifications-page :deep(.notification-tabs > .el-tabs__header .el-tabs__nav-wrap::after) {
  height: 1px;
  background: var(--border-color);
}

.notification-toolbar {
  display: flex;
  min-height: 64px;
  padding: 10px 24px;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
}

.notification-toolbar > span {
  color: var(--text-muted);
  font-size: 13px;
}

.notification-toolbar :deep(.el-button) {
  height: 38px;
  color: #64748b;
  border-color: var(--border-color);
  border-radius: 10px;
  font-weight: 600;
}

.notification-toolbar :deep(.el-button:hover) {
  color: var(--brand-blue);
  background: #f7faff;
  border-color: #b9cdf8;
}

.notification-list {
  display: grid;
}

.notification-item {
  position: relative;
  display: flex;
  min-height: 124px;
  padding: 22px 24px;
  box-sizing: border-box;
  align-items: flex-start;
  gap: 16px;
  background: #fff;
  border-bottom: 1px solid var(--border-color);
  transition: background 0.18s ease;
}

.notification-item.unread {
  background: #f8faff;
}

.notification-item:hover {
  background: #f6f9fe;
}

.unread-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 8px;
  margin-top: 8px;
  background: transparent;
  border-radius: 50%;
}

.notification-item.unread .unread-dot {
  background: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.08);
}

.notification-content {
  min-width: 0;
  flex: 1;
}

.notification-title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.notification-title strong {
  color: var(--text-main);
  font-size: 15px;
  font-weight: 700;
}

.notification-content p {
  margin: 10px 0 8px;
  color: #69778d;
  font-size: 14px;
  line-height: 1.6;
}

.notification-content time {
  color: #9aa6b7;
  font-size: 12px;
}

.notification-action {
  display: flex;
  min-width: 72px;
  min-height: 34px;
  align-items: center;
  justify-content: flex-end;
}

.notification-action > span {
  color: #8794a8;
  font-size: 12px;
}

.notification-action :deep(.el-button) {
  border-radius: 9px;
}

.pagination-row {
  display: flex;
  padding: 20px 24px;
  justify-content: flex-end;
}

.request-card {
  margin: 24px;
  border-color: var(--border-color);
  border-radius: var(--library-radius);
}

.request-records {
  margin-top: 0;
}

.notifications-page :deep(.request-card .el-card__header) {
  padding: 18px 22px;
  border-bottom-color: var(--border-color);
}

.card-title {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.card-title strong {
  color: var(--text-main);
  font-size: 16px;
}

.card-title span {
  color: var(--text-muted);
  font-size: 12px;
}

.notifications-page :deep(.request-card .el-input__wrapper),
.notifications-page :deep(.request-card .el-textarea__inner) {
  border-radius: 10px;
}

@media (max-width: 640px) {
  .notifications-page :deep(.notification-tabs > .el-tabs__header) {
    padding-inline: 16px;
  }

  .notification-toolbar,
  .notification-item {
    padding-inline: 16px;
  }

  .notification-item {
    gap: 10px;
  }

  .notification-action {
    min-width: 54px;
  }

  .request-card {
    margin: 16px;
  }

  .pagination-row {
    padding-inline: 16px;
  }
}
</style>
