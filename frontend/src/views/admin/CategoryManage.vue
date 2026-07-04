<template>
  <div class="category-manage-page">
    <el-card shadow="never" class="workspace-card">
      <template #header>
        <div class="section-heading">
          <div>
            <h3>分类目录</h3>
            <p>维护馆藏图书的分类体系</p>
          </div>
          <span class="heading-mark" aria-hidden="true">类</span>
        </div>
      </template>

      <div class="category-toolbar">
        <div class="toolbar-copy">
          <strong>新增分类</strong>
          <span>输入分类名称后按回车或点击添加</span>
        </div>
        <span class="toolbar-spacer"></span>
        <el-input
          v-model="newCatName"
          class="category-input"
          placeholder="请输入新分类名称"
          clearable
          @keyup.enter="addCategory"
        >
          <template #prefix><el-icon><Grid /></el-icon></template>
        </el-input>
        <el-button type="primary" class="add-button" @click="addCategory">
          <el-icon><Plus /></el-icon>
          <span>添加分类</span>
        </el-button>
      </div>

      <el-table :data="categories" stripe class="category-table">
        <el-table-column prop="id" label="ID" width="90" />
        <el-table-column prop="name" label="分类名称" min-width="240">
          <template #default="{ row }">
            <span class="category-name">
              <i aria-hidden="true"></i>
              {{ row.name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="book_count" label="图书数量" width="130">
          <template #default="{ row }">
            <el-tag type="info" effect="plain">{{ row.book_count }} 本</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editCategory(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteCategory(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span>共 {{ categories.length }} 个图书分类</span>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { categoryApi } from '../../api/auth'

const categories = ref([])
const newCatName = ref('')

onMounted(() => fetchData())

async function fetchData() { const r = await categoryApi.list(); categories.value = r.data.list }

async function addCategory() {
  if (!newCatName.value) return
  try { await categoryApi.add({ name: newCatName.value }); newCatName.value = ''; ElMessage.success('已添加'); fetchData() } catch (e) { /* handled */ }
}

async function editCategory(row) {
  try {
    const { value } = await ElMessageBox.prompt('新名称', '编辑分类', { inputValue: row.name })
    if (value) { await categoryApi.update(row.id, { name: value }); fetchData(); ElMessage.success('已更新') }
  } catch (e) { /* cancel */ }
}

async function deleteCategory(row) {
  try {
    await ElMessageBox.confirm(`确定删除 "${row.name}"？`, '确认')
    await categoryApi.delete(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch (e) { /* cancel or error */ }
}
</script>

<style scoped>
.category-manage-page {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
}

.workspace-card :deep(.el-card__header) {
  min-height: 74px;
  padding: 16px 24px;
  border-bottom-color: var(--library-border);
}

.workspace-card :deep(.el-card__body) {
  padding: 22px 24px 18px;
}

.section-heading,
.category-toolbar,
.category-name,
.table-footer {
  display: flex;
  align-items: center;
}

.section-heading {
  justify-content: space-between;
  gap: 18px;
}

.section-heading h3 {
  margin: 0;
  color: var(--library-text);
  font-size: 17px;
  font-weight: 700;
}

.section-heading p {
  margin: 5px 0 0;
  color: var(--library-muted);
  font-size: 12px;
}

.heading-mark {
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

.category-toolbar {
  gap: 12px;
  padding: 16px;
  margin-bottom: 18px;
  border: 1px solid var(--library-border);
  border-radius: 14px;
  background: #f9fbfd;
}

.toolbar-copy {
  display: flex;
  min-width: 190px;
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

.category-input {
  width: min(360px, 38%);
}

.add-button {
  min-width: 118px;
  height: 40px;
}

.add-button .el-icon {
  margin-right: 6px;
}

.category-table {
  width: 100%;
  border: 1px solid var(--library-border);
  border-radius: 14px;
  overflow: hidden;
}

.category-table :deep(.cell) {
  padding-inline: 16px;
}

.category-name {
  gap: 10px;
  color: #344054;
  font-weight: 600;
}

.category-name i {
  width: 8px;
  height: 8px;
  flex: 0 0 8px;
  border-radius: 50%;
  background: var(--library-primary);
  box-shadow: 0 0 0 4px #edf3ff;
}

.table-footer {
  min-height: 50px;
  justify-content: flex-end;
  padding-top: 14px;
  color: var(--library-muted);
  font-size: 13px;
}

:global(body:has(.category-manage-page) .el-message-box) {
  padding: 0;
  overflow: hidden;
  border: 1px solid var(--library-border);
  border-radius: var(--library-radius);
  box-shadow: 0 20px 60px rgba(20, 35, 60, 0.16);
}

:global(body:has(.category-manage-page) .el-message-box__header) {
  padding: 20px 24px 12px;
}

:global(body:has(.category-manage-page) .el-message-box__title) {
  color: var(--library-text);
  font-size: 18px;
  font-weight: 700;
}

:global(body:has(.category-manage-page) .el-message-box__content) {
  padding: 10px 24px 20px;
  color: var(--library-muted);
}

:global(body:has(.category-manage-page) .el-message-box__input .el-input__wrapper) {
  min-height: 42px;
  border-radius: 12px;
}

:global(body:has(.category-manage-page) .el-message-box__btns) {
  padding: 16px 24px 20px;
  border-top: 1px solid var(--library-border);
}

:global(body:has(.category-manage-page) .el-message-box__btns .el-button) {
  border-radius: var(--library-control-radius);
  font-weight: 600;
}

:global(body:has(.category-manage-page) .el-message-box__btns .el-button--primary) {
  border-color: var(--library-primary);
  background: var(--library-primary);
}
</style>
