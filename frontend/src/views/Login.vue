<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="login-title">智慧图书馆管理系统</h1>
      <p class="login-subtitle">Smart Library Management System</p>

      <el-tabs v-model="activeTab" class="login-tabs">
        <el-tab-pane label="密码登录" name="password">
          <el-form :model="loginForm" :rules="rules" ref="loginFormRef" size="large">
            <el-form-item prop="username">
              <el-input v-model="loginForm.username" placeholder="用户名" prefix-icon="User" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="loginForm.password" type="password" placeholder="密码" prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" @click="handleLogin" style="width:100%">
                登 录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="短信登录" name="sms">
          <el-form :model="smsForm" size="large">
            <el-form-item>
              <el-input v-model="smsForm.phone" placeholder="手机号" prefix-icon="Phone" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="smsForm.code" placeholder="验证码" prefix-icon="Message" style="width:60%">
                <template #append>
                  <el-button :disabled="smsCountdown > 0" @click="sendSms" style="width:100px">
                    {{ smsCountdown > 0 ? `${smsCountdown}s` : '获取验证码' }}
                  </el-button>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="success" @click="handleSmsLogin" style="width:100%">
                短信登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <div class="login-footer">
        <el-button link type="primary" @click="$router.push('/register')">没有账号？立即注册</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('password')
const loading = ref(false)
const smsCountdown = ref(0)

const loginForm = reactive({ username: '', password: '' })
const smsForm = reactive({ phone: '', code: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  if (!loginForm.username || !loginForm.password) return
  loading.value = true
  try {
    await userStore.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    const role = userStore.userRole
    if (role === 'admin') router.push('/admin/dashboard')
    else if (role === 'teacher') router.push('/teacher/books')
    else router.push('/student/books')
  } catch (e) {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

import { authApi } from '../api/auth'

async function sendSms() {
  if (!smsForm.phone) {
    ElMessage.warning('请输入手机号')
    return
  }
  try {
    await authApi.sendSms(smsForm.phone)
    ElMessage.success('验证码已发送（Mock模式，请查看控制台）')
    smsCountdown.value = 60
    const timer = setInterval(() => {
      smsCountdown.value--
      if (smsCountdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e) {
    // handled by interceptor
  }
}

async function handleSmsLogin() {
  if (!smsForm.phone || !smsForm.code) {
    ElMessage.warning('请输入手机号和验证码')
    return
  }
  try {
    const res = await authApi.loginSms({ phone: smsForm.phone, code: smsForm.code })
    const store = useUserStore()
    store.token = res.data.token
    store.user = res.data.user
    localStorage.setItem('token', res.data.token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    ElMessage.success('登录成功')
    const role = store.userRole
    if (role === 'admin') router.push('/admin/dashboard')
    else if (role === 'teacher') router.push('/teacher/books')
    else router.push('/student/books')
  } catch (e) {
    // handled
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.login-title { text-align: center; font-size: 24px; margin-bottom: 8px; color: #303133; }
.login-subtitle { text-align: center; font-size: 13px; color: #909399; margin-bottom: 30px; }
.login-footer { text-align: center; margin-top: 20px; }
</style>
