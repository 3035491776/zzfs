<template>
  <div class="login-container">
    <div class="library-atmosphere" aria-hidden="true">
      <div class="book-field">
        <article
          v-for="(book, index) in floatingBooks"
          :key="book.title"
          class="floating-book"
          :class="[`book--${index + 1}`, `book--${book.depth}`]"
        >
          <span class="book-category">{{ book.category }}</span>
          <strong>{{ book.title }}</strong>
          <span class="book-author">{{ book.author }}</span>
        </article>
      </div>
      <div class="background-veil"></div>
    </div>

    <div class="login-card">
      <h1 class="login-title">智慧图书馆管理系统</h1>
      <p class="login-welcome">欢迎回来，请登录您的账号</p>
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

const floatingBooks = [
  { title: '算法导论', author: 'Thomas H. Cormen', category: '计算机科学', depth: 'near' },
  { title: '人工智能：一种现代方法', author: 'Stuart Russell', category: '计算机科学', depth: 'far' },
  { title: '计算机网络', author: 'Andrew S. Tanenbaum', category: '计算机科学', depth: 'mid' },
  { title: '枪炮、病菌与钢铁', author: '贾雷德·戴蒙德', category: '历史', depth: 'far' },
  { title: '原则', author: '瑞·达利欧', category: '经济', depth: 'mid' },
  { title: '红楼梦', author: '曹雪芹', category: '文学', depth: 'near' },
  { title: '活着', author: '余华', category: '文学', depth: 'mid' },
  { title: '百年孤独', author: '加西亚·马尔克斯', category: '文学', depth: 'mid' },
  { title: '苏菲的世界', author: '乔斯坦·贾德', category: '哲学', depth: 'far' },
  { title: '三体', author: '刘慈欣', category: '文学', depth: 'near' },
  { title: '史记', author: '司马迁', category: '历史', depth: 'mid' },
  { title: '万历十五年', author: '黄仁宇', category: '历史', depth: 'far' },
  { title: '人类简史', author: '尤瓦尔·赫拉利', category: '历史', depth: 'mid' },
  { title: '国富论', author: '亚当·斯密', category: '经济', depth: 'near' },
  { title: '经济学原理', author: '曼昆', category: '经济', depth: 'far' },
  { title: '理想国', author: '柏拉图', category: '哲学', depth: 'mid' },
  { title: '时间简史', author: '斯蒂芬·霍金', category: '自然科学', depth: 'far' },
  { title: '自私的基因', author: '理查德·道金斯', category: '自然科学', depth: 'mid' },
]

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
:global(html:has(.login-container)),
:global(body:has(.login-container)),
:global(#app:has(.login-container)) {
  width: 100%;
  min-width: 0;
  overflow-x: hidden;
}

.login-container {
  position: relative;
  box-sizing: border-box;
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 20px;
  overflow: hidden;
  isolation: isolate;
  background: #eef4ff;
}

.library-atmosphere,
.book-field,
.background-veil {
  position: absolute;
  inset: 0;
}

.library-atmosphere {
  z-index: -1;
  overflow: hidden;
  background:
    radial-gradient(circle at 17% 14%, rgba(255, 255, 255, 0.94) 0, rgba(255, 255, 255, 0) 28%),
    radial-gradient(circle at 86% 78%, rgba(199, 217, 255, 0.44) 0, rgba(199, 217, 255, 0) 32%),
    radial-gradient(circle at 62% 30%, rgba(255, 255, 255, 0.42) 0 1px, rgba(255, 255, 255, 0) 2px) 0 0 / 24px 24px,
    linear-gradient(112deg, rgba(255, 255, 255, 0.22), rgba(224, 234, 252, 0.08) 48%, rgba(255, 255, 255, 0.2)),
    linear-gradient(180deg, #fafbfc 0%, #eef4ff 48%, #e4edff 100%);
}

.book-field {
  overflow: hidden;
}

.background-veil {
  z-index: 5;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(0.6px);
}

.floating-book {
  --book-width: 108px;
  --tilt: 0deg;
  --cover: #4778bd;
  --cover-deep: #315d9c;
  --cover-ink: #f8fbff;
  --tag-bg: rgba(255, 255, 255, 0.18);
  --duration: 46s;
  --delay: 0s;
  position: absolute;
  top: var(--top);
  left: var(--left);
  width: var(--book-width);
  aspect-ratio: 0.72;
  display: flex;
  flex-direction: column;
  padding: 14px 12px 12px 16px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 5px 10px 10px 5px;
  color: var(--cover-ink);
  background:
    linear-gradient(90deg, rgba(0, 0, 0, 0.13) 0, transparent 7px),
    linear-gradient(145deg, var(--cover) 0%, var(--cover-deep) 100%);
  box-shadow:
    0 18px 38px rgba(70, 98, 146, 0.16),
    inset -3px 0 rgba(255, 255, 255, 0.12);
  pointer-events: none;
  contain: layout paint;
  will-change: transform;
  animation-duration: var(--duration);
  animation-delay: var(--delay);
  animation-timing-function: ease-in-out;
  animation-iteration-count: infinite;
  animation-direction: alternate;
}

.floating-book::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 7px;
  width: 1px;
  background: rgba(255, 255, 255, 0.24);
}

.floating-book::after {
  content: "";
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 24px;
  height: 1px;
  background: rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px rgba(255, 255, 255, 0.3);
}

.floating-book:nth-child(odd) {
  animation-name: drift-right;
}

.floating-book:nth-child(even) {
  animation-name: drift-left;
}

.book-category {
  align-self: flex-start;
  max-width: 100%;
  margin-bottom: auto;
  padding: 3px 6px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 999px;
  background: var(--tag-bg);
  font-size: 8px;
  line-height: 1.2;
  letter-spacing: 0.04em;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.floating-book strong {
  display: -webkit-box;
  margin: 12px 0 6px;
  overflow: hidden;
  font-family: "Noto Serif SC", "Songti SC", "SimSun", serif;
  font-size: 13px;
  line-height: 1.42;
  letter-spacing: 0.03em;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.book-author {
  overflow: hidden;
  font-size: 8px;
  line-height: 1.35;
  opacity: 0.72;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book--near {
  z-index: 3;
  --lift: -14px;
  --right-start: -24px;
  --right-mid: 28px;
  --right-end: 82px;
  --left-start: 48px;
  --left-mid: -18px;
  --left-end: -82px;
  opacity: 0.84;
  filter: blur(0.3px);
}

.book--mid {
  z-index: 2;
  --lift: -8px;
  --right-start: -18px;
  --right-mid: 24px;
  --right-end: 60px;
  --left-start: 38px;
  --left-mid: -14px;
  --left-end: -60px;
  opacity: 0.56;
  filter: blur(1.2px);
}

.book--far {
  z-index: 1;
  --lift: -4px;
  --right-start: -12px;
  --right-mid: 18px;
  --right-end: 44px;
  --left-start: 28px;
  --left-mid: -10px;
  --left-end: -44px;
  opacity: 0.3;
  filter: blur(4px);
}

.book--1  { --top: 7%;  --left: 6%;  --book-width: 126px; --tilt: -5deg; --duration: 34s; --delay: -18s; --cover: #4778bd; --cover-deep: #315d9c; }
.book--2  { --top: 4%;  --left: 23%; --book-width: 66px;  --tilt: 4deg;  --duration: 50s; --delay: -9s;  --cover: #bf8b55; --cover-deep: #9b6840; }
.book--3  { --top: 29%; --left: 71%; --book-width: 94px;  --tilt: 6deg;  --duration: 40s; --delay: -31s; --cover: #3f8f8a; --cover-deep: #286a68; }
.book--4  { --top: 5%;  --left: 91%; --book-width: 64px;  --tilt: -3deg; --duration: 48s; --delay: -22s; --cover: #b9a56c; --cover-deep: #8f7c49; }
.book--5  { --top: 35%; --left: 7%;  --book-width: 98px;  --tilt: 7deg;  --duration: 42s; --delay: -13s; --cover: #ba6b52; --cover-deep: #914c3b; }
.book--6  { --top: 67%; --left: 8%;  --book-width: 128px; --tilt: 3deg;  --duration: 36s; --delay: -40s; --cover: #8e3f4c; --cover-deep: #672b37; }
.book--7  { --top: 74%; --left: 19%; --book-width: 92px;  --tilt: -7deg; --duration: 38s; --delay: -29s; --cover: #5e8b60; --cover-deep: #416c46; }
.book--8  { --top: 47%; --left: 21%; --book-width: 96px;  --tilt: -4deg; --duration: 41s; --delay: -7s;  --cover: #d38a54; --cover-deep: #aa6337; }
.book--9  { --top: 19%; --left: 23%; --book-width: 62px;  --tilt: 5deg;  --duration: 52s; --delay: -36s; --cover: #7689a6; --cover-deep: #536982; }
.book--10 { --top: 7%;  --left: 78%; --book-width: 124px; --tilt: -6deg; --duration: 32s; --delay: -15s; --cover: #315f82; --cover-deep: #24465f; }
.book--11 { --top: 3%;  --left: 19%; --book-width: 92px;  --tilt: 3deg;  --duration: 37s; --delay: -24s; --cover: #6f7653; --cover-deep: #50563a; }
.book--12 { --top: 80%; --left: 75%; --book-width: 68px;  --tilt: 8deg;  --duration: 49s; --delay: -46s; --cover: #a45c64; --cover-deep: #7d3f47; }
.book--13 { --top: 39%; --left: 72%; --book-width: 96px;  --tilt: -5deg; --duration: 44s; --delay: -20s; --cover: #4f8873; --cover-deep: #35634f; }
.book--14 { --top: 64%; --left: 84%; --book-width: 128px; --tilt: 5deg;  --duration: 35s; --delay: -33s; --cover: #ad7548; --cover-deep: #855531; }
.book--15 { --top: 43%; --left: 88%; --book-width: 64px;  --tilt: -8deg; --duration: 51s; --delay: -17s; --cover: #7894a1; --cover-deep: #546f7a; }
.book--16 { --top: 78%; --left: 75%; --book-width: 94px;  --tilt: 4deg;  --duration: 39s; --delay: -28s; --cover: #9a8351; --cover-deep: #725e37; }
.book--17 { --top: 40%; --left: 5%;  --book-width: 66px;  --tilt: -3deg; --duration: 47s; --delay: -38s; --cover: #5574a0; --cover-deep: #394f73; }
.book--18 { --top: 23%; --left: 82%; --book-width: 98px;  --tilt: 6deg;  --duration: 43s; --delay: -11s; --cover: #3a827d; --cover-deep: #275e5b; }

@keyframes drift-right {
  0% {
    transform: translate3d(var(--right-start), 2px, 0) rotate(var(--tilt));
  }
  43% {
    transform: translate3d(var(--right-mid), var(--lift), 0) rotate(var(--tilt));
  }
  100% {
    transform: translate3d(var(--right-end), 5px, 0) rotate(var(--tilt));
  }
}

@keyframes drift-left {
  0% {
    transform: translate3d(var(--left-start), 4px, 0) rotate(var(--tilt));
  }
  54% {
    transform: translate3d(var(--left-mid), var(--lift), 0) rotate(var(--tilt));
  }
  100% {
    transform: translate3d(var(--left-end), 0, 0) rotate(var(--tilt));
  }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  padding: 40px;
  border: 1px solid rgba(211, 222, 239, 0.88);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow:
    0 24px 60px rgba(76, 101, 144, 0.12),
    0 6px 18px rgba(76, 101, 144, 0.06);
  backdrop-filter: blur(18px);
}

.login-title {
  margin: 0;
  color: #1f2d42;
  font-family: "Noto Serif SC", "Songti SC", "SimSun", serif;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-align: center;
}

.login-welcome {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 14px;
  line-height: 1.5;
  text-align: center;
}

.login-subtitle {
  margin: 5px 0 26px;
  color: #7b8ba3;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-align: center;
}

.login-tabs :deep(.el-tabs__header) {
  margin-bottom: 24px;
}

.login-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background: #e8eef7;
}

.login-tabs :deep(.el-tabs__item) {
  height: 44px;
  color: #75859b;
  font-weight: 500;
}

.login-tabs :deep(.el-tabs__item.is-active) {
  color: #356ee6;
  font-weight: 700;
}

.login-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 999px;
  background: #356ee6;
}

.login-card :deep(.el-form-item) {
  margin-bottom: 20px;
}

.login-card :deep(.el-input__wrapper) {
  min-height: 46px;
  border-radius: 12px;
  background: #f8faff;
  box-shadow: 0 0 0 1px #dfe7f2 inset;
  transition:
    background 180ms ease,
    box-shadow 180ms ease;
}

.login-card :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #b9c9df inset;
}

.login-card :deep(.el-input__wrapper.is-focus) {
  background: #fff;
  box-shadow:
    0 0 0 1px #4d7fe8 inset,
    0 0 0 3px rgba(77, 127, 232, 0.12);
}

.login-card :deep(.el-input__inner) {
  color: #25344b;
}

.login-card :deep(.el-input__inner::placeholder),
.login-card :deep(.el-input__icon) {
  color: #96a5ba;
}

.login-card :deep(.el-button--primary:not(.is-link)),
.login-card :deep(.el-button--success) {
  min-height: 46px;
  border-color: #3366ff;
  border-radius: 12px;
  background: #3366ff;
  font-weight: 700;
  letter-spacing: 0.16em;
  box-shadow: 0 5px 14px rgba(51, 102, 255, 0.14);
  transition:
    background 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease;
}

.login-card :deep(.el-button--primary:not(.is-link):hover),
.login-card :deep(.el-button--success:hover) {
  border-color: #2d62ce;
  background: #2d62ce;
  box-shadow: 0 7px 17px rgba(51, 102, 255, 0.18);
}

.login-footer {
  margin-top: 20px;
  text-align: center;
}

.login-footer :deep(.el-button) {
  color: #4776cf;
  font-weight: 500;
}

@media (max-width: 767px) {
  .login-container {
    align-items: flex-start;
    padding: max(48px, 8vh) 16px 32px;
  }

  .login-card {
    width: min(100%, 420px);
    padding: 32px 24px;
  }

  .login-title {
    font-size: 22px;
  }

  .floating-book {
    --book-width: 68px;
  }

  .book-field .book--near {
    --book-width: 86px;
  }

  .book-field .book--far {
    --book-width: 54px;
  }

  .book--2,
  .book--4,
  .book--7,
  .book--9,
  .book--12,
  .book--15,
  .book--17 {
    display: none;
  }
}

@media (min-width: 768px) and (max-width: 1100px) {
  .book--2,
  .book--8,
  .book--9,
  .book--11,
  .book--12,
  .book--16 {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .floating-book {
    animation: none;
    transform: rotate(var(--tilt));
    will-change: auto;
  }
}
</style>
