<template>
  <div class="seat-manage-page">
    <el-card shadow="never" class="workspace-card">
      <el-tabs v-model="activeTab" class="student-tabs management-tabs">
        <!-- Tab 1: 座位列表 -->
        <el-tab-pane label="座位列表" name="seats">
          <div class="seat-toolbar">
            <div class="toolbar-copy">
              <strong>馆内座位</strong>
              <span>维护座位位置、设施与开放状态</span>
            </div>
            <span class="toolbar-spacer"></span>
            <el-button type="primary" class="create-button" @click="showDialog(null)">
              <el-icon><Plus /></el-icon>
              <span>新增座位</span>
            </el-button>
          </div>

          <el-table :data="seats" stripe class="management-table">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="seat_number" label="编号" width="110" />
            <el-table-column prop="room_name" label="自习室" min-width="180" />
            <el-table-column prop="floor" label="楼层" width="90" />
            <el-table-column prop="status_text" label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="row.status === 'available' ? 'success' : row.status === 'occupied' ? 'warning' : 'info'" effect="plain">
                  {{ row.status_text }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="has_power" label="电源" width="100">
              <template #default="{ row }">
                <el-tag type="info" effect="plain">{{ row.has_power ? '有电源' : '无电源' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="showDialog(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="delSeat(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="table-footer">
            <span>共 {{ seats.length }} 个座位</span>
          </div>
        </el-tab-pane>

        <!-- Tab 2: 报修处理 -->
        <el-tab-pane label="报修处理" name="repairs">
          <div class="repair-filter">
            <div class="toolbar-copy">
              <strong>报修状态</strong>
              <span>按处理进度筛选座位报修记录</span>
            </div>
            <el-radio-group v-model="repairStatus" class="status-switch" @change="fetchRepairs">
              <el-radio-button value="pending">待处理</el-radio-button>
              <el-radio-button value="fixing">维修中</el-radio-button>
              <el-radio-button value="resolved">已修复</el-radio-button>
              <el-radio-button value="rejected">已驳回</el-radio-button>
            </el-radio-group>
          </div>

          <el-table :data="repairs" stripe v-loading="repairLoading" class="management-table">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="reporter_name" label="报修人" width="110" />
            <el-table-column prop="seat_number" label="座位" width="110" />
            <el-table-column prop="room_name" label="自习室" width="160" />
            <el-table-column prop="description" label="故障描述" min-width="180" show-overflow-tooltip />
            <el-table-column prop="status_text" label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="row.status === 'resolved' ? 'success' : row.status === 'rejected' ? 'danger' : row.status === 'fixing' ? 'warning' : 'info'" effect="plain">
                  {{ row.status_text }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="报修时间" width="170" />
            <el-table-column label="操作" width="220" fixed="right">
              <template #default="{ row }">
                <template v-if="row.status === 'pending'">
                  <el-button size="small" type="primary" @click="markFixing(row)">开始维修</el-button>
                  <el-button size="small" type="danger" @click="rejectRepair(row)">驳回</el-button>
                </template>
                <template v-else-if="row.status === 'fixing'">
                  <el-button size="small" type="primary" @click="resolveRepair(row)">标记已修复</el-button>
                </template>
                <span v-else class="reviewed-text">{{ row.review_comment || '已处理' }}</span>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-row">
            <span>共 {{ repairTotal }} 条报修记录</span>
            <el-pagination
              v-model:current-page="repairPage"
              :total="repairTotal"
              :page-size="10"
              layout="prev,pager,next"
              background
              @current-change="fetchRepairs"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 新增/编辑座位弹窗 -->
    <el-dialog
      :title="editing ? '编辑座位' : '新增座位'"
      v-model="dialogVisible"
      width="480px"
      class="seat-dialog"
    >
      <el-form :model="form" label-width="80px" class="seat-form">
        <el-form-item label="编号"><el-input v-model="form.seat_number" /></el-form-item>
        <el-form-item label="自习室"><el-input v-model="form.room_name" /></el-form-item>
        <el-form-item label="楼层"><el-input-number v-model="form.floor" :min="1" :max="10" /></el-form-item>
        <el-form-item label="电源"><el-switch v-model="form.has_power" /></el-form-item>
        <el-form-item label="状态"><el-select v-model="form.status"><el-option label="可用" value="available" /><el-option label="占用" value="occupied" /><el-option label="维护" value="maintenance" /></el-select></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" /></el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-actions">
          <el-button @click="dialogVisible=false">取消</el-button>
          <el-button type="primary" @click="saveSeat">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { seatApi, seatRepairApi } from '../../api/auth'

const activeTab = ref('seats')

// ---- 座位管理 ----
const seats = ref([])
const dialogVisible = ref(false)
const editing = ref(null)
const form = ref({})
onMounted(() => fetchSeats())
async function fetchSeats() { const r = await seatApi.list(); seats.value = r.data.list }
function showDialog(row) {
  editing.value = row
  form.value = row ? { ...row } : { seat_number: '', room_name: '', floor: 1, has_power: true, status: 'available', description: '' }
  dialogVisible.value = true
}
async function saveSeat() {
  try {
    editing.value ? await seatApi.update(editing.value.id, form.value) : await seatApi.add(form.value)
    ElMessage.success(editing.value ? '已更新' : '已添加')
    dialogVisible.value = false; fetchSeats()
  } catch (e) { /* handled */ }
}
async function delSeat(row) {
  try { await ElMessageBox.confirm('确定删除？', '确认'); await seatApi.delete(row.id); ElMessage.success('已删除'); fetchSeats() } catch (e) { /* handled */ }
}

// ---- 报修处理 ----
const repairs = ref([])
const repairPage = ref(1)
const repairTotal = ref(0)
const repairStatus = ref('pending')
const repairLoading = ref(false)

async function fetchRepairs() {
  repairLoading.value = true
  try { const r = await seatRepairApi.all({ page: repairPage.value, status: repairStatus.value }); repairs.value = r.data.list; repairTotal.value = r.data.total } catch (e) { /* */ }
  repairLoading.value = false
}

async function markFixing(row) { try { await seatRepairApi.fix(row.id); ElMessage.success('已标记为维修中'); fetchRepairs(); fetchSeats() } catch (e) { /* */ } }
async function resolveRepair(row) {
  try {
    const { value } = await ElMessageBox.prompt('处理意见（选填）', '确认修复', { inputValue: '已修复', confirmButtonText: '确认' })
    await seatRepairApi.resolve(row.id, { comment: value || '' }); ElMessage.success('已标记修复'); fetchRepairs(); fetchSeats()
  } catch (e) { /* cancel */ }
}
async function rejectRepair(row) {
  try {
    const { value } = await ElMessageBox.prompt('驳回理由（选填）', '驳回报修', { inputValue: '经检查无需维修', confirmButtonText: '确认驳回' })
    await seatRepairApi.reject(row.id, { comment: value || '' }); ElMessage.success('已驳回'); fetchRepairs()
  } catch (e) { /* cancel */ }
}
</script>

<style scoped>
.seat-manage-page {
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

.seat-toolbar,
.repair-filter,
.table-footer,
.pagination-row,
.dialog-actions {
  display: flex;
  align-items: center;
}

.seat-toolbar,
.repair-filter {
  min-height: 72px;
  justify-content: space-between;
  gap: 24px;
  padding: 14px 16px;
  margin-bottom: 18px;
  border: 1px solid var(--library-border);
  border-radius: 14px;
  background: #f9fbfd;
}

.toolbar-copy {
  display: flex;
  min-width: 180px;
  flex-direction: column;
}

.toolbar-copy strong {
  color: var(--library-text);
  font-size: 15px;
  font-weight: 700;
}

.toolbar-copy span {
  margin-top: 4px;
  color: var(--library-muted);
  font-size: 12px;
}

.toolbar-spacer {
  flex: 1;
}

.create-button {
  min-width: 118px;
  height: 40px;
}

.create-button .el-icon {
  margin-right: 6px;
}

.status-switch {
  width: auto;
  flex-shrink: 0;
  flex-direction: row;
  flex-wrap: nowrap;
}

.status-switch :deep(.el-radio-button__inner) {
  min-width: 76px;
  border-color: var(--library-border);
  color: #667085;
  font-weight: 600;
}

.status-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  border-color: var(--library-primary);
  color: #fff;
  background: var(--library-primary);
  box-shadow: -1px 0 0 0 var(--library-primary);
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

.table-footer,
.pagination-row {
  min-height: 58px;
  padding-top: 18px;
  color: var(--library-muted);
  font-size: 13px;
}

.table-footer {
  justify-content: flex-end;
}

.pagination-row {
  justify-content: space-between;
  gap: 20px;
}

.reviewed-text {
  color: var(--library-muted);
  font-size: 13px;
}

.dialog-actions {
  justify-content: flex-end;
  gap: 10px;
}

:global(.seat-dialog) {
  border-radius: var(--library-radius);
  overflow: hidden;
}

:global(.seat-dialog .el-dialog__header) {
  padding: 20px 24px 16px;
  margin-right: 0;
  border-bottom: 1px solid var(--library-border);
}

:global(.seat-dialog .el-dialog__title) {
  color: var(--library-text);
  font-size: 18px;
  font-weight: 700;
}

:global(.seat-dialog .el-dialog__body) {
  padding: 22px 24px 8px;
}

:global(.seat-dialog .el-dialog__footer) {
  padding: 16px 24px 20px;
  border-top: 1px solid var(--library-border);
}

:global(.seat-dialog .el-form-item) {
  margin-bottom: 18px;
}

:global(.seat-dialog .el-form-item__label) {
  color: #5f6f85;
  font-weight: 500;
}

:global(.seat-dialog .el-input__wrapper),
:global(.seat-dialog .el-select__wrapper) {
  border-radius: 12px;
}

:global(.seat-dialog .el-input-number),
:global(.seat-dialog .el-select) {
  width: 100%;
}

:global(.seat-dialog .el-button) {
  border-radius: var(--library-control-radius);
  font-weight: 600;
}

:global(.seat-dialog .el-button--primary) {
  border-color: var(--library-primary);
  background: var(--library-primary);
}

:global(body:has(.seat-manage-page) .el-message-box) {
  padding: 0;
  overflow: hidden;
  border: 1px solid var(--library-border);
  border-radius: var(--library-radius);
  box-shadow: 0 20px 60px rgba(20, 35, 60, 0.16);
}

:global(body:has(.seat-manage-page) .el-message-box__header) {
  padding: 20px 24px 12px;
}

:global(body:has(.seat-manage-page) .el-message-box__title) {
  color: var(--library-text);
  font-size: 18px;
  font-weight: 700;
}

:global(body:has(.seat-manage-page) .el-message-box__content) {
  padding: 10px 24px 20px;
  color: var(--library-muted);
}

:global(body:has(.seat-manage-page) .el-message-box__input .el-input__wrapper) {
  min-height: 42px;
  border-radius: 12px;
}

:global(body:has(.seat-manage-page) .el-message-box__btns) {
  padding: 16px 24px 20px;
  border-top: 1px solid var(--library-border);
}

:global(body:has(.seat-manage-page) .el-message-box__btns .el-button) {
  border-radius: var(--library-control-radius);
  font-weight: 600;
}

:global(body:has(.seat-manage-page) .el-message-box__btns .el-button--primary) {
  border-color: var(--library-primary);
  background: var(--library-primary);
}
</style>
