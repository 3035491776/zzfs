<template>
  <div class="profile-page">
    <el-row :gutter="24" class="profile-grid">
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="profile-card">
          <template #header>
            <div class="card-heading">
              <div>
                <h3>个人信息</h3>
                <span>管理你的基本账户资料</span>
              </div>
              <span class="heading-mark" aria-hidden="true">人</span>
            </div>
          </template>

          <div class="identity-banner">
            <div class="avatar">{{ form.real_name?.charAt(0) || form.username?.charAt(0) || '用' }}</div>
            <div>
              <strong>{{ form.real_name || '用户' }}</strong>
              <span>{{ form.username }}</span>
            </div>
          </div>

          <el-form :model="form" label-width="90px" class="profile-form">
            <el-form-item label="用户名"><el-input v-model="form.username" disabled /></el-form-item>
            <el-form-item label="真实姓名"><el-input v-model="form.real_name" disabled /></el-form-item>
            <el-form-item label="手机号"><el-input v-model="form.phone" placeholder="请输入手机号" /></el-form-item>
            <el-form-item label="邮箱"><el-input v-model="form.email" placeholder="请输入邮箱地址" /></el-form-item>
            <el-form-item class="form-action">
              <el-button type="primary" @click="saveProfile"><span aria-hidden="true">✓</span>保存信息</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="profile-card security-card">
          <template #header>
            <div class="card-heading">
              <div>
                <h3>安全设置</h3>
                <span>定期更新密码以保障账户安全</span>
              </div>
              <span class="heading-mark safe" aria-hidden="true">盾</span>
            </div>
          </template>

          <div class="security-notice">
            <span aria-hidden="true">!</span>
            <p>建议使用不少于 8 位且包含字母与数字的密码，并避免与其他平台使用相同密码。</p>
          </div>

          <el-form :model="pwForm" label-width="90px" class="profile-form password-form">
            <el-form-item label="原密码"><el-input v-model="pwForm.old_password" type="password" show-password placeholder="请输入原密码" /></el-form-item>
            <el-form-item label="新密码"><el-input v-model="pwForm.new_password" type="password" show-password placeholder="请输入新密码" /></el-form-item>
            <el-form-item class="form-action">
              <el-button type="danger" @click="changePassword"><span aria-hidden="true">↻</span>修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { userApi } from '../api/auth'

const form = reactive({ username: '', real_name: '', phone: '', email: '' })
const pwForm = reactive({ old_password: '', new_password: '' })

onMounted(async () => {
  try {
    const res = await userApi.getProfile()
    Object.assign(form, res.data.user)
  } catch (e) { /* handled */ }
})

async function saveProfile() {
  try {
    await userApi.updateProfile({ phone: form.phone, email: form.email })
    ElMessage.success('信息已更新')
  } catch (e) { /* handled */ }
}

async function changePassword() {
  if (!pwForm.old_password || !pwForm.new_password) {
    ElMessage.warning('请填写完整')
    return
  }
  try {
    await userApi.changePassword(pwForm)
    ElMessage.success('密码修改成功')
    pwForm.old_password = ''
    pwForm.new_password = ''
  } catch (e) { /* handled */ }
}
</script>

<style scoped>
.profile-page {
  width: 100%;
  max-width: 1240px;
  min-height: 100%;
  margin: 0 auto;
}

.profile-grid {
  align-items: stretch;
}

.profile-grid > :deep(.el-col) {
  display: flex;
}

.profile-page :deep(.profile-card) {
  width: 100%;
  min-height: 586px;
  border-color: var(--border-color);
  border-radius: 16px;
  box-shadow: var(--library-card-shadow);
}

.profile-page :deep(.profile-card .el-card__header) {
  min-height: 74px;
  padding: 16px 24px;
  border-bottom-color: var(--border-color);
}

.profile-page :deep(.profile-card .el-card__body) {
  padding: 26px;
}

.card-heading {
  display: flex;
  height: 100%;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.card-heading h3 {
  margin: 0;
  color: var(--text-main);
  font-size: 17px;
  font-weight: 700;
}

.card-heading div > span {
  display: block;
  margin-top: 5px;
  color: var(--text-muted);
  font-size: 12px;
}

.heading-mark {
  display: grid;
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  place-items: center;
  color: var(--brand-blue);
  background: #edf3ff;
  border-radius: 11px;
  font-size: 13px;
  font-weight: 700;
}

.heading-mark.safe {
  color: #1da979;
  background: #eafaf4;
}

.identity-banner {
  display: flex;
  min-height: 94px;
  padding: 18px 20px;
  margin-bottom: 28px;
  box-sizing: border-box;
  align-items: center;
  gap: 16px;
  background: #f5f7fa;
  border-radius: 14px;
}

.avatar {
  display: grid;
  width: 58px;
  height: 58px;
  flex: 0 0 58px;
  place-items: center;
  color: #fff;
  background: var(--brand-blue);
  border-radius: 50%;
  box-shadow: 0 8px 18px rgba(47, 111, 237, 0.2);
  font-size: 22px;
  font-weight: 700;
}

.identity-banner strong,
.identity-banner span {
  display: block;
}

.identity-banner strong {
  color: var(--text-main);
  font-size: 18px;
}

.identity-banner span {
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 13px;
}

.profile-form {
  max-width: 520px;
}

.profile-page :deep(.profile-form .el-form-item) {
  margin-bottom: 20px;
}

.profile-page :deep(.profile-form .el-form-item__label) {
  color: #69778d;
  font-weight: 500;
}

.profile-page :deep(.profile-form .el-input__wrapper) {
  min-height: 46px;
  padding-inline: 15px;
  border-radius: 12px;
  box-shadow: 0 0 0 1px var(--border-color) inset;
}

.profile-page :deep(.profile-form .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--brand-blue) inset;
}

.profile-page :deep(.profile-form .el-input.is-disabled .el-input__wrapper) {
  background: #f3f6fa;
  box-shadow: 0 0 0 1px #e5eaf1 inset;
}

.profile-page :deep(.form-action) {
  margin-top: 26px;
  margin-bottom: 0;
}

.profile-page :deep(.form-action .el-button) {
  height: 44px;
  padding: 0 22px;
  gap: 7px;
  border-radius: 11px;
  font-weight: 600;
}

.profile-page :deep(.form-action .el-button--primary) {
  background: var(--brand-blue);
  border-color: var(--brand-blue);
}

.profile-page :deep(.form-action .el-button--danger) {
  background: #e5484d;
  border-color: #e5484d;
}

.security-notice {
  display: flex;
  padding: 16px 18px;
  margin-bottom: 30px;
  align-items: flex-start;
  gap: 12px;
  color: #68778d;
  background: #f7f9fc;
  border: 1px solid #e8edf4;
  border-radius: 13px;
}

.security-notice > span {
  display: grid;
  width: 24px;
  height: 24px;
  flex: 0 0 24px;
  place-items: center;
  color: #d08a19;
  background: #fff5dc;
  border-radius: 50%;
  font-size: 13px;
  font-weight: 700;
}

.security-notice p {
  margin: 1px 0 0;
  font-size: 13px;
  line-height: 1.65;
}

.password-form {
  margin-top: 8px;
}

@media (max-width: 1199px) {
  .profile-grid {
    row-gap: 24px;
  }

  .profile-page :deep(.profile-card) {
    min-height: auto;
  }
}

@media (max-width: 640px) {
  .profile-page :deep(.profile-card .el-card__header),
  .profile-page :deep(.profile-card .el-card__body) {
    padding-inline: 18px;
  }

  .profile-page :deep(.profile-form .el-form-item) {
    display: block;
  }

  .profile-page :deep(.profile-form .el-form-item__label) {
    width: auto !important;
    justify-content: flex-start;
  }

  .profile-page :deep(.profile-form .el-form-item__content) {
    margin-left: 0 !important;
  }
}
</style>
