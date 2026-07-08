<template>
  <main class="landing-page">
    <div class="landing-backdrop" aria-hidden="true">
      <template v-if="videoReady && !videoFailed">
        <video
          ref="videoARef"
          class="landing-video is-active"
          :src="videoUrl"
          muted
          autoplay
          loop
          playsinline
          preload="auto"
          @timeupdate="handleTimeUpdate"
          @ended="switchVideo"
          @error="handleVideoError"
        />
        <video
          ref="videoBRef"
          class="landing-video"
          :src="videoUrl"
          muted
          autoplay
          loop
          playsinline
          preload="auto"
          @timeupdate="handleTimeUpdate"
          @ended="switchVideo"
          @error="handleVideoError"
        />
      </template>
      <div class="landing-fallback" :class="{ 'is-visible': !videoReady || videoFailed }"></div>
      <div class="landing-wash"></div>
    </div>

    <section class="landing-shell">
      <header class="landing-nav" aria-label="首页导航">
        <RouterLink class="landing-mark" to="/" aria-label="智慧图书馆首页">
          <span></span>
        </RouterLink>

        <nav class="landing-links" aria-label="服务导航">
          <span v-for="item in navItems" :key="item">{{ item }}</span>
        </nav>

        <div class="landing-actions">
          <RouterLink class="landing-action" to="/login">登录</RouterLink>
          <RouterLink class="landing-action is-solid" to="/register">注册</RouterLink>
        </div>
      </header>

      <div id="landing-stats" class="landing-stats" aria-label="图书馆数据">
        <article
          v-for="(stat, index) in stats"
          :key="stat.label"
          class="stat-card"
          :style="{ '--delay': `${0.18 + index * 0.12}s` }"
        >
          <strong><span>+</span>{{ stat.value }}</strong>
          <small>{{ stat.label }}</small>
        </article>
      </div>

      <div class="landing-bottom">
        <p class="landing-kicker">
          智慧图书馆管理系统
          <span>让借阅、预约与阅读服务更轻盈地连接起来</span>
        </p>

        <RouterLink class="landing-cta" to="/login" aria-label="进入系统并立即登录">
          <span>进入系统</span>
          <strong>立即登录</strong>
          <i aria-hidden="true">↗</i>
        </RouterLink>

        <h1 class="landing-title" aria-label="Smart Library System">
          <span
            v-for="(word, index) in titleWords"
            :key="word"
            :style="{ '--delay': `${0.32 + index * 0.14}s` }"
          >
            <em>{{ word }}</em>
          </span>
        </h1>
      </div>
    </section>
  </main>
</template>

<script setup>
import { nextTick, onMounted, ref } from 'vue'

const videoUrl = '/videos/landing-hero.mp4'

const navItems = ['馆藏资源', '空间预约', '智能助手', '通知服务']
const titleWords = ['SMART', 'LIBRARY', 'SYSTEM']
const stats = [
  { value: '120K', label: '数字馆藏' },
  { value: '36', label: '知识分类' },
  { value: '8K', label: '服务人次' },
]

const videoARef = ref(null)
const videoBRef = ref(null)
const activeVideo = ref('a')
const videoReady = ref(false)
const videoFailed = ref(false)

function getVideoPair() {
  return {
    a: videoARef.value,
    b: videoBRef.value,
  }
}

function switchVideo() {
  if (videoFailed.value) return

  const videos = getVideoPair()
  const nextKey = activeVideo.value === 'a' ? 'b' : 'a'
  const incoming = videos[nextKey]
  const outgoing = videos[activeVideo.value]

  if (!incoming || !outgoing) return

  incoming.currentTime = 0
  incoming.play().catch(handleVideoError)
  incoming.classList.add('is-active')
  outgoing.classList.remove('is-active')
  activeVideo.value = nextKey
}

function handleTimeUpdate(event) {
  const current = event.target
  if (!current?.duration || current !== getVideoPair()[activeVideo.value]) return

  if (current.currentTime >= current.duration - 0.16) {
    switchVideo()
  }
}

function handleVideoError() {
  videoFailed.value = true
}

onMounted(() => {
  fetch(videoUrl, { method: 'HEAD', mode: 'no-cors', cache: 'force-cache' })
    .then(async () => {
      videoReady.value = true
      await nextTick()
      videoARef.value?.play().catch(handleVideoError)
    })
    .catch(handleVideoError)
})
</script>

<style scoped>
:global(html:has(.landing-page)),
:global(body:has(.landing-page)),
:global(#app:has(.landing-page)) {
  width: 100%;
  min-width: 0;
  min-height: 100%;
  overflow-x: hidden;
}

.landing-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #f7f8f4;
  color: #050505;
  font-family: "Arial Narrow", "Helvetica Neue", "Microsoft YaHei", sans-serif;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.landing-backdrop,
.landing-video,
.landing-fallback,
.landing-wash {
  position: absolute;
  inset: 0;
}

.landing-backdrop {
  z-index: 0;
  overflow: hidden;
  background:
    radial-gradient(circle at 28% 42%, rgba(118, 96, 255, 0.28), transparent 26%),
    radial-gradient(circle at 52% 34%, rgba(98, 211, 235, 0.18), transparent 22%),
    linear-gradient(115deg, #ffffff 0%, #f4f7f3 48%, #eef2f9 100%);
}

.landing-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.18s ease;
  filter: brightness(0.94) saturate(1.12) contrast(1.1);
}

.landing-video.is-active {
  opacity: 1;
}

.landing-fallback {
  opacity: 0;
  transition: opacity 0.3s ease;
  background:
    radial-gradient(ellipse 38% 44% at 30% 42%, rgba(104, 75, 219, 0.22), transparent 60%),
    radial-gradient(ellipse 26% 30% at 37% 50%, rgba(76, 197, 234, 0.18), transparent 58%),
    conic-gradient(from 130deg at 35% 48%, transparent 0deg, rgba(85, 47, 213, 0.28) 58deg, transparent 108deg, rgba(32, 175, 220, 0.16) 166deg, transparent 238deg, rgba(240, 82, 129, 0.14) 290deg, transparent 360deg),
    linear-gradient(118deg, #ffffff 0%, #f7f7f1 52%, #edf2fb 100%);
}

.landing-fallback.is-visible {
  opacity: 1;
}

.landing-wash {
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.02) 0%, rgba(255, 255, 255, 0.08) 38%, rgba(255, 255, 255, 0.45) 68%, rgba(255, 255, 255, 0.78) 100%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.02) 48%, rgba(255, 255, 255, 0.18));
}

.landing-shell {
  position: relative;
  z-index: 1;
  display: flex;
  min-height: 100vh;
  flex-direction: column;
  padding: clamp(20px, 2.7vw, 42px);
}

.landing-nav {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 28px;
  animation: fade-down 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.landing-mark {
  display: inline-flex;
  width: 38px;
  height: 38px;
  align-items: center;
  justify-content: center;
  border: 3px solid #5e0ed7;
  border-radius: 50%;
  box-shadow: 0 16px 40px rgba(94, 14, 215, 0.16);
}

.landing-mark span {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: #5e0ed7;
}

.landing-links {
  display: flex;
  justify-content: center;
  gap: clamp(18px, 3.6vw, 58px);
  color: rgba(0, 0, 0, 0.78);
  font-size: clamp(12px, 1.1vw, 16px);
  font-weight: 800;
  letter-spacing: 0.16em;
}

.landing-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.landing-action {
  display: inline-flex;
  min-height: 38px;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(0, 0, 0, 0.14);
  border-radius: 999px;
  padding: 0 18px;
  color: #080808;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-decoration: none;
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.landing-action:hover,
.landing-action:focus-visible {
  border-color: rgba(94, 14, 215, 0.55);
  transform: translateY(-1px);
}

.landing-action.is-solid {
  border-color: #050505;
  background: #050505;
  color: #fff;
}

.landing-stats {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: flex-end;
  gap: clamp(22px, 3.2vw, 54px);
  padding: 24px 0 12px;
}

.stat-card {
  text-align: right;
  animation: fade-up 0.72s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: var(--delay);
}

.stat-card strong {
  display: block;
  color: #020202;
  font-size: clamp(2rem, 5.2vw, 4.6rem);
  font-weight: 900;
  letter-spacing: 0.1em;
  line-height: 0.92;
}

.stat-card strong span {
  color: #5e0ed7;
  font-size: 0.48em;
  vertical-align: 0.2em;
}

.stat-card small {
  display: block;
  margin-top: 10px;
  color: rgba(0, 0, 0, 0.82);
  font-size: clamp(11px, 1.05vw, 15px);
  font-weight: 850;
  letter-spacing: 0.18em;
}

.landing-bottom {
  display: grid;
  grid-template-columns: minmax(150px, 320px) auto minmax(340px, 1fr);
  align-items: end;
  gap: clamp(16px, 3vw, 48px);
}

.landing-kicker {
  margin: 0 0 8px;
  max-width: 300px;
  color: #050505;
  font-size: clamp(11px, 1vw, 15px);
  font-weight: 850;
  line-height: 1.58;
  animation: fade-up 0.72s cubic-bezier(0.22, 1, 0.36, 1) 0.7s both;
}

.landing-kicker span {
  display: block;
  margin-top: 12px;
  color: rgba(0, 0, 0, 0.58);
  font-size: 0.86em;
  letter-spacing: 0.04em;
  text-transform: none;
}

.landing-cta {
  display: inline-grid;
  grid-template-columns: auto auto;
  align-items: end;
  gap: 2px 10px;
  justify-self: center;
  margin-bottom: 8px;
  color: #5e0ed7;
  font-weight: 900;
  letter-spacing: 0.14em;
  text-decoration: none;
  animation: fade-up 0.72s cubic-bezier(0.22, 1, 0.36, 1) 0.82s both;
  transition: transform 0.2s ease, color 0.2s ease;
}

.landing-cta span {
  grid-column: 1 / -1;
  color: rgba(0, 0, 0, 0.52);
  font-size: 11px;
  letter-spacing: 0.22em;
}

.landing-cta strong {
  font-size: clamp(17px, 2.2vw, 30px);
}

.landing-cta i {
  font-size: clamp(17px, 2vw, 26px);
  font-style: normal;
  line-height: 1;
}

.landing-cta:hover,
.landing-cta:focus-visible {
  color: #38059d;
  transform: translateY(-2px);
}

.landing-title {
  margin: 0;
  text-align: right;
}

.landing-title span {
  display: block;
  overflow: hidden;
}

.landing-title em {
  display: block;
  color: #020202;
  font-size: clamp(3.3rem, 9.6vw, 10rem);
  font-style: normal;
  font-weight: 950;
  letter-spacing: 0;
  line-height: 0.86;
  animation: title-reveal 0.76s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: var(--delay);
}

@keyframes fade-down {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(34px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes title-reveal {
  from {
    transform: translateY(112%);
  }

  to {
    transform: translateY(0);
  }
}

@media (max-width: 980px) {
  .landing-shell {
    padding: 20px;
  }

  .landing-nav {
    grid-template-columns: auto auto;
  }

  .landing-links {
    grid-column: 1 / -1;
    grid-row: 2;
    justify-content: flex-start;
    gap: 18px;
    overflow-x: auto;
    padding: 6px 0;
    white-space: nowrap;
  }

  .landing-stats {
    align-items: flex-start;
    justify-content: flex-end;
    padding-top: 12vh;
  }

  .landing-bottom {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .landing-kicker,
  .landing-cta {
    justify-self: start;
  }

  .landing-title {
    text-align: left;
  }

  .landing-title em {
    font-size: clamp(3.2rem, 18vw, 7rem);
  }
}

@media (max-width: 640px) {
  .landing-actions {
    gap: 8px;
  }

  .landing-action {
    min-height: 34px;
    padding: 0 12px;
    font-size: 12px;
  }

  .landing-links {
    font-size: 11px;
  }

  .landing-stats {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
  }

  .stat-card strong {
    font-size: clamp(1.55rem, 10vw, 2.7rem);
  }

  .stat-card small {
    font-size: 10px;
    letter-spacing: 0.08em;
  }
}

@media (prefers-reduced-motion: reduce) {
  .landing-video,
  .landing-nav,
  .stat-card,
  .landing-kicker,
  .landing-cta,
  .landing-title em {
    animation: none;
    transition: none;
  }
}
</style>
