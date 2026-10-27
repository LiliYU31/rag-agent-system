<template>
  <div class="app">
    <!-- 左侧固定栏：小助手对话 -->
    <aside class="sidebar">

      <!-- 左侧边栏顶部 -->
      <div class="sidebar-header" style="display: flex; justify-content: space-between; padding: 12px;">
        <el-button icon="Menu" circle @click="drawerVisible = true" />
        <el-button icon="Plus" circle @click="startNewChat" title="新对话" />
      </div>

      <!-- 历史记录抽屉 -->
      <el-drawer v-model="drawerVisible" title="历史记录" direction="ltr" size="260px">
        <div class="history-list">
          <div
              v-for="date in historyList"
              :key="date"
              class="history-item"
              :class="{ active: currentSessionId === date }"
              @click="loadHistoryChat(date)"
          >
            📅 {{ date }}
          </div>
        </div>
      </el-drawer>

      <!-- 聊天消息区（滚动区域） -->
      <div class="chat-history" ref="chatHistoryRef">
        <!-- 空状态提示（无消息时显示） -->
        <div v-if="chatHistory.length === 0" class="empty-state">
          <div class="empty-icon">🤖</div>
          <div class="empty-title">你好，我是日历日程小助手</div>
          <div class="empty-tip">可以问我：帮我添加日程、今天有什么安排，或分析某月的计划与学习安排...</div>
        </div>

        <!-- 消息列表 -->
        <div
            v-for="(msg, i) in chatHistory"
            :key="i"
            class="chat-msg"
            :class="msg.role"
        >
          <div class="msg-bubble">
            <!-- 思考过程（可折叠） -->
            <div v-if="msg.role === 'ai' && msg.thinking && msg.showThinking" class="thinking-box">
              <div class="thinking-label">🤔 思考中...</div>
              <div class="thinking-content">{{ msg.thinking }}</div>
            </div>
            <!-- 正式回答 -->
            <div v-if="msg.content">{{ msg.content }}</div>
            <div v-if="msg.role === 'ai' && !msg.content && !msg.thinking">思考中...</div>
          </div>
        </div>
      </div>

      <!-- 底部输入区（固定） -->
      <div class="chat-input-area">
        <div class="input-wrapper">
          <!-- 文本输入区（自动高度） -->
          <textarea
              ref="inputRef"
              v-model="chatInput"
              placeholder="发消息..."
              class="chat-textarea"
              rows="1"
              @input="autoResize"
              @keydown.enter.exact.prevent="sendChat"
              :disabled="loading"
          ></textarea>

          <!-- 底部工具栏 -->
          <div class="input-toolbar">
            <div class="toolbar-right">
              <button
                  class="send-btn"
                  :disabled="!chatInput.trim() || loading"
                  @click="sendChat"
              >➤</button>
            </div>
          </div>
        </div>

      </div>
    </aside>

    <!-- 右侧主区域 -->
    <div class="main-area">
      <!-- 顶部导航 -->
      <header class="top-nav">
        <nav class="nav-items">
          <router-link
              v-for="item in navItems"
              :key="item.path"
              :to="item.path"
              class="nav-item"
              :class="{ active: $route.path === item.path }"
          >
            {{ item.name }}
          </router-link>
        </nav>
        <div class="user-avatar"></div>
      </header>

      <!-- 页面内容 -->
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onMounted } from 'vue'
import { chatStream } from './api/chat'
import request from './api/request'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const drawerVisible = ref(false)
const historyList = ref([])

const navItems = [
  { name: '日历', path: '/calendar' },
  { name: '日程', path: '/schedule' },
  { name: '日报', path: '/report' },
  { name: '进度', path: '/progress' },
]

const chatHistory = ref([])
const chatInput = ref('')
const loading = ref(false)
const chatHistoryRef = ref(null)
const inputRef = ref(null)

// 获取今天日期 YYYY-MM-DD
// 6点切分逻辑
const getTodayStr = () => {
  const d = new Date()
  d.setHours(d.getHours() - 6) // 核心：往前推6小时
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const currentSessionId = ref(localStorage.getItem('current_session_id') || getTodayStr())

// 自动滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatHistoryRef.value) {
    chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
  }
}

// 监听消息变化，自动滚动
watch(chatHistory, scrollToBottom, { deep: true })

// 只有一个 onMounted
onMounted(async () => {
  // 1. 计算今天属于哪个“业务日”
  const today = getTodayStr()

  // 如果你希望一打开就是今天的最新对话，可以加上这句
  if (!localStorage.getItem('keep_old_session')) {
    currentSessionId.value = today
    localStorage.setItem('current_session_id', today)
  }

  // 2. 拉取左侧历史列表
  try {
    const res = await request.get('/chat/history')
    historyList.value = res.history || []
  } catch (e) {
    console.error("获取历史列表失败", e)
  }

  // 3. 加载当前业务日的聊天记录
  await loadChat(currentSessionId.value)
})

// 切换历史记录
const loadHistoryChat = async (dateStr) => {
  currentSessionId.value = dateStr
  localStorage.setItem('current_session_id', dateStr)
  localStorage.setItem('keep_old_session', 'true')
  drawerVisible.value = false
  await loadChat(dateStr)
}

// 加载聊天记录
const loadChat = async (sessionId) => {
  chatHistory.value = []
  try {
    const res = await request.get(`/chat/history/${sessionId}`)
    if (res.messages && res.messages.length > 0) {
      chatHistory.value = res.messages
    }
    scrollToBottom()
  } catch (e) {
    console.error("加载聊天记录失败")
  }
}

// 新建对话
const startNewChat = () => {
  const now = new Date()
  const timeStr = `${now.getHours()}${now.getMinutes()}`
  const newId = chatHistory.value.length > 0 ? `${getTodayStr()}_${timeStr}` : getTodayStr()
  currentSessionId.value = newId
  localStorage.setItem('current_session_id', newId)
  chatHistory.value = []
}

// 发送消息
const sendChat = async () => {
  const q = chatInput.value.trim()
  if (!q || loading.value) return

  chatHistory.value.push({ role: 'user', content: q })
  chatInput.value = ''
  nextTick(() => {
    if (inputRef.value) inputRef.value.style.height = 'auto'
  })

  const aiIndex = chatHistory.value.length
  chatHistory.value.push({ role: 'ai', content: '', thinking: '', showThinking: true })
  loading.value = true
  scrollToBottom()

  // 修复了参数顺序：传入了 currentSessionId.value
  await chatStream(
      q,
      currentSessionId.value,
      // onThinking
      (chunk) => {
        const msg = chatHistory.value[aiIndex]
        chatHistory.value.splice(aiIndex, 1, { ...msg, thinking: msg.thinking + chunk })
        scrollToBottom()
      },
      // onAnswer
      (chunk) => {
        const msg = chatHistory.value[aiIndex]
        const newContent = msg.content + chunk

        // 匹配 UI_ACTION
        // 如果大模型强行在中间加了换行，这个正则可能匹配不到，改成下面这个允许中间有空格/换行：
        const actionMatch = newContent.match(/\[UI_ACTION:\s*(\/\w+)\s*\]/)
        if (actionMatch) {
          const targetPath = actionMatch[1]
          //加上时间戳 query，强制刷新组件
          router.push({ path: targetPath, query: { t: Date.now() } })
          ElMessage.success(`已自动跳转到相关页面`)
        }

        const cleanContent = newContent.replace(/\[UI_ACTION:\s*\/\w+\]\s*/g, '')
        chatHistory.value.splice(aiIndex, 1, {
          ...msg,
          content: cleanContent,
          showThinking: false,
        })
        scrollToBottom()
      },
      // onDone
      () => {
        loading.value = false
        // 结束后刷新侧边栏历史列表
        request.get('/chat/history').then(res => historyList.value = res.history || [])
      },
      // onError
      (err) => {
        const msg = chatHistory.value[aiIndex]
        console.error('【真实错误】', err)
        let errMsg = typeof err === 'string' ? err : '网络或后端异常'

        if (msg.content) {
          chatHistory.value.splice(aiIndex, 1, {
            ...msg,
            content: msg.content + '\n\n*(连接中断，回答可能不完整)*',
            showThinking: false,
          })
        } else {
          chatHistory.value.splice(aiIndex, 1, {
            ...msg,
            content: `[请求失败] ${errMsg}`,
            showThinking: false,
          })
        }
        loading.value = false
      }
  )
}

// 输入框自动高度
const autoResize = () => {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

</script>

<style>
:root {
  --sw-primary: #3978d4;
  --sw-primary-soft: #edf4ff;
  --sw-text: #263449;
  --sw-muted: #7b8798;
  --sw-border: #e5eaf1;
  --sw-surface: #ffffff;
  --sw-canvas: #f4f6fa;
  --el-color-primary: var(--sw-primary);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: var(--sw-text);
  background: var(--sw-canvas);
}

.app {
  display: flex;
  min-height: 100vh;       /* 改成固定高度 */
  overflow: hidden;       /* 整体不滚动 */
}

/* 左侧固定栏 */
/* ─── 左侧栏 ─── */
.sidebar {
  width: 280px;
  min-width: 280px;
  background: #f8f9fc;
  border-right: 1px solid var(--sw-border);
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  background: #fff;
}

/* ─── 聊天消息区（滚动） ─── */
.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  min-height: 0;
}

/* 空状态提示 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: 40px 16px;
}

.empty-icon {
  font-size: 42px;
  margin-bottom: 16px;
  opacity: 0.8;
}

.empty-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.empty-tip {
  font-size: 12px;
  color: #999;
  line-height: 1.6;
}

/* ─── 消息气泡 ─── */
.chat-msg {
  margin-bottom: 12px;
  display: flex;
}

.chat-msg.user {
  justify-content: flex-end;
}

.chat-msg.ai {
  justify-content: flex-start;
}

.msg-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

.chat-msg.user .msg-bubble {
  background: #d6e9ff;           /* 淡蓝色 */
  color: #1a1a1a;
  border-top-right-radius: 4px;
}

.chat-msg.ai .msg-bubble {
  background: #fff;              /* 白色 */
  color: #333;
  border: 1px solid #ececec;
  border-top-left-radius: 4px;
}

/* ─── 底部输入区 ─── */
.chat-input-area {
  flex-shrink: 0;
  padding: 12px 16px 16px;
  background: #f8f9fc;
  border-top: 1px solid var(--sw-border);
}

/* 输入框外框 */
.input-wrapper {
  background: #fff;
  border: 1px solid #dfe5ee;
  border-radius: 14px;
  padding: 8px 10px 6px;
  transition: border-color 0.2s;
}

.input-wrapper:focus-within {
  border-color: var(--sw-primary);
  box-shadow: 0 0 0 3px rgba(57, 120, 212, 0.1);
}

/* 文本输入区（自动高度） */
.chat-textarea {
  width: 100%;
  border: none;
  outline: none;
  resize: none;
  font-size: 13px;
  line-height: 1.5;
  max-height: 120px;
  overflow-y: auto;
  background: transparent;
  font-family: inherit;
  padding: 4px 2px;
  color: #333;
  box-sizing: border-box;
}

.chat-textarea::placeholder {
  color: #bbb;
}

.chat-textarea:disabled {
  background: transparent;
  cursor: not-allowed;
}

/* 底部工具栏 */
.input-toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 6px;
}

/* 发送按钮 */
.send-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: none;
  background: var(--sw-primary);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  transition: all 0.2s;
  padding: 0;
}

.send-btn:hover:not(:disabled) {
  background: #2f68bb;
}

.send-btn:disabled {
  background: #d0d0d0;
  cursor: not-allowed;
}

/* 右侧主区域 */
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;          /* 主区域固定高度 */
  overflow: hidden;       /* 主区域不滚动 */
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 30px;
  background: var(--sw-surface);
  border-bottom: 1px solid var(--sw-border);
  box-shadow: 0 2px 8px rgba(34, 52, 79, 0.025);
  flex-shrink: 0;         /* 导航栏不被压缩 */
}

.nav-items {
  display: flex;
  gap: 10px;
}

.nav-item {
  position: relative;
  padding: 9px 15px;
  border-radius: 9px;
  font-size: 15px;
  font-weight: 600;
  color: #687589;
  text-decoration: none;
  transition: color 0.2s;
}

.nav-item:hover {
  color: var(--sw-primary);
  background: #f5f8fd;
}

.nav-item.active {
  color: var(--sw-primary);
  background: var(--sw-primary-soft);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid #dbe3ef;
  background: linear-gradient(145deg, #edf3fc, #dce8f8);
}

.main-content {
  padding: 20px 30px;
  flex: 1;
  overflow: hidden;       /* 关键：让子组件自己管理滚动 */
  min-height: 0;          /* 关键：让 flex 子元素能正确收缩 */
}

@media (max-width: 760px) {
  .sidebar { width: 240px; min-width: 240px; }
  .top-nav { padding: 10px 14px; }
  .nav-items { gap: 2px; }
  .nav-item { padding: 8px 10px; font-size: 14px; }
  .main-content { padding: 14px; }
}

/* ─── 自定义删除确认框 ─── */
.delete-confirm-box {
  border-radius: 12px !important;
  padding: 20px !important;
  width: 400px !important;
  overflow: hidden;
  box-shadow: 0 18px 48px rgba(31, 48, 74, 0.18) !important;
}

.delete-confirm-box .el-message-box__header {
  padding-bottom: 12px;
}

.delete-confirm-box .el-message-box__title {
  font-size: 17px;
  font-weight: 700;
  color: #263449;
}

.delete-confirm-box .el-message-box__content {
  padding: 12px 0 20px;
  font-size: 14px;
  line-height: 1.65;
  color: #69778b;
}

.delete-confirm-box .el-message-box__status {
  font-size: 22px !important;
  color: #d99a32 !important;
}

.delete-confirm-btn {
  background-color: var(--sw-primary) !important;
  border-color: var(--sw-primary) !important;
  color: #fff !important;
  border-radius: 8px !important;
  padding: 9px 20px !important;
  font-weight: 600;
}

.delete-confirm-btn:hover {
  background-color: #2f68bb !important;
  border-color: #2f68bb !important;
}

/* 取消按钮美化 */
.delete-confirm-box .el-button:not(.delete-confirm-btn) {
  border-radius: 8px;
  padding: 9px 20px;
  color: #5f6e82;
  border-color: #dce3ec;
}

.delete-confirm-box .el-button:not(.delete-confirm-btn):hover {
  color: var(--sw-primary);
  border-color: #b7cef0;
  background: #f6f9ff;
}

/* ─── 自定义滚动条 ─── */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #d9d9d9;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #bfbfbf;
}

/* 横向滚动条稍微细一点 */
.month-plans::-webkit-scrollbar {
  height: 6px;
}
.thinking-box {
  background: #f5f5f5;
  border-left: 3px solid #d0d0d0;
  border-radius: 4px;
  padding: 8px 10px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #888;
}

.thinking-label {
  font-weight: 600;
  margin-bottom: 4px;
  color: #666;
}

.thinking-content {
  white-space: pre-wrap;
  line-height: 1.5;
  max-height: 120px;
  overflow-y: auto;
}
</style>
