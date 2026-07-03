<template>
  <div class="library-map-page">
    <el-row :gutter="24" class="map-layout">
      <el-col :xs="24" :lg="17">
        <el-card shadow="never" class="map-card">
          <template #header><h3>图书馆位置</h3></template>
          <div class="library-banner">
            <div class="library-icon" aria-hidden="true">▥</div>
            <div>
              <strong>{{ libraryInfo.name }}</strong>
              <span>{{ libraryInfo.address }}</span>
            </div>
          </div>

          <div id="baidu-map" ref="mapRef" class="baidu-map">
            <div class="map-placeholder">
              <div class="map-pin" aria-hidden="true">⌖</div>
              <strong>百度地图加载区域</strong>
              <span>实际部署时需配置百度地图 AK</span>
              <small>API Key：{{ libraryInfo.baidu_map_ak ? '已配置' : '未配置（请设置 BAIDU_MAP_AK 环境变量）' }}</small>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="7">
        <div class="side-column">
          <el-card shadow="never" class="info-card">
            <template #header><h3>位置信息</h3></template>
            <div class="info-list">
              <div class="info-item">
                <span class="info-icon" aria-hidden="true">⌖</span>
                <div><small>地址</small><strong>{{ libraryInfo.address }}</strong></div>
              </div>
              <div class="info-item">
                <span class="info-icon" aria-hidden="true">↗</span>
                <div><small>坐标</small><strong>{{ libraryInfo.lat }}, {{ libraryInfo.lng }}</strong></div>
              </div>
              <div class="info-item">
                <span class="info-icon" aria-hidden="true">◷</span>
                <div><small>开放时间</small><strong>{{ libraryInfo.opening_hours || '周一至周日 08:00 — 22:00' }}</strong></div>
              </div>
              <div class="info-item">
                <span class="info-icon" aria-hidden="true">☎</span>
                <div><small>联系电话</small><strong>{{ libraryInfo.phone || '010-8888-6666' }}</strong></div>
              </div>
            </div>
          </el-card>

          <el-card shadow="never" class="nearby-card">
            <template #header>
              <div class="card-heading">
                <h3>附近地点</h3>
                <span>{{ points.length }} 个地点</span>
              </div>
            </template>
            <el-input v-model="keyword" placeholder="搜索附近..." clearable @change="searchNearby" />
            <div v-if="points.length" class="nearby-list">
              <button v-for="point in points" :key="`${point.name}-${point.lat}-${point.lng}`" type="button" class="nearby-item">
                <span class="nearby-icon" aria-hidden="true">⌖</span>
                <span class="nearby-text">
                  <strong>{{ point.name }}</strong>
                  <small>{{ point.type }}</small>
                </span>
                <span class="nearby-coordinate">{{ point.lat }}, {{ point.lng }}</span>
              </button>
            </div>
            <div v-else class="nearby-empty">暂无附近地点</div>
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { mapApi } from '../../api/auth'

const libraryInfo = ref({ name: '', address: '', lat: 0, lng: 0, baidu_map_ak: '' })
const points = ref([])
const keyword = ref('')

onMounted(async () => {
  const r = await mapApi.libraryInfo()
  libraryInfo.value = r.data
  searchNearby()
})

async function searchNearby() { const r = await mapApi.nearby(keyword.value); points.value = r.data.list }
</script>

<style scoped>
.library-map-page {
  min-height: 100%;
}

.map-layout {
  align-items: stretch;
}

.map-layout > :deep(.el-col) {
  display: flex;
}

.library-map-page :deep(.map-card),
.library-map-page :deep(.info-card),
.library-map-page :deep(.nearby-card) {
  width: 100%;
  overflow: hidden;
  border-color: var(--border-color);
  border-radius: 16px;
  box-shadow: var(--library-card-shadow);
}

.library-map-page :deep(.map-card .el-card__header),
.library-map-page :deep(.info-card .el-card__header),
.library-map-page :deep(.nearby-card .el-card__header) {
  min-height: 68px;
  padding: 0 24px;
  border-bottom-color: var(--border-color);
}

.library-map-page :deep(.map-card .el-card__header),
.library-map-page :deep(.info-card .el-card__header),
.library-map-page :deep(.nearby-card .el-card__header) {
  display: flex;
  align-items: center;
}

.library-map-page h3 {
  margin: 0;
  color: var(--text-main);
  font-size: 17px;
  font-weight: 700;
}

.library-map-page :deep(.map-card .el-card__body) {
  padding: 24px;
}

.library-banner {
  display: flex;
  min-height: 82px;
  padding: 16px 18px;
  margin-bottom: 20px;
  box-sizing: border-box;
  align-items: center;
  gap: 14px;
  background: #f5f7fa;
  border-radius: 13px;
}

.library-icon {
  display: grid;
  width: 48px;
  height: 48px;
  flex: 0 0 48px;
  place-items: center;
  color: var(--brand-blue);
  background: #e7efff;
  border-radius: 12px;
  font-size: 24px;
  font-weight: 700;
}

.library-banner strong,
.library-banner span {
  display: block;
}

.library-banner strong {
  color: var(--text-main);
  font-size: 17px;
}

.library-banner span {
  margin-top: 5px;
  color: var(--text-muted);
  font-size: 13px;
}

.baidu-map {
  display: flex;
  width: 100%;
  height: 470px;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  color: var(--text-muted);
  background-color: #f4f6fb;
  background-image:
    linear-gradient(rgba(125, 145, 176, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(125, 145, 176, 0.08) 1px, transparent 1px);
  background-size: 44px 44px;
  border: 1px solid #dfe5ee;
  border-radius: 14px;
}

.map-placeholder {
  display: flex;
  align-items: center;
  flex-direction: column;
  text-align: center;
}

.map-pin {
  display: grid;
  width: 60px;
  height: 60px;
  margin-bottom: 16px;
  place-items: center;
  color: #fff;
  background: var(--brand-blue);
  border-radius: 50%;
  box-shadow: 0 10px 24px rgba(47, 111, 237, 0.24);
  font-size: 30px;
}

.map-placeholder strong {
  color: var(--text-main);
  font-size: 16px;
}

.map-placeholder span {
  margin-top: 6px;
  font-size: 13px;
}

.map-placeholder small {
  margin-top: 5px;
  color: var(--brand-blue);
  font-size: 12px;
}

.side-column {
  display: flex;
  width: 100%;
  flex-direction: column;
  gap: 24px;
}

.library-map-page :deep(.info-card .el-card__body) {
  padding: 0;
}

.info-list {
  display: grid;
}

.info-item {
  display: flex;
  min-height: 82px;
  padding: 17px 22px;
  box-sizing: border-box;
  align-items: flex-start;
  gap: 14px;
  border-bottom: 1px solid var(--border-color);
}

.info-item:last-child {
  border-bottom: 0;
}

.info-icon {
  display: grid;
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  place-items: center;
  color: var(--brand-blue);
  background: #edf3ff;
  border-radius: 9px;
  font-size: 16px;
  font-weight: 700;
}

.info-item small,
.info-item strong {
  display: block;
}

.info-item small {
  margin-bottom: 5px;
  color: var(--text-muted);
  font-size: 12px;
}

.info-item strong {
  color: #30394b;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.5;
}

.card-heading {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
}

.card-heading span {
  color: var(--text-muted);
  font-size: 12px;
}

.library-map-page :deep(.nearby-card .el-card__body) {
  padding: 18px;
}

.library-map-page :deep(.nearby-card .el-input__wrapper) {
  height: 40px;
  margin-bottom: 14px;
  border-radius: 10px;
  box-shadow: 0 0 0 1px var(--border-color) inset;
}

.nearby-list {
  display: grid;
  gap: 8px;
}

.nearby-item {
  display: flex;
  width: 100%;
  min-height: 62px;
  padding: 10px;
  align-items: center;
  gap: 11px;
  color: inherit;
  font: inherit;
  text-align: left;
  background: #fff;
  border: 1px solid transparent;
  border-radius: 10px;
  cursor: default;
  transition: background 0.18s ease, border-color 0.18s ease;
}

.nearby-item:hover {
  background: #f8faff;
  border-color: #dce7fb;
}

.nearby-icon {
  display: grid;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  place-items: center;
  color: #8190a6;
  background: #f1f4f8;
  border-radius: 10px;
  font-size: 17px;
}

.nearby-text {
  min-width: 0;
  flex: 1;
}

.nearby-text strong,
.nearby-text small {
  display: block;
}

.nearby-text strong {
  overflow: hidden;
  color: var(--text-main);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nearby-text small {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 11px;
}

.nearby-coordinate {
  max-width: 104px;
  color: #8794a8;
  font-size: 10px;
  line-height: 1.4;
  text-align: right;
}

.nearby-empty {
  padding: 32px 12px;
  color: #98a4b5;
  text-align: center;
  background: #fafbfd;
  border-radius: 10px;
  font-size: 13px;
}

@media (max-width: 1199px) {
  .map-layout {
    row-gap: 24px;
  }

  .baidu-map {
    height: 420px;
  }
}

@media (max-width: 640px) {
  .library-map-page :deep(.map-card .el-card__body) {
    padding: 16px;
  }

  .baidu-map {
    height: 340px;
  }

  .nearby-coordinate {
    display: none;
  }
}
</style>
