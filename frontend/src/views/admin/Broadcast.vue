<template>
  <div class="broadcast-page">
    <el-card shadow="never" class="workspace-card">
      <template #header>
        <div class="section-heading">
          <div>
            <h3>系统通知广播</h3>
            <p>面向指定用户群体发布图书馆通知</p>
          </div>
        </div>
      </template>

      <el-form :model="form" label-width="100px" size="default" class="broadcast-form">
        <el-form-item label="发送对象" required>
          <el-radio-group v-model="form.target" class="target-switch">
            <el-radio-button value="all">全体师生</el-radio-button>
            <el-radio-button value="student">仅学生</el-radio-button>
            <el-radio-button value="teacher">仅教师</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="通知标题" required>
          <el-input v-model="form.title" placeholder="如：图书馆国庆闭馆通知" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="通知内容" required>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="5"
            placeholder="请填写通知详细内容，如闭馆时间、活动详情、学习资源推荐等..."
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item>
          <div class="broadcast-actions">
            <el-button type="primary" class="send-button" @click="handleSend" :loading="sending">
              <el-icon><Promotion /></el-icon>
              <span>发送通知</span>
            </el-button>
            <el-button @click="resetForm">清空</el-button>
          </div>
        </el-form-item>
      </el-form>

      <!-- 快捷模板 -->
      <div class="template-section">
        <div class="subsection-heading">
          <div>
            <h4>快捷模板</h4>
            <p>选择常用模板后可继续编辑通知内容</p>
          </div>
          <el-tag type="info" effect="plain">{{ templates.length }} 个模板</el-tag>
        </div>
        <el-row :gutter="12">
          <el-col :span="8" v-for="tpl in templates" :key="tpl.title">
            <el-card shadow="never" class="tpl-card" @click="applyTemplate(tpl)">
              <strong>{{ tpl.title }}</strong>
              <p>{{ tpl.content }}</p>
            </el-card>
          </el-col>
        </el-row>
      </div>
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
.broadcast-page {
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
  padding: 24px;
}

.section-heading h3,
.subsection-heading h4 {
  margin: 0;
  color: var(--library-text);
  font-weight: 700;
}

.section-heading h3 {
  font-size: 17px;
}

.section-heading p,
.subsection-heading p {
  margin: 5px 0 0;
  color: var(--library-muted);
  font-size: 12px;
}

.broadcast-form {
  max-width: 820px;
}

.broadcast-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.broadcast-form :deep(.el-form-item__label) {
  color: #5f6f85;
  font-weight: 500;
}

.target-switch {
  width: auto;
  flex-direction: row;
  flex-wrap: nowrap;
}

.target-switch :deep(.el-radio-button__inner) {
  min-width: 92px;
  border-color: var(--library-border);
  color: #667085;
  font-weight: 600;
}

.target-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  border-color: var(--library-primary);
  color: #fff;
  background: var(--library-primary);
  box-shadow: -1px 0 0 0 var(--library-primary);
}

.broadcast-actions,
.subsection-heading {
  display: flex;
  align-items: center;
}

.broadcast-actions {
  gap: 10px;
}

.send-button {
  min-width: 112px;
}

.send-button .el-icon {
  margin-right: 6px;
}

.template-section {
  padding-top: 22px;
  margin-top: 6px;
  border-top: 1px solid var(--library-border);
}

.subsection-heading {
  min-height: 50px;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 14px;
}

.subsection-heading h4 {
  font-size: 15px;
}

.tpl-card {
  min-height: 104px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.tpl-card :deep(.el-card__body) {
  padding: 16px;
}

.tpl-card strong {
  color: #344054;
  font-size: 14px;
}

.tpl-card p {
  display: -webkit-box;
  margin: 7px 0 0;
  overflow: hidden;
  color: var(--library-muted);
  font-size: 12px;
  line-height: 1.6;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.tpl-card:hover {
  border-color: var(--library-primary);
  background: #f5f8ff;
}
</style>
