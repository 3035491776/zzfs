<template>
  <div>
    <h2>分类管理</h2>
    <div style="margin:20px 0">
      <el-input v-model="newCatName" placeholder="新分类名称" style="width:200px" @keyup.enter="addCategory" />
      <el-button type="primary" @click="addCategory" style="margin-left:8px">添加</el-button>
    </div>
    <el-table :data="categories" stripe border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="分类名称" />
      <el-table-column prop="book_count" label="图书数量" width="100" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="editCategory(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteCategory(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
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
