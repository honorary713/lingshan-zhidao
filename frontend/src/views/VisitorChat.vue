<template>
  <div class="visitor-shell">
    <!-- 墨染背景 -->
    <div class="ink-bg">
      <div class="ink-vignette"></div>
      <div class="ink-mist"></div>
    </div>

    <!-- 顶栏 -->
    <header class="topbar">
      <button class="back-btn" @click="goHome">← 返回首页</button>
      <div class="topbar-brand">校园智导 · AI 导览</div>
      <div class="topbar-status">
        <button class="new-chat-btn" @click="startNewSession">新对话</button>
        <span class="dot"></span>
        <span>在线</span>
      </div>
    </header>

    <!-- 消息区 -->
    <main class="messages" ref="chatScroll">
      <div class="empty-state" v-if="chatList.length === 0 && !loading">
        <div class="empty-icon">
          <svg viewBox="0 0 48 48" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1" opacity="0.25">
            <circle cx="24" cy="16" r="8"/>
            <path d="M8 44c0-10 7-16 16-16s16 6 16 16"/>
          </svg>
        </div>
        <p class="empty-title">校园智导 · AI 导览</p>
        <p class="empty-hint">我是您的校园导览助手，新生报到、住宿餐饮、学习教务都可以问我。</p>
      </div>

      <template v-else>
        <div v-for="(item, idx) in chatList" :key="item.logId || item._tempId" class="msg-row" :style="{ animationDelay: idx * 0.06 + 's' }">
          <div class="msg user" v-if="item.question">
            <div class="bubble user-bubble">{{ item.question }}</div>
          </div>
          <div class="msg bot" v-if="item.isTyping || item.answer">
            <div class="bot-avatar">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="8" r="4"/>
                <path d="M4 24c0-5 3.5-8 8-8s8 3 8 8"/>
              </svg>
            </div>
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
      </template>
    </main>

    <!-- Live2D 数字人 -->
    <div class="dh-zone">
      <Live2DModel ref="live2dRef" :model-path="config.model_path || '/live2d/hiyori/hiyori_free_t08.model3.json'" :width="280" :height="400" @loaded="onModelLoaded" @error="onModelError" />
      <div v-if="modelFailed" class="dh-ghost">石</div>
    </div>

    <!-- 快捷标签 -->
    <nav class="quickbar">
      <button class="chip" @click="quickAsk('学校概况')">学校概况</button>
      <button class="chip" @click="quickAsk('报到需要带什么')">报到材料</button>
      <button class="chip" @click="quickAsk('宿舍怎么住')">宿舍生活</button>
      <button class="chip" @click="quickAsk('学费怎么交')">学费缴纳</button>
      <button class="chip" @click="quickAsk('怎么申请助学金')">奖助学金</button>
      <button class="chip" @click="quickAsk('校园怎么走')">校园导览</button>
    </nav>

    <!-- 输入区 -->
    <footer class="input-zone">
      <div class="status-line">{{ statusText }}</div>
      <div class="input-row">
        <input v-model="inputText" class="input-field" placeholder="输入您的问题…" @keydown.enter="sendMsg" :disabled="loading" />
        <button class="mic-btn" :class="{ listening: isRecording }" @mousedown="startRecord" @mouseup="stopRecord" @mouseleave="stopRecord" @touchstart.prevent="startRecord" @touchend.prevent="stopRecord" @touchcancel.prevent="stopRecord" :disabled="loading">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/>
          </svg>
        </button>
        <button class="send-btn" @click="sendMsg" :disabled="loading || isSpeaking">{{ loading ? '…' : '发送' }}</button>
        <button v-if="isSpeaking" class="stop-btn" @click="stopSpeaking">⏹</button>
      </div>
    </footer>
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
const statusText = ref('键盘输入或长按麦克风说话')
const live2dRef = ref(null)
const modelFailed = ref(false)
const config = ref({ model_path: '/live2d/hiyori/hiyori_free_t08.model3.json' })
const { isRecording, startRecording, stopRecording, playAudioWithLipSync, stopAllAudio, cleanup } = useAudio()

// 会话 ID：整轮对话共用同一个，后端按 session_id 维护多轮记忆
const SESSION_STORAGE_KEY = 'lingshan_session_id'
const sessionId = ref('')

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

function startNewSession() {
  localStorage.setItem(SESSION_STORAGE_KEY, createSessionId())
  sessionId.value = localStorage.getItem(SESSION_STORAGE_KEY)
  chatList.value = []
  ElMessage.success('已开启新对话')
}

function goHome() { router.push('/') }
function onModelLoaded() { modelFailed.value = false }
function onModelError() { modelFailed.value = true }
function quickAsk(text) { inputText.value = text; sendMsg() }
function formatSource(s) { return ((s && s.source) || '').replace(/\.(docx|pdf|txt|md)$/i, '') }

onMounted(async () => {
  sessionId.value = getOrCreateSessionId()
  try { config.value = await getConfig() } catch(e){/*ignore*/}
})
onUnmounted(() => { cleanup(); if(live2dRef.value){ live2dRef.value.setMouth(0); live2dRef.value.stopTalking() } })

watch(chatList, async () => { await nextTick(); if(chatScroll.value) chatScroll.value.scrollTop = chatScroll.value.scrollHeight }, { deep: true })

function stopSpeaking() { stopAllAudio(live2dRef); isSpeaking.value = false; live2dRef.value?.stopTalking(); statusText.value = '键盘输入或长按麦克风说话' }

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
    statusText.value = '键盘输入或长按麦克风说话'; fetchAudioInBackground(res.data.log_id, res.data.answer)
  } catch {
    const t = chatList.value.find(i => i._tempId === tempId)
    if (t) { t.logId = null; t.answer = '抱歉，服务暂不可用。'; t.isTyping = false; t.isError = true; t._tempId = undefined }
    ElMessage.error('请求失败'); statusText.value = '键盘输入或长按麦克风说话'
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
    if (!wav) { statusText.value = '键盘输入或长按麦克风说话'; return }
    statusText.value = '识别中…'
    const fd = new FormData(); fd.append('file', wav, 'r.wav')
    const res = await axios.post('/api/chat/asr', fd, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 10000 })
    if (res.data?.text?.trim()) { inputText.value = res.data.text.trim(); statusText.value = '确认后发送' }
    else { statusText.value = '键盘输入或长按麦克风说话'; ElMessage.warning('未能识别') }
  } catch { statusText.value = '键盘输入或长按麦克风说话'; ElMessage.error('语音识别失败') }
  finally { isRecording.value = false }
}
</script>

<style scoped>
.visitor-shell{position:relative;width:100%;height:100dvh;display:flex;flex-direction:column;overflow:hidden;background:#0f0d0a;font-family:var(--font-sans);font-weight:300;color:#c8c0b4}
.ink-bg{position:absolute;inset:0;pointer-events:none;z-index:0}
.ink-vignette{position:absolute;inset:0;background:radial-gradient(ellipse 600px 360px at 50% 75%, rgba(160,132,76,0.04) 0%, transparent 70%),radial-gradient(ellipse 100vw 100vh at 50% 0%, rgba(0,0,0,0) 0%, #0f0d0a 100%)}
.ink-mist{position:absolute;bottom:0;left:0;right:0;height:180px;background:radial-gradient(ellipse 400px 100px at 50% 100%, rgba(160,132,76,0.03) 0%, transparent 70%)}
.topbar{flex-shrink:0;height:48px;display:flex;align-items:center;justify-content:space-between;padding:0 16px;position:relative;z-index:10;background:rgba(15,13,10,0.85);backdrop-filter:blur(10px);border-bottom:1px solid rgba(255,255,255,0.03)}
.back-btn{background:none;border:none;color:rgba(200,192,180,0.45);font-size:13px;cursor:pointer;font-family:var(--font-sans);font-weight:300;padding:4px 0;transition:color 0.25s}
.back-btn:hover{color:var(--patina)}
.new-chat-btn{background:none;border:1px solid rgba(255,255,255,0.08);border-radius:12px;color:rgba(200,192,180,0.45);font-size:11px;cursor:pointer;font-family:var(--font-sans);font-weight:300;padding:3px 10px;margin-right:6px;transition:all .25s}
.new-chat-btn:hover{border-color:rgba(160,132,76,0.35);color:var(--patina);background:rgba(160,132,76,0.06)}
.topbar-brand{font-family:var(--font-song);font-size:14px;letter-spacing:0.12em;color:rgba(200,192,180,0.6)}
.topbar-status{display:flex;align-items:center;gap:5px;font-size:12px;color:rgba(200,192,180,0.3)}
.topbar-status .dot{width:5px;height:5px;border-radius:50%;background:#5e8c6a;animation:pulse-dot 3s ease-in-out infinite}
@keyframes pulse-dot{0%,100%{opacity:.5}50%{opacity:1}}
.messages{flex:1;overflow-y:auto;padding:16px 20px 20px;position:relative;z-index:1;scroll-behavior:smooth}
.messages::-webkit-scrollbar{width:3px}
.messages::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.05);border-radius:2px}
.empty-state{text-align:center;padding-top:80px}
.empty-icon{margin-bottom:20px;color:rgba(160,132,76,0.25)}
.empty-title{font-family:var(--font-song);font-size:20px;letter-spacing:0.2em;margin:0 0 8px;color:rgba(200,192,180,0.5)}
.empty-hint{font-size:14px;color:rgba(200,192,180,0.25);margin:0}
.msg-row{animation:fade-up 0.4s ease both}
@keyframes fade-up{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.msg{display:flex;margin:12px 0}
.msg.user{justify-content:flex-end}
.msg.bot{justify-content:flex-start;align-items:flex-start;gap:8px}
.bot-avatar{width:28px;height:28px;border-radius:50%;background:rgba(160,132,76,0.08);border:1px solid rgba(160,132,76,0.1);display:flex;align-items:center;justify-content:center;color:rgba(160,132,76,0.5);flex-shrink:0;margin-top:2px}
.bubble{max-width:68%;padding:10px 14px;font-size:14px;line-height:1.7;white-space:pre-wrap;word-break:break-word;letter-spacing:0.02em}
.user-bubble{background:rgba(160,132,76,0.1);color:#c8c0b4;border-radius:12px 12px 4px 12px;border:1px solid rgba(160,132,76,0.06)}
.bot-bubble{background:rgba(255,255,255,0.03);color:#c8c0b4;border-radius:12px 12px 12px 4px;border:1px solid rgba(255,255,255,0.03)}
.typing-bubble{display:flex;gap:4px;align-items:center;padding:14px 16px;background:rgba(255,255,255,0.02);border-radius:12px 12px 12px 4px;border:1px solid rgba(255,255,255,0.02)}
.typing-dot{width:5px;height:5px;background:rgba(200,192,180,0.2);border-radius:50%;animation:dot-bounce 1.4s ease-in-out infinite both}
.typing-dot:nth-child(1){animation-delay:-.32s}
.typing-dot:nth-child(2){animation-delay:-.16s}
@keyframes dot-bounce{0%,80%,100%{transform:scale(.5);opacity:.3}40%{transform:scale(1);opacity:.8}}
.rating{margin-top:4px;font-size:12px;color:rgba(200,192,180,0.25);padding-left:36px;display:flex;align-items:center;gap:4px}
.rating-label{margin-right:2px}
.rating-num{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;border:1px solid rgba(255,255,255,0.06);font-size:11px;cursor:pointer;transition:all .2s}
.rating-num:hover{border-color:var(--patina);color:var(--patina);background:rgba(160,132,76,0.06)}
.rating.done{color:rgba(160,132,76,0.35)}
.sources{margin-top:6px;font-size:11px;color:rgba(200,192,180,0.25);padding-left:36px;display:flex;align-items:center;gap:5px;flex-wrap:wrap}
.sources-label{color:rgba(160,132,76,0.4);margin-right:2px}
.sources-item{padding:1px 8px;border:1px solid rgba(255,255,255,0.05);border-radius:10px;background:rgba(255,255,255,0.02)}
.dh-zone{position:absolute;bottom:160px;right:0;width:280px;height:400px;overflow:hidden;z-index:2;pointer-events:none;display:flex;align-items:flex-end;justify-content:center;-webkit-mask-image:linear-gradient(to bottom, transparent 0%, #000 12%, #000 85%, transparent 100%);mask-image:linear-gradient(to bottom, transparent 0%, #000 12%, #000 85%, transparent 100%)}
.dh-zone canvas{display:block}
.dh-ghost{font-size:56px;color:rgba(160,132,76,0.08);font-family:var(--font-song);animation:float 4s ease-in-out infinite}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
.quickbar{flex-shrink:0;display:flex;gap:6px;padding:8px 16px 6px;overflow-x:auto;white-space:nowrap;scrollbar-width:none;position:relative;z-index:3;background:linear-gradient(to top, rgba(15,13,10,0.95), rgba(15,13,10,0.6));border-top:1px solid rgba(255,255,255,0.02)}
.quickbar::-webkit-scrollbar{display:none}
.chip{flex-shrink:0;height:28px;padding:0 12px;border:1px solid rgba(255,255,255,0.04);border-radius:14px;background:rgba(255,255,255,0.02);color:rgba(200,192,180,0.4);font-size:12px;cursor:pointer;font-family:var(--font-sans);font-weight:300;transition:all .25s;letter-spacing:.03em}
.chip:hover{background:rgba(160,132,76,0.06);border-color:rgba(160,132,76,0.15);color:rgba(200,192,180,0.7)}
.input-zone{flex-shrink:0;padding:0 16px 12px;position:relative;z-index:3;background:linear-gradient(to top, rgba(15,13,10,1) 60%, transparent)}
.status-line{text-align:center;color:rgba(200,192,180,0.2);padding:4px 0 8px;font-size:11px;letter-spacing:.04em}
.input-row{display:flex;gap:6px;align-items:center}
.input-field{flex:1;height:40px;border:1px solid rgba(255,255,255,0.05);border-radius:20px;padding:0 16px;font-size:14px;font-weight:300;font-family:var(--font-sans);background:rgba(255,255,255,0.03);color:#c8c0b4;outline:none;transition:border-color .3s,background .3s}
.input-field::placeholder{color:rgba(200,192,180,0.18)}
.input-field:focus{border-color:rgba(160,132,76,0.25);background:rgba(255,255,255,0.05)}
.input-field:disabled{opacity:.3}
.mic-btn{width:36px;height:36px;min-width:36px;border-radius:50%;border:1px solid rgba(255,255,255,0.05);background:rgba(255,255,255,0.03);color:rgba(200,192,180,0.35);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .3s}
.mic-btn:hover:not(:disabled){background:rgba(255,255,255,0.06);color:rgba(200,192,180,0.6)}
.mic-btn:disabled{opacity:.25}
.mic-btn.listening{background:var(--cinnabar);border-color:var(--cinnabar);color:#fff;animation:mic-pulse 1.2s ease-in-out infinite}
@keyframes mic-pulse{0%,100%{box-shadow:0 0 0 0 rgba(193,69,58,.2)}50%{box-shadow:0 0 0 8px rgba(193,69,58,0)}}
.send-btn{height:40px;padding:0 20px;border:none;border-radius:20px;background:rgba(160,132,76,0.55);color:#fff;font-size:13px;font-weight:500;cursor:pointer;letter-spacing:.06em;transition:background .25s}
.send-btn:hover:not(:disabled){background:rgba(160,132,76,0.75)}
.send-btn:disabled{opacity:.25;cursor:not-allowed}
.stop-btn{height:40px;width:40px;border:none;border-radius:50%;background:rgba(193,69,58,0.4);color:#fff;font-size:14px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .25s}
.stop-btn:hover{background:var(--cinnabar)}
</style>
