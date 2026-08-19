<template>
  <div class="ai-page">
    <el-row :gutter="24" class="ai-layout">
      <el-col :xs="24" :lg="16">
        <el-card shadow="never" class="chat-card">
          <template #header>
            <div class="panel-heading">
              <div>
                <h3>AI 智能助手</h3>
                <span>随时为你解答图书馆相关问题</span>
              </div>
              <div class="online-status"><i></i>在线</div>
            </div>
          </template>
          <div class="chat-box" ref="chatBox">
            <div v-if="messages.length === 0" class="msg assistant">
              <div class="msg-avatar">AI</div>
              <div class="msg-content">你好，我是智慧图书馆 AI 助手，可以帮你查询馆藏、推荐图书、解答借阅规则。请问有什么可以帮你？</div>
            </div>
            <div v-if="messages.length === 0" class="quick-questions" aria-label="快捷问题">
              <button v-for="question in quickQuestions" :key="question" class="quick-question" type="button" @click="fillQuickQuestion(question)">
                {{ question }}
              </button>
            </div>
            <div v-for="(msg, i) in messages" :key="i" :class="['msg', messageRole(msg)]">
              <div class="msg-avatar">{{ messageRole(msg) === 'assistant' ? 'AI' : '我' }}</div>
              <div
                v-if="messageRole(msg) === 'assistant'"
                class="msg-content ai-message-markdown"
                v-html="renderAssistantMessage(msg.content)"
              ></div>
              <div v-else class="msg-content">{{ msg.content }}</div>
            </div>
            <div v-if="loading" class="msg assistant">
              <div class="msg-avatar">AI</div>
              <div class="msg-content thinking"><i></i><i></i><i></i></div>
            </div>
          </div>
          <div class="context-status-bar" v-if="messages.length > 0">
            <div class="status-info">
              <span class="status-label">上下文进度</span>
              <span class="status-detail">{{ contextStatus.detail }}</span>
            </div>
            <div class="status-progress-wrap">
              <div class="status-progress" :style="{ width: contextStatus.percent + '%' }" :class="contextStatus.level"></div>
            </div>
            <span class="status-percent">{{ contextStatus.percent }}%</span>
          </div>
          <div class="chat-input">
            <el-input v-model="input" placeholder="输入您的问题..." @keyup.enter="sendMsg" />
            <el-button type="primary" @click="sendMsg" :loading="loading" :disabled="loading">
              <span aria-hidden="true">➤</span>发送
            </el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card shadow="never" class="recommend-card">
          <template #header>
            <div class="panel-heading">
              <div>
                <h3>AI 推荐图书</h3>
                <span>根据你的兴趣智能推荐</span>
              </div>
              <el-button type="primary" link :loading="recommendLoading" :disabled="recommendLoading" @click="getRecommend"><span aria-hidden="true">↻</span>刷新推荐</el-button>
            </div>
          </template>
          <div v-if="recommendations.length === 0" class="recommend-empty">
            点击刷新获取推荐
          </div>
          <div class="recommend-list">
            <div v-for="b in recommendations" :key="b.book_id"
                 class="recommend-item" @click="showBookDetail(b)">
              <div class="book-mark" aria-hidden="true">书</div>
              <div class="book-info">
                <div class="rec-title">{{ b.title }}</div>
                <div class="rec-author">{{ b.author }}</div>
                <div class="rec-reason">{{ b.reason }}</div>
              </div>
            </div>
          </div>
          <div v-if="summary" class="rec-summary">{{ summary }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图书详情弹窗 -->
    <el-dialog v-model="dialogVisible" :title="selectedBook?.title" width="450px" class="book-dialog">
      <el-descriptions v-if="selectedBook" :column="1" border>
        <el-descriptions-item label="书名">{{ selectedBook.title }}</el-descriptions-item>
        <el-descriptions-item label="作者">{{ selectedBook.author }}</el-descriptions-item>
        <el-descriptions-item label="库存">{{ selectedBook.stock ?? '--' }} 册</el-descriptions-item>
        <el-descriptions-item label="推荐理由">{{ selectedBook.reason || 'AI 推荐' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleBorrow" :loading="borrowing">
          立即借阅
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { aiApi, borrowApi } from '../../api/auth'
import { useUserStore } from '../../store/user'

const messages = ref([])
const userStore = useUserStore()
const input = ref('')
const loading = ref(false)
const recommendations = ref([])
const summary = ref('')
const chatBox = ref(null)
const recommendLoading = ref(false)
const quickQuestions = [
  '如何借阅一本图书？',
  '推荐几本数据结构复习书',
  '自习室预约规则是什么？',
]

// 详情弹窗
const dialogVisible = ref(false)
const selectedBook = ref(null)
const borrowing = ref(false)

const CONTEXT_MAX_MESSAGES = 50
const contextStatus = computed(() => {
  const count = messages.value.length
  const raw = Math.min(count / CONTEXT_MAX_MESSAGES, 1)
  const percent = Math.round(raw * 100)
  let level = 'low'
  if (raw >= 0.8) level = 'high'
  else if (raw >= 0.5) level = 'mid'

  const userTurns = messages.value.filter(m => m.role === 'user').length
  const tokenEstimate = messages.value.reduce((sum, m) => sum + (m.content?.length || 0), 0)

  let detail = `${count} 条消息 · ${userTurns} 轮对话`
  if (tokenEstimate > 2000) detail += ` · ~${Math.round(tokenEstimate / 1000)}k 字符`

  return { percent, level, detail }
})

onMounted(async () => {
  restoreChatHistory()
  await nextTick()
  scrollToLatestMessage()
  getRecommend()
})

async function sendMsg() {
  const content = input.value.trim()
  if (!content) return
  messages.value.push({ role: 'user', content })
  persistChatHistory()
  loading.value = true
  const msg = content; input.value = ''
  try {
    const r = await aiApi.chat(msg)
    messages.value.push({ role: 'assistant', content: r.data.reply })
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '抱歉，AI 服务暂时不可用。错误：' + (e.message || '未知') })
  } finally {
    loading.value = false
    persistChatHistory()
  }
  await nextTick()
  scrollToLatestMessage()
}

function getChatHistoryKey() {
  const user = userStore.user || {}
  const identity = user.user_id || user.id || user.username || user.real_name || 'current-user'
  return `smart-library:ai-chat-history:${user.role || 'user'}:${identity}`
}

function restoreChatHistory() {
  try {
    const stored = JSON.parse(localStorage.getItem(getChatHistoryKey()) || '[]')
    if (!Array.isArray(stored)) return
    messages.value = stored
      .filter(message => (
        ['user', 'assistant'].includes(message?.role)
        && typeof message.content === 'string'
        && message.content.trim()
      ))
      .slice(-100)
      .map(message => ({ role: message.role, content: message.content }))
  } catch (e) {
    messages.value = []
  }
}

function persistChatHistory() {
  try {
    localStorage.setItem(getChatHistoryKey(), JSON.stringify(messages.value.slice(-100)))
  } catch (e) {
    // Local storage can be unavailable or full; chat remains usable for the current visit.
  }
}

function scrollToLatestMessage() {
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}

function messageRole(message) {
  return message?.role === 'user' ? 'user' : 'assistant'
}

function fillQuickQuestion(question) {
  input.value = question
}

function renderAssistantMessage(content) {
  const lines = String(content ?? '').replace(/\r\n?/g, '\n').split('\n')
  const blocks = []
  let index = 0

  while (index < lines.length) {
    const line = lines[index]

    if (!line.trim()) {
      index += 1
      continue
    }

    if (/^```/.test(line.trim())) {
      const codeLines = []
      index += 1
      while (index < lines.length && !/^```/.test(lines[index].trim())) {
        codeLines.push(lines[index])
        index += 1
      }
      if (index < lines.length) index += 1
      blocks.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`)
      continue
    }

    if (/^\s{0,3}([-*_])(?:\s*\1){2,}\s*$/.test(line)) {
      blocks.push('<hr>')
      index += 1
      continue
    }

    const heading = line.match(/^\s*#{1,4}\s+(.+)$/)
    if (heading) {
      const level = Math.min(4, Math.max(3, line.trim().match(/^#+/)[0].length))
      blocks.push(`<h${level}>${renderInline(heading[1])}</h${level}>`)
      index += 1
      continue
    }

    const unordered = line.match(/^\s*[-*+]\s+(.+)$/)
    const ordered = line.match(/^\s*\d+\.\s+(.+)$/)
    if (unordered || ordered) {
      const isOrdered = Boolean(ordered)
      const items = []
      const itemPattern = isOrdered ? /^\s*\d+\.\s+(.+)$/ : /^\s*[-*+]\s+(.+)$/
      while (index < lines.length) {
        const item = lines[index].match(itemPattern)
        if (!item) break
        items.push(`<li>${renderInline(item[1])}</li>`)
        index += 1
      }
      blocks.push(`<${isOrdered ? 'ol' : 'ul'}>${items.join('')}</${isOrdered ? 'ol' : 'ul'}>`)
      continue
    }

    const paragraph = []
    while (index < lines.length && lines[index].trim()) {
      if (/^(\s*#{1,4}\s+|\s*[-*+]\s+|\s*\d+\.\s+|\s*```|\s{0,3}([-*_])(?:\s*\2){2,}\s*$)/.test(lines[index])) break
      paragraph.push(lines[index])
      index += 1
    }
    if (paragraph.length) blocks.push(`<p>${paragraph.map(renderInline).join('<br>')}</p>`)
    else index += 1
  }

  return blocks.join('')
}

function renderInline(value) {
  const codeTokens = []
  let text = escapeHtml(value).replace(/`([^`]+)`/g, (_, code) => {
    const token = `@@CODE_${codeTokens.length}@@`
    codeTokens.push(`<code>${code}</code>`)
    return token
  })
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  return text.replace(/@@CODE_(\d+)@@/g, (_, tokenIndex) => codeTokens[Number(tokenIndex)] || '')
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

async function getRecommend() {
  recommendLoading.value = true
  try {
    const r = await aiApi.recommend()
    recommendations.value = r.data.recommendations || []
    summary.value = r.data.summary || ''
  } catch (e) {
    ElMessage.error('刷新推荐失败，请稍后重试')
  } finally {
    recommendLoading.value = false
  }
}

function showBookDetail(book) {
  selectedBook.value = book
  dialogVisible.value = true
}

async function handleBorrow() {
  if (!selectedBook.value) return
  borrowing.value = true
  try {
    await borrowApi.apply(selectedBook.value.book_id)
    ElMessage.success(`《${selectedBook.value.title}》借阅申请已提交，等待管理员审核`)
    dialogVisible.value = false
  } catch (e) {
    // handled by interceptor
  } finally {
    borrowing.value = false
  }
}
</script>

<style scoped>
.ai-page {
  min-height: 100%;
}

.ai-layout {
  align-items: stretch;
}

.ai-layout > :deep(.el-col) {
  display: flex;
}

.ai-page :deep(.chat-card),
.ai-page :deep(.recommend-card) {
  width: 100%;
  height: 680px;
  overflow: hidden;
  border-color: var(--border-color);
  border-radius: 16px;
  box-shadow: var(--library-card-shadow);
}

.ai-page :deep(.chat-card .el-card__header),
.ai-page :deep(.recommend-card .el-card__header) {
  min-height: 72px;
  padding: 17px 24px;
  border-bottom-color: var(--border-color);
}

.panel-heading {
  display: flex;
  height: 100%;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.panel-heading h3 {
  margin: 0;
  color: var(--text-main);
  font-size: 17px;
  font-weight: 700;
}

.panel-heading > div > span {
  display: block;
  margin-top: 5px;
  color: var(--text-muted);
  font-size: 12px;
}

.online-status {
  display: inline-flex;
  height: 32px;
  padding: 0 13px;
  align-items: center;
  gap: 7px;
  color: var(--brand-blue);
  background: #edf3ff;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
}

.online-status i {
  width: 7px;
  height: 7px;
  background: #22c58b;
  border-radius: 50%;
  box-shadow: 0 0 0 3px rgba(34, 197, 139, 0.12);
}

.ai-page :deep(.chat-card .el-card__body) {
  display: flex;
  height: calc(100% - 72px);
  padding: 0;
  box-sizing: border-box;
  flex-direction: column;
}

.chat-box {
  flex: 1;
  min-height: 0;
  padding: 26px;
  overflow-y: auto;
  scrollbar-color: #d7deea transparent;
  scrollbar-width: thin;
}

.msg {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-start;
  gap: 12px;
}

.msg.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  display: grid;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  place-items: center;
  color: var(--brand-blue);
  background: #edf3ff;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 700;
}

.msg.user .msg-avatar {
  color: #fff;
  background: var(--brand-blue);
}

.msg-content {
  max-width: 72%;
  padding: 13px 16px;
  border: 1px solid #e3e9f0;
  color: #344054;
  background: #f3f6fa;
  border-radius: 6px 16px 16px 16px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.msg.user .msg-content {
  border-color: var(--brand-blue);
  color: #fff;
  background: var(--brand-blue);
  border-radius: 16px 6px 16px 16px;
}

.ai-message-markdown :deep(p) {
  margin: 0 0 10px;
}

.ai-message-markdown :deep(p:last-child) {
  margin-bottom: 0;
}

.ai-message-markdown :deep(h3),
.ai-message-markdown :deep(h4) {
  margin: 2px 0 10px;
  color: #24334d;
  font-weight: 700;
  line-height: 1.45;
}

.ai-message-markdown :deep(h3) {
  font-size: 15px;
}

.ai-message-markdown :deep(h4) {
  font-size: 14px;
}

.ai-message-markdown :deep(strong) {
  color: #263954;
  font-weight: 700;
}

.ai-message-markdown :deep(ul),
.ai-message-markdown :deep(ol) {
  padding-left: 20px;
  margin: 8px 0 12px;
}

.ai-message-markdown :deep(li + li) {
  margin-top: 4px;
}

.ai-message-markdown :deep(hr) {
  height: 1px;
  margin: 13px 0;
  border: 0;
  background: #dce4ee;
}

.ai-message-markdown :deep(code) {
  padding: 1px 5px;
  border-radius: 4px;
  color: #435a7a;
  background: #e8eef6;
  font-family: "Cascadia Code", Consolas, monospace;
  font-size: 0.92em;
}

.ai-message-markdown :deep(pre) {
  margin: 10px 0;
  padding: 10px 12px;
  overflow-x: auto;
  border: 1px solid #dfe7f0;
  border-radius: 8px;
  background: #edf2f7;
  line-height: 1.55;
}

.ai-message-markdown :deep(pre code) {
  padding: 0;
  color: #40516a;
  background: transparent;
  font-size: 12px;
}

.quick-questions {
  display: flex;
  margin: -4px 0 22px 48px;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-question {
  max-width: 100%;
  padding: 7px 10px;
  border: 1px solid #dbe5f5;
  border-radius: 999px;
  color: #526b92;
  background: #f8fbff;
  cursor: pointer;
  font-size: 12px;
  line-height: 1.35;
  transition: border-color 160ms ease, background-color 160ms ease, color 160ms ease;
}

.quick-question:hover,
.quick-question:focus-visible {
  border-color: #b7caf0;
  color: var(--brand-blue);
  background: #f0f5ff;
  outline: none;
}

.thinking {
  display: flex;
  min-width: 54px;
  align-items: center;
  gap: 5px;
}

.thinking i {
  width: 6px;
  height: 6px;
  background: #9aa6b8;
  border-radius: 50%;
  animation: thinking 1.2s infinite ease-in-out;
}

.thinking i:nth-child(2) { animation-delay: 0.15s; }
.thinking i:nth-child(3) { animation-delay: 0.3s; }

@keyframes thinking {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.45; }
  30% { transform: translateY(-3px); opacity: 1; }
}

.chat-input {
  display: flex;
  padding: 18px 22px;
  gap: 12px;
  background: #fff;
  border-top: 1px solid var(--border-color);
}

/* ---- 上下文进度状态栏 ---- */
.context-status-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 24px;
  background: #fafbfd;
  border-top: 1px solid #edf1f7;
  font-size: 12px;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  min-width: 0;
}

.status-label {
  color: #6b7d99;
  font-weight: 600;
  white-space: nowrap;
}

.status-detail {
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-progress-wrap {
  flex: 1;
  height: 4px;
  background: #e5eaf2;
  border-radius: 999px;
  overflow: hidden;
  min-width: 40px;
}

.status-progress {
  height: 100%;
  border-radius: 999px;
  transition: width 0.45s ease;
}

.status-progress.low {
  background: linear-gradient(90deg, #22c58b, #3dd68c);
}

.status-progress.mid {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.status-progress.high {
  background: linear-gradient(90deg, #f97316, #ef4444);
}

.status-percent {
  flex-shrink: 0;
  width: 36px;
  text-align: right;
  color: #6b7d99;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 640px) {
  .context-status-bar {
    padding: 8px 14px;
    gap: 7px;
  }

  .status-detail {
    display: none;
  }
}
/* ---- 状态栏结束 ---- */

.chat-input :deep(.el-input) {
  flex: 1;
}

.chat-input :deep(.el-input__wrapper) {
  height: 46px;
  padding-inline: 16px;
  border-radius: 12px;
  box-shadow: 0 0 0 1px var(--border-color) inset;
}

.chat-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--brand-blue) inset;
}

.chat-input :deep(.el-button) {
  height: 46px;
  padding: 0 22px;
  gap: 7px;
  border-radius: 12px;
  font-weight: 600;
}

.recommend-item {
  display: flex;
  padding: 16px;
  gap: 13px;
  background: #fff;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.ai-page :deep(.recommend-card .el-card__body) {
  height: calc(100% - 72px);
  padding: 20px;
  box-sizing: border-box;
  overflow-y: auto;
}

.panel-heading :deep(.el-button) {
  padding: 8px 0;
  font-weight: 600;
}

.panel-heading :deep(.el-button span) {
  display: inline-flex;
  margin: 0;
  align-items: center;
  gap: 5px;
  color: var(--brand-blue);
  font-size: 13px;
}

.recommend-list {
  display: grid;
  gap: 14px;
}

.recommend-item:hover {
  transform: translateY(-1px);
  border-color: #b9cdf8;
  box-shadow: 0 8px 20px rgba(47, 111, 237, 0.08);
}

.book-mark {
  display: grid;
  width: 38px;
  height: 46px;
  flex: 0 0 38px;
  place-items: center;
  color: var(--brand-blue);
  background: #edf3ff;
  border-radius: 7px 7px 9px 9px;
  font-size: 12px;
  font-weight: 700;
}

.book-info {
  min-width: 0;
}

.rec-title {
  overflow: hidden;
  color: var(--text-main);
  font-size: 14px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rec-author {
  margin: 5px 0 8px;
  color: var(--text-muted);
  font-size: 12px;
}

.rec-reason {
  display: -webkit-box;
  overflow: hidden;
  color: #758398;
  font-size: 12px;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.recommend-empty {
  padding: 70px 20px;
  color: #98a4b5;
  text-align: center;
  background: #fafbfd;
  border: 1px dashed #d9e0ea;
  border-radius: 12px;
}

.rec-summary {
  padding: 13px 14px;
  margin-top: 16px;
  color: #39745e;
  background: #effaf5;
  border: 1px solid #d4f0e4;
  border-radius: 10px;
  font-size: 12px;
  line-height: 1.6;
}

:deep(.book-dialog) {
  border-radius: 16px;
}

:deep(.book-dialog .el-dialog__header) {
  padding-bottom: 18px;
  border-bottom: 1px solid #e1e7ef;
}

@media (max-width: 1199px) {
  .ai-layout {
    row-gap: 24px;
  }

  .ai-page :deep(.chat-card),
  .ai-page :deep(.recommend-card) {
    height: 620px;
  }
}

@media (max-width: 640px) {
  .ai-page :deep(.chat-card),
  .ai-page :deep(.recommend-card) {
    height: 580px;
    border-radius: 12px;
  }

  .ai-page :deep(.chat-card .el-card__header),
  .ai-page :deep(.recommend-card .el-card__header) {
    padding-inline: 16px;
  }

  .chat-box {
    padding: 18px 14px;
  }

  .msg-content {
    max-width: 82%;
  }

  .chat-input {
    padding: 14px;
  }

  .chat-input :deep(.el-button) {
    padding-inline: 16px;
  }

  .panel-heading > div > span {
    display: none;
  }
}
</style>
