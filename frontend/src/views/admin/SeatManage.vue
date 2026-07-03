<template>
  <div>
    <h2>座位管理</h2>

    <el-tabs v-model="activeTab" style="margin-top:20px">
      <!-- Tab 1: 座位列表 -->
      <el-tab-pane label="座位列表" name="seats">
        <div style="margin-bottom:16px"><el-button type="primary" @click="showDialog(null)">新增座位</el-button></div>
        <el-table :data="seats" stripe border>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="seat_number" label="编号" width="100" />
          <el-table-column prop="room_name" label="自习室" />
          <el-table-column prop="floor" label="楼层" width="60" />
          <el-table-column prop="status_text" label="状态" width="80"><template #default="{row}"><el-tag :type="row.status==='available'?'success':row.status==='occupied'?'warning':'info'">{{row.status_text}}</el-tag></template></el-table-column>
          <el-table-column prop="has_power" label="电源" width="60"><template #default="{row}">{{row.has_power?'有':'无'}}</template></el-table-column>
          <el-table-column label="操作" width="120"><template #default="{row}"><el-button size="small" @click="showDialog(row)">编辑</el-button><el-button size="small" type="danger" @click="delSeat(row)">删除</el-button></template></el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- Tab 2: 报修处理 -->
      <el-tab-pane label="报修处理" name="repairs">
        <el-radio-group v-model="repairStatus" @change="fetchRepairs" style="margin-bottom:16px">
          <el-radio-button value="pending">待处理</el-radio-button>
          <el-radio-button value="fixing">维修中</el-radio-button>
          <el-radio-button value="resolved">已修复</el-radio-button>
          <el-radio-button value="rejected">已驳回</el-radio-button>
        </el-radio-group>
        <el-table :data="repairs" stripe border v-loading="repairLoading">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="reporter_name" label="报修人" width="100" />
          <el-table-column prop="seat_number" label="座位" width="100" />
          <el-table-column prop="room_name" label="自习室" width="150" />
          <el-table-column prop="description" label="故障描述" min-width="180" show-overflow-tooltip />
          <el-table-column prop="status_text" label="状态" width="80">
            <template #default="{row}"><el-tag :type="row.status==='resolved'?'success':row.status==='rejected'?'danger':row.status==='fixing'?'warning':'info'" size="small">{{row.status_text}}</el-tag></template>
          </el-table-column>
          <el-table-column prop="create_time" label="报修时间" width="160" />
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{row}">
              <template v-if="row.status==='pending'">
                <el-button size="small" type="warning" @click="markFixing(row)">开始维修</el-button>
                <el-button size="small" type="danger" @click="rejectRepair(row)">驳回</el-button>
              </template>
              <template v-else-if="row.status==='fixing'">
                <el-button size="small" type="success" @click="resolveRepair(row)">标记已修复</el-button>
              </template>
              <span v-else style="color:#909399;font-size:13px">{{ row.review_comment || '已处理' }}</span>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="repairPage" :total="repairTotal" :page-size="10" layout="prev,pager,next" @current-change="fetchRepairs" style="margin-top:20px" />
      </el-tab-pane>
    </el-tabs>

    <!-- 新增/编辑座位弹窗 -->
    <el-dialog :title="editing?'编辑座位':'新增座位'" v-model="dialogVisible" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="编号"><el-input v-model="form.seat_number" /></el-form-item>
        <el-form-item label="自习室"><el-input v-model="form.room_name" /></el-form-item>
        <el-form-item label="楼层"><el-input-number v-model="form.floor" :min="1" :max="10" /></el-form-item>
        <el-form-item label="电源"><el-switch v-model="form.has_power" /></el-form-item>
        <el-form-item label="状态"><el-select v-model="form.status"><el-option label="可用" value="available" /><el-option label="占用" value="occupied" /><el-option label="维护" value="maintenance" /></el-select></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="saveSeat">保存</el-button></template>
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
