<template>
  <div class="seat-reserve-page">
    <el-tabs v-model="mainTab" class="main-tabs student-tabs">
      <!-- ============================================================ -->
      <!-- Tab 1: 座位预约 -->
      <!-- ============================================================ -->
      <el-tab-pane label="座位预约" name="reserve">
        <section class="seat-selection">
        <el-tabs v-model="roomTab" @tab-click="fetchSeats" type="card" class="room-tabs">
          <el-tab-pane v-for="room in rooms" :key="room" :label="room" :name="room" />
        </el-tabs>
        <el-row :gutter="20" class="seat-grid">
          <el-col :xs="24" :sm="12" :lg="6" v-for="seat in filteredSeats" :key="seat.id">
            <el-card shadow="never" :class="['seat-card', seat.status]" @click="seat.status==='available'&&showReserve(seat)">
              <div class="seat-card__header">
                <strong>{{ seat.seat_number }}</strong>
                <el-tag
                  :type="seat.status==='available'?'success':seat.status==='occupied'?'primary':'danger'"
                  size="small"
                  effect="light"
                  round
                >
                  {{ seat.status==='available'?'可用':seat.status==='occupied'?'已预约':seat.status==='maintenance'?'维修中':seat.status_text }}
                </el-tag>
              </div>
              <p class="seat-card__location">{{ seat.room_name }} · F{{ seat.floor }}</p>
              <p :class="['seat-card__power', { muted: !seat.has_power }]">
                <span aria-hidden="true">ϟ</span>
                {{ seat.has_power ? '有电源' : '无电源' }}
              </p>
              <el-button
                type="primary"
                class="seat-card__action"
                :disabled="seat.status!=='available'"
                @click.stop="showReserve(seat)"
              >
                {{ seat.status==='available'?'预约':seat.status==='occupied'?'已预约':seat.status==='maintenance'?'维修中':seat.status_text }}
              </el-button>
            </el-card>
          </el-col>
        </el-row>
        </section>

        <section class="reservations-card">
        <header class="section-header"><h3>我的预约</h3></header>
        <el-table :data="myReservations" stripe class="reservations-table">
          <el-table-column prop="seat_number" label="座位" width="100" />
          <el-table-column prop="room_name" label="自习室" width="150" />
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column label="时段" width="150"><template #default="{row}">{{ row.start_time }}-{{ row.end_time }}</template></el-table-column>
          <el-table-column prop="status_text" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status==='reserved'?'primary':row.status==='checked_in'?'success':'info'" size="small" effect="light" round>{{ row.status_text }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" align="right">
            <template #default="{ row }">
              <el-button v-if="row.status==='reserved'" size="small" type="success" @click="checkin(row)">签到</el-button>
              <el-button v-if="row.status==='reserved'" size="small" type="danger" plain @click="cancel(row)">取消</el-button>
            </template>
          </el-table-column>
        </el-table>
        </section>
      </el-tab-pane>

      <!-- ============================================================ -->
      <!-- Tab 2: 座位报修 -->
      <!-- ============================================================ -->
      <el-tab-pane label="座位报修" name="repair">
        <section class="repair-panel">
        <!-- 报修表单 -->
        <el-card shadow="never" class="repair-card">
          <template #header>
            <div class="card-title">
              <strong>座位设施损坏？请告诉我们</strong>
              <span>填写故障信息，我们会尽快处理</span>
            </div>
          </template>
          <el-form label-width="100px" size="default">
            <el-form-item label="损坏座位" required>
              <el-select v-model="repairSeatId" placeholder="请选择座位" filterable style="width:100%">
                <el-option v-for="s in allSeats" :key="s.id"
                  :label="`${s.seat_number} (${s.room_name} F${s.floor})`"
                  :value="s.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="故障描述" required>
              <el-input v-model="repairDesc" type="textarea" :rows="3" placeholder="请描述具体故障（如：电源插座松动、桌面破损、灯光闪烁等）" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="submitRepair" :loading="repairSubmitting">提交报修</el-button>
              <el-button @click="repairSeatId=0;repairDesc=''">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 我的报修记录 -->
        <el-card shadow="never" class="repair-card repair-records">
          <template #header>
            <div class="card-title">
              <strong>我的报修记录</strong>
              <span>查看设施报修处理进度</span>
            </div>
          </template>
          <el-table :data="myRepairs" stripe v-loading="repairLoading">
            <el-table-column prop="seat_number" label="座位" width="100" />
            <el-table-column prop="room_name" label="自习室" width="150" />
            <el-table-column prop="description" label="故障描述" min-width="160" show-overflow-tooltip />
            <el-table-column prop="status_text" label="状态" width="90">
              <template #default="{row}"><el-tag :type="row.status==='resolved'?'success':row.status==='rejected'?'danger':row.status==='fixing'?'warning':'info'" size="small">{{row.status_text}}</el-tag></template>
            </el-table-column>
            <el-table-column prop="review_comment" label="处理意见" min-width="120" show-overflow-tooltip />
            <el-table-column prop="create_time" label="报修时间" width="160" />
          </el-table>
          <div class="pagination-row">
            <el-pagination v-model:current-page="repairPage" :total="repairTotal" :page-size="10"
              layout="prev,pager,next" @current-change="fetchMyRepairs" />
          </div>
        </el-card>
        </section>
      </el-tab-pane>
    </el-tabs>

    <!-- 预约弹窗 -->
    <el-dialog title="预约座位" v-model="dialogVisible" width="420px" class="reserve-dialog">
      <p class="dialog-seat">座位：<strong>{{ selectedSeat?.seat_number }}</strong><span>{{ selectedSeat?.room_name }}</span></p>
      <el-form label-width="80px">
        <el-form-item label="日期"><el-date-picker v-model="reserveDate" type="date" :disabled-date="disabledDate" /></el-form-item>
        <el-form-item label="开始时间"><el-time-select v-model="startTime" :max-time="endTime" placeholder="开始" start="08:00" step="01:00" end="21:00" /></el-form-item>
        <el-form-item label="结束时间"><el-time-select v-model="endTime" :min-time="startTime" placeholder="结束" start="09:00" step="01:00" end="22:00" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="doReserve">确认预约</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { seatApi, seatRepairApi } from '../../api/auth'

const mainTab = ref('reserve')

// ---- 座位预约 ----
const allSeats = ref([])
const seats = ref([])
const myReservations = ref([])
const rooms = ref([])
const roomTab = ref('')
const dialogVisible = ref(false)
const selectedSeat = ref(null)
const reserveDate = ref(new Date())
const startTime = ref('08:00')
const endTime = ref('10:00')
const filteredSeats = computed(() => roomTab.value ? allSeats.value.filter(s => s.room_name === roomTab.value) : allSeats.value)

onMounted(() => { fetchSeats(); fetchMyReservations(); fetchMyRepairs() })

async function fetchSeats() {
  const r = await seatApi.list()
  allSeats.value = r.data.list; seats.value = r.data.list
  rooms.value = r.data.rooms || []
  if (!roomTab.value && rooms.value.length) roomTab.value = rooms.value[0]
}
async function fetchMyReservations() { const r = await seatApi.myReservations(); myReservations.value = r.data.list }
function disabledDate(time) { const today = new Date(); today.setHours(0,0,0,0); const max = new Date(today); max.setDate(max.getDate()+7); return time.getTime() < today.getTime()-86400000 || time.getTime() > max.getTime() }
function showReserve(seat) { selectedSeat.value = seat; dialogVisible.value = true }
async function doReserve() {
  if (!selectedSeat.value || !startTime.value || !endTime.value) return
  try {
    await seatApi.reserve(selectedSeat.value.id, { date: reserveDate.value.toISOString().split('T')[0], start_time: startTime.value, end_time: endTime.value })
    ElMessage.success('预约成功'); dialogVisible.value = false; fetchSeats(); fetchMyReservations()
  } catch (e) { /* handled */ }
}
async function checkin(row) { try { await seatApi.checkin(row.id); ElMessage.success('签到成功'); fetchMyReservations() } catch (e) { /* handled */ } }
async function cancel(row) { try { await seatApi.cancel(row.id); ElMessage.success('已取消'); fetchMyReservations(); fetchSeats() } catch (e) { /* handled */ } }

// ---- 座位报修 ----
const repairSeatId = ref(0)
const repairDesc = ref('')
const repairSubmitting = ref(false)
const myRepairs = ref([])
const repairPage = ref(1)
const repairTotal = ref(0)
const repairLoading = ref(false)

async function submitRepair() {
  if (!repairSeatId.value) { ElMessage.warning('请选择要报修的座位'); return }
  if (!repairDesc.value.trim()) { ElMessage.warning('请描述故障情况'); return }
  repairSubmitting.value = true
  try {
    await seatRepairApi.submit({ seat_id: repairSeatId.value, description: repairDesc.value })
    ElMessage.success('报修已提交，管理员会尽快处理')
    repairSeatId.value = 0; repairDesc.value = ''; fetchMyRepairs()
  } catch (e) { /* handled */ }
  repairSubmitting.value = false
}

async function fetchMyRepairs() {
  repairLoading.value = true
  try { const r = await seatRepairApi.my({ page: repairPage.value }); myRepairs.value = r.data.list; repairTotal.value = r.data.total } catch (e) { /* */ }
  repairLoading.value = false
}
</script>

<style scoped>
.seat-reserve-page {
  min-height: 100%;
}

.seat-reserve-page :deep(.main-tabs > .el-tabs__header) {
  margin: 0;
  padding: 12px 26px 0;
  background: #fff;
  border: 1px solid var(--border-color);
  border-bottom: 0;
  border-radius: 16px 16px 0 0;
}

.seat-reserve-page :deep(.main-tabs > .el-tabs__header .el-tabs__nav-wrap::after) {
  height: 1px;
  background: var(--border-color);
}

.seat-selection,
.repair-panel {
  padding: 26px;
  background: #fff;
  border: 1px solid var(--border-color);
  border-top: 0;
  border-radius: 0 0 16px 16px;
  box-shadow: var(--library-card-shadow);
}

.seat-reserve-page :deep(.room-tabs > .el-tabs__header) {
  margin: 0 0 24px;
  border: 0;
}

.seat-reserve-page :deep(.room-tabs > .el-tabs__header .el-tabs__nav) {
  display: flex;
  gap: 10px;
  border: 0;
}

.seat-reserve-page :deep(.room-tabs > .el-tabs__header .el-tabs__item) {
  height: 42px;
  padding: 0 20px;
  color: #718096;
  background: #fff;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  transition: color 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.seat-reserve-page :deep(.room-tabs > .el-tabs__header .el-tabs__item:first-child),
.seat-reserve-page :deep(.room-tabs > .el-tabs__header .el-tabs__item:last-child) {
  border-radius: 12px;
}

.seat-reserve-page :deep(.room-tabs > .el-tabs__header .el-tabs__item.is-active) {
  color: var(--brand-blue);
  background: #f8faff;
  border-color: var(--brand-blue);
  box-shadow: 0 0 0 1px rgba(47, 111, 237, 0.08);
}

.seat-grid {
  row-gap: 20px;
}

.seat-reserve-page :deep(.seat-card) {
  position: relative;
  height: 228px;
  overflow: hidden;
  cursor: default;
  background: #fff;
  border: 1px solid var(--border-color);
  border-left-width: 5px;
  border-radius: var(--library-radius);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.seat-reserve-page :deep(.seat-card.available) {
  cursor: pointer;
  border-left-color: #20b985;
}

.seat-reserve-page :deep(.seat-card.occupied) {
  border-left-color: var(--brand-blue);
}

.seat-reserve-page :deep(.seat-card.maintenance) {
  border-left-color: #ef4444;
}

.seat-reserve-page :deep(.seat-card.available:hover) {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(36, 59, 92, 0.09);
}

.seat-reserve-page :deep(.seat-card .el-card__body) {
  display: flex;
  height: 100%;
  padding: 24px;
  box-sizing: border-box;
  flex-direction: column;
}

.seat-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.seat-card__header strong {
  color: var(--text-main);
  font-size: 21px;
  font-weight: 700;
}

.seat-card__location {
  margin: 20px 0 0;
  color: var(--text-muted);
  font-size: 14px;
}

.seat-card__power {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 14px 0 0;
  color: #20b985;
  font-size: 13px;
}

.seat-card__power.muted {
  color: #aab4c3;
}

.seat-card__power span {
  font-size: 17px;
  font-weight: 700;
}

.seat-reserve-page :deep(.seat-card__action) {
  width: 100%;
  height: 40px;
  margin-top: auto;
  border-radius: 10px;
  font-weight: 600;
}

.seat-reserve-page :deep(.seat-card__action.is-disabled) {
  color: #fff;
  background: #a8c2f8;
  border-color: #a8c2f8;
}

.reservations-card {
  margin-top: 28px;
  overflow: hidden;
  background: #fff;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  box-shadow: var(--library-card-shadow);
}

.section-header {
  display: flex;
  min-height: 68px;
  padding: 0 26px;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
}

.section-header h3 {
  margin: 0;
  color: var(--text-main);
  font-size: 17px;
  font-weight: 700;
}

.repair-panel {
  display: grid;
  gap: 22px;
}

.seat-reserve-page :deep(.repair-card) {
  border-color: var(--border-color);
  border-radius: var(--library-radius);
}

.seat-reserve-page :deep(.repair-card .el-card__header) {
  padding: 20px 24px;
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

.seat-reserve-page :deep(.repair-card .el-input__wrapper),
.seat-reserve-page :deep(.repair-card .el-textarea__inner) {
  border-radius: 10px;
}

.pagination-row {
  display: flex;
  padding: 18px 0 2px;
  justify-content: flex-end;
}

.dialog-seat {
  display: flex;
  padding: 14px 16px;
  margin: 0 0 20px;
  align-items: center;
  gap: 6px;
  color: #64748b;
  background: #f5f8fd;
  border-radius: 10px;
}

.dialog-seat strong {
  color: var(--text-main);
  font-size: 17px;
}

.dialog-seat span {
  margin-left: auto;
  color: var(--text-muted);
  font-size: 13px;
}

:deep(.reserve-dialog) {
  border-radius: 16px;
}

:deep(.reserve-dialog .el-dialog__header) {
  padding-bottom: 18px;
  border-bottom: 1px solid var(--border-color);
}

:deep(.reserve-dialog .el-date-editor),
:deep(.reserve-dialog .el-select) {
  width: 100%;
}

@media (max-width: 768px) {
  .seat-selection,
  .repair-panel {
    padding: 18px;
  }

  .seat-reserve-page :deep(.main-tabs > .el-tabs__header) {
    padding-inline: 18px;
  }

  .seat-reserve-page :deep(.room-tabs > .el-tabs__header .el-tabs__nav) {
    padding-bottom: 4px;
    overflow-x: auto;
  }

  .reservations-card {
    overflow-x: auto;
  }

  .section-header {
    padding-inline: 18px;
  }
}
</style>
