<template>
  <div class="register-container">
    <div class="register-card">
      <h1 class="register-title">用户注册</h1>
      <el-form :model="form" :rules="rules" ref="formRef" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码(6-16位，含数字和字母)" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item prop="real_name">
          <el-input v-model="form.real_name" placeholder="真实姓名" prefix-icon="UserFilled" />
        </el-form-item>
        <el-form-item prop="role">
          <el-radio-group v-model="form.role">
            <el-radio label="student">学生</el-radio>
            <el-radio label="teacher">教师</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item prop="phone">
          <el-input v-model="form.phone" placeholder="手机号（选填）" prefix-icon="Phone" />
        </el-form-item>
        <el-form-item prop="email">
          <el-input v-model="form.email" placeholder="邮箱（选填）" prefix-icon="Message" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleRegister" style="width:100%">
            注 册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="register-footer">
        <el-button link type="primary" @click="$router.push('/login')">已有账号？去登录</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)

const form = reactive({ username: '', password: '', real_name: '', role: 'student', phone: '', email: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, max: 16, message: '6-16位', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
}

async function handleRegister() {
  if (!form.username || !form.password || !form.real_name) return
  loading.value = true
  try {
    await userStore.register({ ...form })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (e) {
    // handled
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.register-card {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.register-title { text-align: center; font-size: 24px; margin-bottom: 30px; color: #303133; }
.register-footer { text-align: center; margin-top: 20px; }
</style>
