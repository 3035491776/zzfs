<template>
  <div class="register-container">
    <div class="library-atmosphere" aria-hidden="true">
      <div class="book-field">
        <article class="floating-book book--1 book--near">
          <span class="book-category">计算机科学</span>
          <strong>算法导论</strong>
          <span class="book-author">Thomas H. Cormen</span>
        </article>
        <article class="floating-book book--2 book--far">
          <span class="book-category">计算机科学</span>
          <strong>人工智能：一种现代方法</strong>
          <span class="book-author">Stuart Russell</span>
        </article>
        <article class="floating-book book--3 book--mid">
          <span class="book-category">计算机科学</span>
          <strong>计算机网络</strong>
          <span class="book-author">Andrew S. Tanenbaum</span>
        </article>
        <article class="floating-book book--4 book--far">
          <span class="book-category">历史</span>
          <strong>枪炮、病菌与钢铁</strong>
          <span class="book-author">贾雷德·戴蒙德</span>
        </article>
        <article class="floating-book book--5 book--mid">
          <span class="book-category">经济</span>
          <strong>原则</strong>
          <span class="book-author">瑞·达利欧</span>
        </article>
        <article class="floating-book book--6 book--near">
          <span class="book-category">文学</span>
          <strong>红楼梦</strong>
          <span class="book-author">曹雪芹</span>
        </article>
        <article class="floating-book book--7 book--mid">
          <span class="book-category">文学</span>
          <strong>活着</strong>
          <span class="book-author">余华</span>
        </article>
        <article class="floating-book book--8 book--mid">
          <span class="book-category">文学</span>
          <strong>百年孤独</strong>
          <span class="book-author">加西亚·马尔克斯</span>
        </article>
        <article class="floating-book book--9 book--far">
          <span class="book-category">哲学</span>
          <strong>苏菲的世界</strong>
          <span class="book-author">乔斯坦·贾德</span>
        </article>
        <article class="floating-book book--10 book--near">
          <span class="book-category">文学</span>
          <strong>三体</strong>
          <span class="book-author">刘慈欣</span>
        </article>
        <article class="floating-book book--11 book--mid">
          <span class="book-category">历史</span>
          <strong>史记</strong>
          <span class="book-author">司马迁</span>
        </article>
        <article class="floating-book book--12 book--far">
          <span class="book-category">历史</span>
          <strong>万历十五年</strong>
          <span class="book-author">黄仁宇</span>
        </article>
        <article class="floating-book book--13 book--mid">
          <span class="book-category">历史</span>
          <strong>人类简史</strong>
          <span class="book-author">尤瓦尔·赫拉利</span>
        </article>
        <article class="floating-book book--14 book--near">
          <span class="book-category">经济</span>
          <strong>国富论</strong>
          <span class="book-author">亚当·斯密</span>
        </article>
        <article class="floating-book book--15 book--far">
          <span class="book-category">经济</span>
          <strong>经济学原理</strong>
          <span class="book-author">曼昆</span>
        </article>
        <article class="floating-book book--16 book--mid">
          <span class="book-category">哲学</span>
          <strong>理想国</strong>
          <span class="book-author">柏拉图</span>
        </article>
        <article class="floating-book book--17 book--far">
          <span class="book-category">自然科学</span>
          <strong>时间简史</strong>
          <span class="book-author">斯蒂芬·霍金</span>
        </article>
        <article class="floating-book book--18 book--mid">
          <span class="book-category">自然科学</span>
          <strong>自私的基因</strong>
          <span class="book-author">理查德·道金斯</span>
        </article>
      </div>
      <div class="background-veil"></div>
    </div>

    <div class="register-card">
      <h1 class="register-title">智慧图书馆管理系统</h1>
      <p class="register-welcome">创建账号，开启您的智慧阅读之旅</p>
      <p class="register-subtitle">Smart Library Management System</p>
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
          <el-radio-group v-model="form.role" class="role-selector">
            <el-radio value="student">学生</el-radio>
            <el-radio value="teacher">教师</el-radio>
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
:global(html:has(.register-container)),
:global(body:has(.register-container)),
:global(#app:has(.register-container)) {
  width: 100%;
  min-width: 0;
  overflow-x: hidden;
}

.register-container {
  position: relative;
  box-sizing: border-box;
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 20px;
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

.register-card {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  width: 460px;
  padding: 32px 40px;
  border: 1px solid rgba(211, 222, 239, 0.88);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow:
    0 24px 60px rgba(76, 101, 144, 0.12),
    0 6px 18px rgba(76, 101, 144, 0.06);
  backdrop-filter: blur(18px);
}

.register-title {
  margin: 0;
  color: #1f2d42;
  font-family: "Noto Serif SC", "Songti SC", "SimSun", serif;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-align: center;
}

.register-welcome {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 14px;
  line-height: 1.5;
  text-align: center;
}

.register-subtitle {
  margin: 5px 0 24px;
  color: #7b8ba3;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-align: center;
}

.register-card :deep(.el-form-item) {
  margin-bottom: 16px;
}

.register-card :deep(.el-input__wrapper) {
  min-height: 44px;
  border-radius: 12px;
  background: #f8faff;
  box-shadow: 0 0 0 1px #dfe7f2 inset;
  transition:
    background 180ms ease,
    box-shadow 180ms ease;
}

.register-card :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #b9c9df inset;
}

.register-card :deep(.el-input__wrapper.is-focus) {
  background: #fff;
  box-shadow:
    0 0 0 1px #4d7fe8 inset,
    0 0 0 3px rgba(77, 127, 232, 0.12);
}

.register-card :deep(.el-input__inner) {
  color: #25344b;
}

.register-card :deep(.el-input__inner::placeholder),
.register-card :deep(.el-input__icon) {
  color: #96a5ba;
}

.role-selector {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.role-selector :deep(.el-radio) {
  box-sizing: border-box;
  width: 100%;
  height: 42px;
  margin: 0;
  padding: 0 16px;
  border: 1px solid #dfe7f2;
  border-radius: 12px;
  background: #f8faff;
  color: #64748b;
  transition:
    border-color 180ms ease,
    background 180ms ease,
    box-shadow 180ms ease;
}

.role-selector :deep(.el-radio:hover) {
  border-color: #b9c9df;
}

.role-selector :deep(.el-radio.is-checked) {
  border-color: #7d9ef5;
  background: #f2f6ff;
  box-shadow: 0 0 0 3px rgba(51, 102, 255, 0.08);
}

.role-selector :deep(.el-radio__input.is-checked .el-radio__inner) {
  border-color: #3366ff;
  background: #3366ff;
}

.role-selector :deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #2857c8;
  font-weight: 600;
}

.register-card :deep(.el-button--primary:not(.is-link)) {
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

.register-card :deep(.el-button--primary:not(.is-link):hover) {
  border-color: #2d62ce;
  background: #2d62ce;
  box-shadow: 0 7px 17px rgba(51, 102, 255, 0.18);
}

.register-footer {
  margin-top: 18px;
  text-align: center;
}

.register-footer :deep(.el-button) {
  color: #4776cf;
  font-weight: 500;
}

@media (max-width: 767px) {
  .register-container {
    align-items: flex-start;
    padding: 24px 16px;
    overflow-y: auto;
  }

  .register-card {
    width: min(100%, 460px);
    padding: 28px 24px;
  }

  .register-title {
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
