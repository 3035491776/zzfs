<template>
  <div>
    <h2>🔔 系统通知广播</h2>
    <el-card style="max-width:700px;margin-top:20px">
      <template #header>向用户发送通知</template>
      <el-form :model="form" label-width="100px" size="default">
        <el-form-item label="发送对象" required>
          <el-radio-group v-model="form.target">
            <el-radio-button value="all">全体师生</el-radio-button>
            <el-radio-button value="student">仅学生</el-radio-button>
            <el-radio-button value="teacher">仅教师</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="通知标题" required>
          <el-input v-model="form.title" placeholder="如：图书馆国庆闭馆通知" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="通知内容" required>
          <el-input v-model="form.content" type="textarea" :rows="5"
            placeholder="请填写通知详细内容，如闭馆时间、活动详情、学习资源推荐等..." maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSend" :loading="sending">
            <el-icon><Promotion /></el-icon> 发送通知
          </el-button>
          <el-button @click="resetForm">清空</el-button>
        </el-form-item>
      </el-form>

      <!-- 快捷模板 -->
      <el-divider content-position="left">快捷模板</el-divider>
      <el-row :gutter="12">
        <el-col :span="8" v-for="tpl in templates" :key="tpl.title">
          <el-card shadow="hover" class="tpl-card" @click="applyTemplate(tpl)">
            <div style="font-weight:bold;margin-bottom:4px">{{ tpl.title }}</div>
            <div style="font-size:12px;color:#909399;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ tpl.content }}</div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { broadcastApi } from '../../api/auth'

const form = reactive({ target: 'all', title: '', content: '' })
const sending = ref(false)

const templates = [
  { title: '闭馆通知', target: 'all', content: '各位读者：图书馆将于本周六（X月X日）闭馆进行设备维护，周日恢复正常开放。请提前安排好借还书时间，给您带来的不便敬请谅解。' },
  { title: '新书上架通知', target: 'all', content: '好消息！图书馆近期采购了一批新书，涵盖计算机、文学、历史等领域，共计XX册。欢迎广大师生前来借阅！' },
  { title: '活动通知', target: 'all', content: '图书馆将于下周三举办"书香校园"读书分享活动，届时将邀请知名作家进行讲座。欢迎各位读者踊跃参加！具体时间地点请关注后续通知。' },
  { title: '考试季延时开放', target: 'student', content: '期末考试临近，为方便同学们复习备考，图书馆自即日起延长开放至晚上23:00。请同学们合理安排学习时间，注意休息。' },
  { title: '假期借书提醒', target: 'all', content: '寒假将至，请各位师生在离校前归还即将到期或已逾期的图书。如需假期阅读，可办理假期借阅手续，借期自动延长。' },
  { title: '数据库培训通知', target: 'teacher', content: '图书馆将于本周五下午举办知网数据库使用培训，由专业讲师讲解文献检索技巧和科研工具使用。欢迎各位老师参加！' },
]

function applyTemplate(tpl) {
  form.target = tpl.target
  form.title = tpl.title
  form.content = tpl.content
}

function resetForm() {
  form.target = 'all'; form.title = ''; form.content = ''
}

async function handleSend() {
  if (!form.title.trim()) { ElMessage.warning('请输入通知标题'); return }
  if (!form.content.trim()) { ElMessage.warning('请输入通知内容'); return }
  sending.value = true
  try {
    const r = await broadcastApi.send({ ...form })
    ElMessage.success(r.message)
    resetForm()
  } catch (e) { /* handled */ }
  sending.value = false
}
</script>

<style scoped>
.tpl-card { cursor: pointer; border: 1px solid #e4e7ed; transition: all 0.2s; }
.tpl-card:hover { border-color: #409EFF; background: #ecf5ff; }
</style>
