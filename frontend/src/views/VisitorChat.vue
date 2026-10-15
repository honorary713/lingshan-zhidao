<template>
  <div class="visitor-shell">
    <!-- 左侧会话边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="startNewSession">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          新对话
        </button>
      </div>

      <div class="session-group">最近</div>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: s.id === sessionId }"
          @click="switchSession(s.id)"
        >
          <svg class="session-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span class="session-title">{{ s.title }}</span>
          <button class="session-del" @click.stop="deleteSession(s.id)">×</button>
        </div>
        <div v-if="sessions.length === 0" class="session-empty">暂无历史对话</div>
      </div>

      <div class="sidebar-footer">
        <button class="back-link" @click="goHome">← 返回首页</button>
      </div>
    </aside>

    <!-- 右侧主区域 -->
    <main class="main-area">
      <header class="topbar">
        <div class="topbar-brand">校园智导 · AI 导览</div>
        <div class="topbar-status"><span class="dot"></span><span>在线</span></div>
      </header>

      <div class="messages" ref="chatScroll">
        <div class="empty-state" v-if="chatList.length === 0 && !loading">
          <div class="empty-logo">石</div>
          <p class="empty-title">校园智导 · AI 导览</p>
          <p class="empty-hint">我是你的校园助手。新生报到、住宿餐饮、学习教务都可以问我。</p>
          <div class="empty-suggest">
            <button class="suggest-chip" v-for="q in suggestions" :key="q" @click="quickAsk(q)">{{ q }}</button>
          </div>
        </div>

        <template v-else>
          <div class="messages-inner">
            <div v-for="(item, idx) in chatList" :key="item.logId || item._tempId" class="msg-row" :style="{ animationDelay: idx * 0.04 + 's' }">
              <div class="msg user" v-if="item.question">
                <div class="bubble user-bubble">{{ item.question }}</div>
              </div>
              <div class="msg bot" v-if="item.isTyping || item.answer">
                <div class="bot-avatar">石</div>
                <div class="bot-content">
                  <div class="bubble typing-bubble" v-if="item.isTyping"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>
                  <div class="bubble bot-bubble" v-else>{{ item.answer }}</div>
                  <div class="sources" v-if="!item.isTyping && !item.isError && item.sources && item.sources.length">
                    <span class="sources-label">参考来源</span>
                    <span v-for="(s, si) in item.sources" :key="si" class="sources-item">{{ formatSource(s) }}</span>
                  </div>
                  <div class="rating" v-if="!item.isTyping && !item.isError && item.rating === null">
                    <span class="rating-label">满意吗？</span>
                    <span v-for="s in [1,2,3,4,5]" :key="s" class="rating-num" @click="handleScore(item.logId, s)">{{ s }}</span>
                  </div>
                  <div class="rating done" v-else-if="!item.isTyping && item.rating !== null">已评分 {{ item.rating }}/5</div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Live2D 数字人（右下角小尺寸） -->
      <div class="dh-zone">
        <Live2DModel ref="live2dRef" :model-path="config.model_path || '/live2d/hiyori/hiyori_free_t08.model3.json'" :width="140" :height="200" @loaded="onModelLoaded" @error="onModelError" />
        <div v-if="modelFailed" class="dh-ghost">石</div>
      </div>

      <!-- 底部输入区 -->
      <footer class="input-dock">
        <div class="input-row">
          <button class="mic-btn" :class="{ listening: isRecording }" @mousedown="startRecord" @mouseup="stopRecord" @mouseleave="stopRecord" @touchstart.prevent="startRecord" @touchend.prevent="stopRecord" @touchcancel.prevent="stopRecord" :disabled="loading">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/>
            </svg>
          </button>
          <input v-model="inputText" class="input-field" placeholder="输入你的问题…" @keydown.enter="sendMsg" :disabled="loading" />
          <button class="send-btn" @click="sendMsg" :disabled="loading || isSpeaking || !inputText.trim()">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
          <button v-if="isSpeaking" class="stop-btn" @click="stopSpeaking">⏹</button>
        </div>
        <div class="input-hint">{{ statusText }}</div>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import Live2DModel from '@/components/Live2DModel.vue'
import { getConfig } from '@/api/digitalHuman'
import { useAudio } from '@/composables/useAudio'

const router = useRouter()
const chatScroll = ref(null)
const inputText = ref('')
const chatList = ref([])
const loading = ref(false)
const isSpeaking = ref(false)
const statusText = ref('按 Enter 发送，或长按麦克风说话')
const live2dRef = ref(null)
const modelFailed = ref(false)
const config = ref({ model_path: '/live2d/hiyori/hiyori_free_t08.model3.json' })
const suggestions = ['学校概况', '报到需要带什么', '宿舍怎么住', '学费怎么交', '怎么申请助学金', '校园怎么走']
const { isRecording, startRecording, stopRecording, playAudioWithLipSync, stopAllAudio, cleanup } = useAudio()

// 会话 ID：整轮对话共用同一个，后端按 session_id 维护多轮记忆
const SESSION_STORAGE_KEY = 'lingshan_session_id'
const SESSIONS_STORAGE_KEY = 'lingshan_sessions'
const sessionId = ref('')
const sessions = ref([])

function createSessionId() {
  return 's' + Date.now() + '-' + Math.random().toString(36).slice(2, 10)
}

function getOrCreateSessionId() {
  let sid = localStorage.getItem(SESSION_STORAGE_KEY)
  if (!sid) {
    sid = createSessionId()
    localStorage.setItem(SESSION_STORAGE_KEY, sid)
  }
  return sid
}

function loadSessions() {
  try { sessions.value = JSON.parse(localStorage.getItem(SESSIONS_STORAGE_KEY) || '[]') } catch { sessions.value = [] }
}
function saveSessions() { localStorage.setItem(SESSIONS_STORAGE_KEY, JSON.stringify(sessions.value)) }

function startNewSession() {
  const newId = createSessionId()
  localStorage.setItem(SESSION_STORAGE_KEY, newId)
  sessionId.value = newId
  chatList.value = []
  ElMessage.success('已开启新对话')
}

function switchSession(id) {
  if (id === sessionId.value) return
  localStorage.setItem(SESSION_STORAGE_KEY, id)
  sessionId.value = id
  chatList.value = []
  ElMessage.info('已切换会话，后续提问将延续该会话上下文')
}

function deleteSession(id) {
  sessions.value = sessions.value.filter(s => s.id !== id)
  saveSessions()
  if (id === sessionId.value) startNewSession()
}

function ensureSessionTitle(text) {
  if (!sessions.value.find(s => s.id === sessionId.value)) {
    sessions.value.unshift({ id: sessionId.value, title: (text || '新对话').slice(0, 18), timestamp: Date.now() })
    saveSessions()
  }
}

function goHome() { router.push('/') }
function onModelLoaded() { modelFailed.value = false }
function onModelError() { modelFailed.value = true }
function quickAsk(text) { inputText.value = text; sendMsg() }
function formatSource(s) { return ((s && s.source) || '').replace(/\.(docx|pdf|txt|md)$/i, '') }

onMounted(async () => {
  sessionId.value = getOrCreateSessionId()
  loadSessions()
  try { config.value = await getConfig() } catch(e){/*ignore*/}
})
onUnmounted(() => { cleanup(); if(live2dRef.value){ live2dRef.value.setMouth(0); live2dRef.value.stopTalking() } })

watch(chatList, async () => { await nextTick(); if(chatScroll.value) chatScroll.value.scrollTop = chatScroll.value.scrollHeight }, { deep: true })

function stopSpeaking() { stopAllAudio(live2dRef); isSpeaking.value = false; live2dRef.value?.stopTalking(); statusText.value = '按 Enter 发送，或长按麦克风说话' }

function speakWithBrowserTTS(text) {
  if (typeof speechSynthesis === 'undefined') { isSpeaking.value = false; return }
  speechSynthesis.cancel(); isSpeaking.value = true
  const u = new SpeechSynthesisUtterance(text); u.lang = 'zh-CN'; u.rate = 1.0
  u.onend = () => { isSpeaking.value = false; live2dRef.value?.stopTalking() }
  u.onerror = () => { isSpeaking.value = false; live2dRef.value?.stopTalking() }
  live2dRef.value?.startTalking()
  speechSynthesis.speak(u)
}

async function fetchAudioInBackground(logId, answerText) {
  if (!logId || logId <= 0) { speakWithBrowserTTS(answerText); return }
  for (let i = 0; i < 60; i++) {
    try {
      const res = await axios.get(`/api/chat/audio/${logId}`)
      if (res.data?.status === 'ready' && res.data.audio) {
        isSpeaking.value = true; live2dRef.value?.startTalking()
        await playAudioWithLipSync(res.data.audio, live2dRef)
        isSpeaking.value = false; live2dRef.value?.stopTalking()
        return
      } else if (res.data?.status === 'failed') { speakWithBrowserTTS(answerText); return }
    } catch(e){/*ignore*/}
    await new Promise(r => setTimeout(r, 200))
  }
  speakWithBrowserTTS(answerText)
}

async function sendMsg() {
  const text = inputText.value.trim()
  if (!text) return ElMessage.warning('请输入您想咨询的问题')
  if (loading.value) return
  inputText.value = ''; loading.value = true; statusText.value = '正在思考…'
  if (live2dRef.value) live2dRef.value.startTalking()
  const tempId = 't' + Date.now()
  chatList.value.push({ _tempId: tempId, logId: null, question: text, answer: '', rating: null, isTyping: true, isError: false })
  try {
    const res = await axios.post('/api/chat', { question: text, session_id: sessionId.value })
    const t = chatList.value.find(i => i._tempId === tempId)
    if (t) { t.logId = res.data.log_id; t.answer = res.data.answer; t.sources = res.data.sources || []; t.isTyping = false; t._tempId = undefined }
    ensureSessionTitle(text)
    statusText.value = '按 Enter 发送，或长按麦克风说话'; fetchAudioInBackground(res.data.log_id, res.data.answer)
  } catch {
    const t = chatList.value.find(i => i._tempId === tempId)
    if (t) { t.logId = null; t.answer = '抱歉，服务暂不可用。'; t.isTyping = false; t.isError = true; t._tempId = undefined }
    ElMessage.error('请求失败'); statusText.value = '按 Enter 发送，或长按麦克风说话'
  } finally { loading.value = false }
}

async function handleScore(logId, score) {
  if (!logId) return
  try { await axios.post('/api/chat/score', { log_id: logId, score }); const t = chatList.value.find(i => i.logId === logId); if(t) t.rating = score; ElMessage.success('感谢反馈') } catch{ ElMessage.error('提交失败') }
}

function stopRecord() { stopRecording() }

async function startRecord() {
  if (isRecording.value || loading.value) return
  statusText.value = '正在聆听…'
  try {
    const wav = await startRecording()
    if (!wav) { statusText.value = '按 Enter 发送，或长按麦克风说话'; return }
    statusText.value = '识别中…'
    const fd = new FormData(); fd.append('file', wav, 'r.wav')
    const res = await axios.post('/api/chat/asr', fd, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 10000 })
    if (res.data?.text?.trim()) { inputText.value = res.data.text.trim(); statusText.value = '确认后发送' }
    else { statusText.value = '按 Enter 发送，或长按麦克风说话'; ElMessage.warning('未能识别') }
  } catch { statusText.value = '按 Enter 发送，或长按麦克风说话'; ElMessage.error('语音识别失败') }
  finally { isRecording.value = false }
}
</script>

<style scoped>
.visitor-shell{position:relative;width:100vw;height:100dvh;display:flex;overflow:hidden;background:#faf7f1;font-family:var(--font-sans);color:#2c2620}

/* 左侧边栏 */
.sidebar{width:260px;flex-shrink:0;display:flex;flex-direction:column;background:#f1e9d9;border-right:1px solid #e4d8c2}
.sidebar-header{padding:14px}
.new-chat-btn{width:100%;height:44px;display:flex;align-items:center;justify-content:center;gap:8px;border:1px solid #e4d8c2;border-radius:8px;background:#fffdf8;color:#3a3024;font-size:14px;font-weight:500;cursor:pointer;transition:background .2s,border-color .2s}
.new-chat-btn:hover{background:#efe6d3;border-color:#d8c9ad}
.session-group{padding:18px 16px 6px;font-size:12px;font-weight:500;color:#8a7c68;letter-spacing:.02em}
.session-list{flex:1;overflow-y:auto;padding:0 10px 10px}
.session-list::-webkit-scrollbar{width:4px}
.session-list::-webkit-scrollbar-thumb{background:#d8cab0;border-radius:2px}
.session-item{display:flex;align-items:center;gap:8px;padding:9px 10px;border-radius:6px;cursor:pointer;color:#3a3024;transition:background .15s;position:relative}
.session-item:hover{background:#ebe1cd}
.session-item.active{background:#e7dcc4}
.session-item.active::before{content:'';position:absolute;left:0;top:8px;bottom:8px;width:3px;background:#b8543f;border-radius:0 2px 2px 0}
.session-icon{color:#a99a82;flex-shrink:0}
.session-title{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px}
.session-del{width:20px;height:20px;display:flex;align-items:center;justify-content:center;border-radius:4px;border:none;background:transparent;color:#a99a82;font-size:15px;cursor:pointer;opacity:0;transition:opacity .15s,background .15s}
.session-item:hover .session-del{opacity:1}
.session-del:hover{background:#ddd0b6;color:#3a3024}
.session-empty{padding:24px 10px;color:#a99a82;font-size:13px;text-align:center}
.sidebar-footer{padding:12px 14px;border-top:1px solid #e4d8c2}
.back-link{background:none;border:none;color:#8a7c68;font-size:13px;cursor:pointer;transition:color .2s}
.back-link:hover{color:#3a3024}

/* 右侧主区域 */
.main-area{flex:1;display:flex;flex-direction:column;position:relative;background:#faf7f1;min-width:0}
.topbar{flex-shrink:0;height:48px;display:flex;align-items:center;justify-content:space-between;padding:0 20px;border-bottom:1px solid #ece2cf;background:#faf7f1}
.topbar-brand{font-size:14px;font-weight:500;color:#2c2620;letter-spacing:.02em}
.topbar-status{display:flex;align-items:center;gap:6px;font-size:12px;color:#8a7c68}
.topbar-status .dot{width:5px;height:5px;border-radius:50%;background:#10a37f;animation:pulse-dot 3s ease-in-out infinite}
@keyframes pulse-dot{0%,100%{opacity:.5}50%{opacity:1}}

.messages{flex:1;overflow-y:auto;position:relative;z-index:1;scroll-behavior:smooth}
.messages::-webkit-scrollbar{width:6px}
.messages::-webkit-scrollbar-thumb{background:#ddd0b6;border-radius:3px}
.empty-state{min-height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 20px 140px;text-align:center}
.empty-logo{width:52px;height:52px;border-radius:50%;background:#3a3024;color:#fff;display:flex;align-items:center;justify-content:center;font-family:var(--font-song);font-size:22px;margin-bottom:22px}
.empty-title{font-size:30px;font-weight:500;color:#2c2620;margin:0 0 10px;letter-spacing:.02em}
.empty-hint{font-size:15px;color:#8a7c68;margin:0 0 32px;max-width:420px;line-height:1.7}
.empty-suggest{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;max-width:520px}
.suggest-chip{height:40px;padding:0 16px;border:1px solid #e4d8c2;border-radius:20px;background:#fffdf8;color:#3a3024;font-size:13px;cursor:pointer;transition:background .2s,border-color .2s}
.suggest-chip:hover{background:#efe6d3;border-color:#d8c9ad}

.messages-inner{max-width:760px;margin:0 auto;width:100%;padding:24px 20px 180px}
.msg-row{animation:fade-up .35s ease both}
@keyframes fade-up{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.msg{display:flex;margin:24px 0}
.msg.user{justify-content:flex-end}
.msg.bot{justify-content:flex-start;align-items:flex-start;gap:14px}
.bot-avatar{width:30px;height:30px;border-radius:50%;background:#3a3024;color:#fff;display:flex;align-items:center;justify-content:center;font-family:var(--font-song);font-size:14px;flex-shrink:0;margin-top:2px}
.bot-content{flex:1;min-width:0;padding-top:4px}
.bubble{font-size:15px;line-height:1.75;white-space:pre-wrap;word-break:break-word;letter-spacing:.01em}
.user-bubble{max-width:78%;background:#e9dcc2;color:#3a3024;border-radius:18px;padding:11px 16px}
.bot-bubble{color:#2c2620;padding:0;max-width:none}
.typing-bubble{display:inline-flex;gap:4px;align-items:center;padding:13px 16px;background:#f3ebda;border-radius:16px}
.typing-dot{width:6px;height:6px;background:#a99a82;border-radius:50%;animation:dot-bounce 1.4s ease-in-out infinite both}
.typing-dot:nth-child(1){animation-delay:-.32s}
.typing-dot:nth-child(2){animation-delay:-.16s}
@keyframes dot-bounce{0%,80%,100%{transform:scale(.5);opacity:.3}40%{transform:scale(1);opacity:.8}}
.sources{margin-top:10px;font-size:12px;color:#8a7c68;display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.sources-label{font-weight:500}
.sources-item{padding:2px 8px;border:1px solid #e4d8c2;border-radius:6px;background:#fffdf8}
.rating{margin-top:12px;font-size:12px;color:#8a7c68;display:flex;align-items:center;gap:6px}
.rating-label{margin-right:2px}
.rating-num{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;border:1px solid #e4d8c2;background:#fffdf8;font-size:11px;cursor:pointer;transition:background .15s,border-color .15s}
.rating-num:hover{background:#efe6d3;border-color:#d8c9ad}
.rating.done{color:#2c2620}

/* Live2D */
.dh-zone{position:fixed;bottom:120px;right:24px;width:140px;height:200px;overflow:hidden;z-index:2;pointer-events:none;-webkit-mask-image:linear-gradient(to bottom, transparent 0%, #000 15%, #000 85%, transparent 100%);mask-image:linear-gradient(to bottom, transparent 0%, #000 15%, #000 85%, transparent 100%)}
.dh-zone canvas{display:block}
.dh-ghost{font-size:48px;color:rgba(58,48,36,0.06);font-family:var(--font-song);animation:float 4s ease-in-out infinite}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}

/* 底部输入 */
.input-dock{position:fixed;bottom:0;left:260px;right:0;z-index:3;padding:0 20px 24px;background:linear-gradient(to top, #faf7f1 55%, rgba(250,247,241,0))}
.input-row{max-width:760px;margin:0 auto;display:flex;align-items:center;gap:8px;background:#fffdf8;border:1px solid #e4d8c2;border-radius:24px;padding:6px 6px 6px 12px;box-shadow:0 2px 14px rgba(120,95,55,0.08);transition:border-color .2s,box-shadow .2s}
.input-row:focus-within{border-color:#c9b58c;box-shadow:0 4px 18px rgba(120,95,55,0.12)}
.input-field{flex:1;height:46px;border:none;outline:none;background:transparent;font-size:15px;color:#2c2620}
.input-field::placeholder{color:#a99a82}
.input-field:disabled{opacity:.5}
.mic-btn{width:36px;height:36px;border-radius:50%;border:none;background:#f1e9d9;color:#8a7c68;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .2s,color .2s}
.mic-btn:hover:not(:disabled){background:#e7dcc4;color:#3a3024}
.mic-btn:disabled{opacity:.3}
.mic-btn.listening{background:#b8543f;color:#fff;animation:mic-pulse 1.2s ease-in-out infinite}
@keyframes mic-pulse{0%,100%{box-shadow:0 0 0 0 rgba(184,84,63,.18)}50%{box-shadow:0 0 0 8px rgba(184,84,63,0)}}
.send-btn{width:36px;height:36px;border-radius:50%;border:none;background:#3a3024;color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .2s,opacity .2s}
.send-btn:hover:not(:disabled){background:#4a3e30}
.send-btn:disabled{opacity:.3;cursor:not-allowed}
.stop-btn{width:36px;height:36px;border-radius:50%;border:none;background:#b8543f;color:#fff;font-size:13px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .2s}
.stop-btn:hover{background:#9c4631}
.input-hint{text-align:center;color:#a99a82;font-size:12px;margin-top:10px;letter-spacing:.02em}
</style>
