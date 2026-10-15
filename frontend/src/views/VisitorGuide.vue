<template>
  <div class="guide-shell">
    <!-- 顶栏 -->
    <header class="topbar">
      <button class="back-btn" @click="goHome">← 返回首页</button>
      <div class="topbar-brand">校园智导 · 点击地标听讲解</div>
      <div class="topbar-status">
        <span>{{ spots.length }} 处校园地标</span>
      </div>
    </header>

    <div class="guide-body">
      <!-- ===== 左侧：校园地图 ===== -->
      <div class="map-wrap">
        <button class="map-zoom-btn" @click="openZoom" title="点击放大查看">⤢ 放大查看</button>
        <svg :viewBox="`0 0 ${vb.w} ${vb.h}`" class="guide-map" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id="goldGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#c9a86a" />
              <stop offset="100%" stop-color="#a0844c" />
            </linearGradient>
            <filter id="softGlow" x="-60%" y="-60%" width="220%" height="220%">
              <feGaussianBlur stdDeviation="6" result="b" />
              <feMerge>
                <feMergeNode in="b" /><feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          <!-- 底图：校园平面图 -->
          <image href="/images/campus_map.jpg" x="0" y="0" :width="vb.w" :height="vb.h" />

          <!-- 点位 -->
          <g v-for="spot in spots" :key="spot.id"
             class="spot-node"
             :class="{ active: isSelected(spot) }"
             @click="openSpot(spot)">
            <circle v-if="isSelected(spot)" :cx="posX(spot)" :cy="posY(spot)" r="18" fill="none"
                    stroke="#c9a86a" stroke-width="2" opacity="0.8">
              <animate attributeName="r" values="16;26;16" dur="1.8s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.8;0.15;0.8" dur="1.8s" repeatCount="indefinite" />
            </circle>
            <circle :cx="posX(spot)" :cy="posY(spot)" r="16"
                    class="spot-circle" :filter="isSelected(spot) ? 'url(#softGlow)' : undefined" />
            <text :x="posX(spot)" :y="posY(spot) + 5" text-anchor="middle" class="spot-no">{{ spot.no }}</text>
            <text :x="posX(spot) + (posX(spot) > vb.w / 2 ? -24 : 24)" :y="posY(spot) + 5"
                  :text-anchor="posX(spot) > vb.w / 2 ? 'end' : 'start'" class="spot-name">{{ spot.name }}</text>
          </g>

          <!-- 指北针 + 图例 -->
          <g transform="translate(1150, 60)" opacity="0.7">
            <circle r="26" fill="none" stroke="rgba(200,192,180,0.35)" stroke-width="1" />
            <path d="M0,-18 L6,4 L0,0 L-6,4 Z" fill="#c9a86a" />
            <text y="-32" text-anchor="middle" class="mini-label">北</text>
          </g>
          <text :x="vb.w / 2" :y="vb.h - 14" text-anchor="middle" class="mini-label" opacity="0.55">
            点击地图圆点查看地标讲解
          </text>
        </svg>
      </div>

      <!-- ===== 右侧：讲解面板 ===== -->
      <div class="panel">
        <!-- 未选择 -->
        <div v-if="!selected" class="panel-empty">
          <span class="panel-empty-mark">🏫</span>
          <p class="panel-empty-title">校园智导 · 新生报到动线</p>
          <p class="panel-empty-hint">
            点击地图上的圆点，<br>查看实拍照片、位置说明与 AI 语音讲解。<br>
            <span class="highlight">{{ spots.length }} 处地标</span> 等你探索。
          </p>
        </div>

        <!-- 已选地标 -->
        <div v-else class="panel-card">
          <div class="panel-card-head">
            <span class="spot-badge">{{ selected.no }}</span>
            <h3 class="panel-card-title">{{ selected.name }}</h3>
            <button class="close-btn" @click="closePanel">✕</button>
          </div>

          <img v-if="selected.img" :src="selected.img" :alt="selected.name" class="panel-img" />
          <div v-else class="photo-placeholder">
            <span class="ph-icon">📷</span>
            <p>实拍照片待补充</p>
            <p class="ph-tip">{{ selected.tip }}</p>
          </div>

          <p class="panel-brief">{{ selected.brief }}</p>

          <!-- AI 讲解 -->
          <button class="ai-btn" :disabled="aiLoading" @click="askAi(selected)">
            {{ aiLoading ? 'AI 讲解员准备中…' : (aiText ? '重新听 AI 讲解' : '听 AI 数字讲解员讲解') }}
          </button>
          <div v-if="aiText" class="ai-answer">{{ aiText }}</div>
          <div v-if="aiSources.length" class="ai-sources">
            <span class="ai-sources-label">参考来源</span>
            <span v-for="(s, si) in aiSources" :key="si" class="ai-sources-item">{{ formatSource(s) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 放大查看灯箱 -->
    <div v-if="zoomOpen" class="zoom-lightbox" @click.self="closeZoom">
      <div class="zoom-toolbar">
        <button @click="zoomScale = Math.min(zoomScale + 0.25, 4)" title="放大">＋</button>
        <span class="zoom-pct">{{ Math.round(zoomScale * 100) }}%</span>
        <button @click="zoomScale = Math.max(zoomScale - 0.25, 0.5)" title="缩小">－</button>
        <button @click="zoomScale = 1" title="重置">重置</button>
        <a class="zoom-dl" :href="mapSrc" download="campus_map.jpg">下载</a>
        <button @click="closeZoom" title="关闭">✕</button>
      </div>
      <div class="zoom-stage" @wheel.prevent="onWheel">
        <img :src="mapSrc" :style="{ transform: `scale(${zoomScale})` }" class="zoom-img" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { GUIDE_SPOTS, GUIDE_VIEWBOX, GUIDE_ROUTE_NAME } from '@/config/guideRoute'

const router = useRouter()
const spots = GUIDE_SPOTS
const vb = GUIDE_VIEWBOX
const routeName = GUIDE_ROUTE_NAME

const selected = ref(null)
const aiText = ref('')
const aiSources = ref([])
const aiLoading = ref(false)
let currentAudio = null

// ===== 放大查看灯箱 =====
const zoomOpen = ref(false)
const zoomScale = ref(1)
const mapSrc = '/images/campus_map.jpg'
function openZoom() { zoomScale.value = 1; zoomOpen.value = true }
function closeZoom() { zoomOpen.value = false; zoomScale.value = 1 }
function onWheel(e) {
  const delta = e.deltaY < 0 ? 0.15 : -0.15
  zoomScale.value = Math.min(4, Math.max(0.5, zoomScale.value + delta))
}

function posX(spot) { return Math.round(spot.pctX * vb.w / 100) }
function posY(spot) { return Math.round(spot.pctY * vb.h / 100) }
function isSelected(spot) { return selected.value && selected.value.id === spot.id }
function formatSource(s) { return ((s && s.source) || '').replace(/\.(docx|pdf|txt|md)$/i, '') }

// ===== 面板交互 =====
function openSpot(spot) {
  selected.value = spot
  aiText.value = ''
  aiSources.value = []
  stopAudio()
}

function closePanel() {
  selected.value = null
  stopAudio()
}

// ===== AI 讲解 =====
async function askAi(spot) {
  aiLoading.value = true
  aiText.value = ''
  stopAudio()
  const tempId = 'g' + Date.now()
  try {
    const res = await axios.post('/api/chat', {
      question: `请用面向新生的校园导览讲解员口吻，简明介绍「${spot.name}」的功能、位置和实用信息，180字以内。`,
      session_id: localStorage.getItem('lingshan_session_id') || tempId,
    })
    aiText.value = res.data.answer
    aiSources.value = res.data.sources || []
    fetchAudioInBackground(res.data.log_id)
  } catch {
    ElMessage.error('讲解服务暂时不可用，请稍后再试')
  } finally {
    aiLoading.value = false
  }
}

async function fetchAudioInBackground(logId) {
  if (!logId || logId <= 0) return
  for (let i = 0; i < 60; i++) {
    try {
      const res = await axios.get(`/api/chat/audio/${logId}`)
      if (res.data?.status === 'ready' && res.data.audio) {
        stopAudio()
        currentAudio = new Audio('data:audio/mp3;base64,' + res.data.audio)
        currentAudio.play()
        return
      }
      if (res.data?.status === 'failed') return
    } catch { /* ignore */ }
    await new Promise(r => setTimeout(r, 200))
  }
}

function stopAudio() {
  if (currentAudio) { currentAudio.pause(); currentAudio = null }
}

function goHome() { stopAudio(); router.push('/') }
</script>

<style scoped>
.guide-shell {
  position: relative;
  width: 100%;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: #0f0d0a;
  color: #c8c0b4;
  font-family: var(--font-sans);
  font-weight: 300;
}

.topbar {
  flex-shrink: 0;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: rgba(15, 13, 10, 0.9);
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}
.back-btn { background: none; border: none; color: rgba(200,192,180,0.45); font-size: 13px; cursor: pointer; font-family: var(--font-sans); transition: color 0.25s; }
.back-btn:hover { color: var(--patina); }
.topbar-brand { font-family: var(--font-song); font-size: 14px; letter-spacing: 0.12em; color: rgba(200,192,180,0.6); }
.topbar-status { display: flex; align-items: center; gap: 6px; font-size: 12px; color: rgba(200,192,180,0.35); }

.guide-body { flex: 1; display: flex; gap: 14px; padding: 14px; min-height: 0; }
.map-wrap { position: relative; flex: 1.35; min-width: 0; display: flex; }
.guide-map { width: 100%; height: auto; max-height: calc(100dvh - 62px); border: 1px solid rgba(255,255,255,0.04); border-radius: 10px; }
.map-zoom-btn {
  position: absolute; top: 12px; right: 12px; z-index: 6;
  padding: 6px 12px; font-size: 12px; letter-spacing: 0.08em;
  color: #e8d9b8; background: rgba(15,13,10,0.7);
  border: 1px solid rgba(160,132,76,0.4); border-radius: 16px;
  cursor: pointer; font-family: var(--font-sans); transition: background 0.25s;
}
.map-zoom-btn:hover { background: rgba(160,132,76,0.2); }

.spot-node { cursor: pointer; }
.spot-circle { fill: rgba(255,255,255,0.92); stroke: rgba(160,132,76,0.6); stroke-width: 1.5; transition: fill 0.3s; }
.spot-node.active .spot-circle { fill: #ffffff; stroke: #c9a86a; stroke-width: 2; }
.spot-no { fill: transparent; stroke: rgba(40,30,15,0.82); stroke-width: 0.8; font-size: 12px; font-weight: 600; pointer-events: none; }
.spot-node.active .spot-no { stroke: #6b5328; }
.spot-name { fill: rgba(200,192,180,0.7); font-size: 13px; font-family: var(--font-song); letter-spacing: 0.05em; pointer-events: none; }
.spot-node.active .spot-name { fill: #e8d9b8; }
.walk-label { fill: rgba(200,192,180,0.55); font-size: 11px; pointer-events: none; }
.mini-label { fill: rgba(200,192,180,0.4); font-size: 11px; pointer-events: none; }

.panel { flex: 1; min-width: 320px; max-width: 430px; display: flex; flex-direction: column; gap: 10px; overflow-y: auto; padding-right: 2px; }
.panel::-webkit-scrollbar { width: 3px; }
.panel::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.06); }

.panel-empty { text-align: center; padding-top: 90px; }
.panel-empty-mark { font-size: 42px; color: rgba(160,132,76,0.35); }
.panel-empty-title { font-family: var(--font-song); font-size: 20px; letter-spacing: 0.2em; color: rgba(200,192,180,0.55); margin: 14px 0 10px; }
.panel-empty-hint { font-size: 13.5px; line-height: 2; color: rgba(200,192,180,0.35); }
.highlight { color: var(--patina); }

.panel-card {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  border-radius: 10px;
  padding: 18px;
}
.panel-card-head { display: flex; align-items: center; gap: 10px; }
.spot-badge {
  width: 30px; height: 30px; border-radius: 50%;
  border: 1px solid rgba(160,132,76,0.4);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 12px; color: var(--patina); flex-shrink: 0;
}
.panel-card-title { flex: 1; font-family: var(--font-song); font-size: 19px; letter-spacing: 0.1em; color: #e8d9b8; margin: 0; }
.close-btn { background: none; border: none; color: rgba(200,192,180,0.35); cursor: pointer; font-size: 14px; }
.close-btn:hover { color: #c8c0b4; }

.panel-img { width: 100%; border-radius: 8px; margin-top: 12px; aspect-ratio: 4/3; object-fit: cover; }
.photo-placeholder {
  width: 100%; margin-top: 12px; aspect-ratio: 4/3;
  border-radius: 8px;
  background: rgba(255,255,255,0.02);
  border: 1px dashed rgba(160,132,76,0.25);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  color: rgba(200,192,180,0.45);
  gap: 4px;
}
.photo-placeholder p { margin: 0; font-size: 13.5px; }
.photo-placeholder .ph-icon { font-size: 32px; opacity: 0.7; }
.photo-placeholder .ph-tip { font-size: 11.5px; color: rgba(200,192,180,0.28); max-width: 80%; text-align: center; line-height: 1.6; }

.panel-brief { font-size: 13.5px; line-height: 1.9; color: rgba(200,192,180,0.6); margin: 12px 0; }

.ai-btn {
  width: 100%; height: 38px; border-radius: 19px;
  border: 1px solid rgba(160,132,76,0.35);
  background: rgba(160,132,76,0.08); color: #d8c9a5;
  font-size: 13px; letter-spacing: 0.06em; cursor: pointer; font-family: var(--font-sans);
  transition: background 0.25s;
}
.ai-btn:hover:not(:disabled) { background: rgba(160,132,76,0.16); }
.ai-btn:disabled { opacity: 0.5; cursor: wait; }

.ai-answer {
  margin-top: 12px; padding: 12px 14px; border-radius: 8px;
  background: rgba(255,255,255,0.025); border-left: 2px solid rgba(160,132,76,0.4);
  font-size: 13px; line-height: 1.9; color: rgba(200,192,180,0.75);
  white-space: pre-wrap;
}
.ai-sources {
  margin-top: 8px; display: flex; align-items: center; gap: 5px; flex-wrap: wrap;
  font-size: 11px; color: rgba(200,192,180,0.4);
}
.ai-sources-label { color: rgba(160,132,76,0.45); }
.ai-sources-item {
  padding: 1px 8px; border: 1px solid rgba(255,255,255,0.06); border-radius: 10px;
  background: rgba(255,255,255,0.02);
}

@media (max-width: 900px) {
  .guide-body { flex-direction: column; }
  .panel { max-width: none; min-width: 0; }
  .guide-map { max-height: 60dvh; }
}

/* ===== 放大查看灯箱 ===== */
.zoom-lightbox {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(0,0,0,0.88);
  display: flex; flex-direction: column;
}
.zoom-toolbar {
  flex-shrink: 0;
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px;
  background: rgba(15,13,10,0.95);
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.zoom-toolbar button, .zoom-dl {
  min-width: 36px; height: 32px; padding: 0 12px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 13px; color: #d8c9a5;
  background: rgba(160,132,76,0.1);
  border: 1px solid rgba(160,132,76,0.35); border-radius: 6px;
  cursor: pointer; text-decoration: none; font-family: var(--font-sans);
}
.zoom-toolbar button:hover, .zoom-dl:hover { background: rgba(160,132,76,0.22); }
.zoom-pct { color: rgba(200,192,180,0.7); font-size: 13px; min-width: 50px; text-align: center; }
.zoom-stage {
  flex: 1; overflow: auto;
  display: flex; align-items: center; justify-content: center; padding: 24px;
}
.zoom-img {
  max-width: none; max-height: none;
  transform-origin: center center;
  transition: transform 0.1s ease-out;
  cursor: zoom-in;
}
</style>
