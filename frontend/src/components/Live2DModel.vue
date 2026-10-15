<template>
  <div ref="canvasContainer" class="live2d-container">
    <!-- 加载态 -->
    <div v-if="!loaded && !failed" class="dh-loading">
      <div class="dh-loading-ring"></div>
      <span>数字人加载中…</span>
    </div>
    <!-- 失败态 -->
    <div v-if="failed" class="dh-fallback">
      <span class="dh-fallback-icon">卍</span>
      <span class="dh-fallback-text">形象加载失败</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as PIXI from 'pixi.js'
import { Live2DModel } from 'pixi-live2d-display/cubism4'

const props = defineProps({
  modelPath: { type: String, required: true },
  width: { type: Number, default: 280 },
  height: { type: Number, default: 400 }
})

const emit = defineEmits(['loaded', 'error'])

const canvasContainer = ref(null)
const loaded = ref(false)
const failed = ref(false)

let app = null
let model = null
let idleCb = null
let talkingCb = null
let loadId = 0
let isTalking = false
let talkingMotionIndex = 0
let talkingFrame = 0

// ===== 工具函数 =====
function getMotionGroups(target) {
  try {
    const g = target.internalModel?.motionManager?._groups
    return g ? Object.keys(g) : []
  } catch (e) { return [] }
}

function getMotionsInGroup(target, group) {
  try {
    return target.internalModel?.motionManager?._groups?.[group] || []
  } catch (e) { return [] }
}

function fitModel(target) {
  if (!target) return
  const b = target.getBounds()
  if (!b.width || !b.height) return
  const s = Math.min(props.width / b.width, props.height / b.height) * 0.82
  target.scale.set(s)
  target.anchor.set(0.5, 0.5)
  target.x = props.width / 2
  target.y = props.height / 2 + 10
}

// ===== 说话动作编排 =====
// haru 模型默认 motion 组名是 ""，里面 26 个动作混在一起
// 我们按文件名特征分类：m01-m08 偏肢体，m09-m16 偏表情，m17-m26 偏互动
function _getMotionIndexForTalking(target, counter) {
  // 用名称包含 m0/m1/m2 的动作轮播
  const groups = getMotionGroups(target)
  const group = groups[0] || ""
  const motions = getMotionsInGroup(target, group)
  if (motions.length === 0) return { group, index: 0 }
  // 挑文件名中包含数字的动作（haru 的特征）
  const numMotions = motions.filter(m => {
    if (typeof m === 'string') return /\d/.test(m)
    if (m.File) return /\d/.test(m.File)
    return false
  })
  if (numMotions.length === 0) return { group, index: counter % motions.length }
  const idx = counter % numMotions.length
  return { group, index: motions.indexOf(numMotions[idx]) }
}

function _playTalkingMotion(counter) {
  if (!model) return
  try {
    const { group, index } = _getMotionIndexForTalking(model, counter)
    model.motion(group, index)
  } catch (e) {}
}

// ===== 加载模型 =====
async function loadModel(path) {
  if (!app) return
  const myId = ++loadId

  // 清理旧模型
  if (idleCb) { app.ticker.remove(idleCb); idleCb = null }
  if (talkingCb) { app.ticker.remove(talkingCb); talkingCb = null }
  if (model) {
    try { app.stage.removeChild(model) } catch (e) { /* ignore */ }
    try { model.destroy() } catch (e) { /* ignore */ }
    model = null
  }
  while (app.stage.children.length > 0) {
    try { app.stage.removeChildAt(0) } catch (e) { break }
  }
  loaded.value = false
  failed.value = false
  isTalking = false

  let lastErr = null
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      model = await Live2DModel.from(path, { autoInteract: false })
      break
    } catch (e) {
      lastErr = e
      if (attempt < 2) await new Promise(r => setTimeout(r, 600))
    }
  }
  if (!model) { failed.value = true; emit('error', lastErr); return }
  if (myId !== loadId) { try { model.destroy() } catch (e) { /* ignore */ }; return }

  app.stage.addChild(model)
  fitModel(model)

  // ===== Idle 动画 =====
  let t = 0
  let motionTimer = 0
  let nextMotion = 3 + Math.random() * 3  // 3~6秒随机动作
  const bp = Math.random() * Math.PI * 2
  const cm = model.internalModel.coreModel
  const sp = (id, val) => { try { cm.setParameterValueById(id, val) } catch (e) {} }
  let motionCount = 0

  idleCb = (delta) => {
    if (!model) return
    t += delta * 0.012
    motionTimer += delta * 0.0167

    // 呼吸
    model.y = props.height / 2 + 10 + Math.sin(t + bp) * 3

    // 身体
    sp('ParamBodyAngleX', Math.sin(t * 0.7 + bp) * 6)
    sp('ParamBodyAngleY', Math.sin(t * 0.5 + 1.2) * 4)
    sp('ParamBodyAngleZ', Math.sin(t * 0.4 + 2.3) * 3)

    // 头部
    sp('ParamAngleX', Math.sin(t * 0.6 + 0.5) * 6)
    sp('ParamAngleY', Math.sin(t * 0.4 + 1.8) * 6)
    sp('ParamAngleZ', Math.sin(t * 0.5 + 3.0) * 3)

    // 手臂摆动
    sp('ParamArmLA', Math.sin(t * 0.3) * 8)
    sp('ParamArmRA', Math.sin(t * 0.3 + Math.PI) * 8)

    // 眨眼(约4秒一次)
    const bs = Math.sin(t * 0.8)
    const bv = bs > 0.94 ? Math.max(0, 1 - (bs - 0.94) * 28) : 1.0
    sp('ParamEyeLOpen', bv)
    sp('ParamEyeROpen', bv)

    // 随机待机动作
    if (motionTimer > nextMotion && !isTalking) {
      try {
        const groups = getMotionGroups(model)
        const g = groups.length > 1 ? groups[Math.floor(Math.random() * (groups.length - 1)) + 1] : groups[0]
        const motions = getMotionsInGroup(model, g)
        if (motions.length > 0) {
          model.motion(g, Math.floor(Math.random() * motions.length))
        }
      } catch (e) {}
      nextMotion = 3 + Math.random() * 3  // 3~6秒
      motionTimer = 0
    }

    model.x = props.width / 2
    model.rotation = 0
  }
  app.ticker.add(idleCb)

  if (myId !== loadId) {
    try { app.stage.removeChild(model) } catch (e) {}
    try { model.destroy() } catch (e) {}
    model = null
    return
  }
  loaded.value = true
  emit('loaded', model)
}

onMounted(async () => {
  try {
    if (canvasContainer.value) {
      canvasContainer.value.querySelectorAll('canvas').forEach(c => c.remove())
    }
    app = new PIXI.Application({
      width: props.width, height: props.height,
      backgroundAlpha: 0, antialias: true,
      resolution: Math.min(window.devicePixelRatio || 1, 2),
      autoDensity: true
    })
    canvasContainer.value.appendChild(app.view)
    Live2DModel.registerTicker(PIXI.Ticker)
    await loadModel(props.modelPath)
  } catch (err) {
    console.error('Live2D 加载失败:', err)
    failed.value = true
    emit('error', err)
  }
})

watch(() => props.modelPath, async (n, o) => {
  if (!n || n === o || !app) return
  try { await loadModel(n) } catch (e) { console.error('模型切换失败:', e) }
})

onUnmounted(() => {
  if (idleCb && app) app.ticker.remove(idleCb)
  if (talkingCb && app) app.ticker.remove(talkingCb)
  if (app) {
    try { const c = app.view; if (c?.parentNode) c.parentNode.removeChild(c) } catch (e) {}
    app.destroy(true, { children: true, texture: true })
    app = null; model = null
  }
})

// ===== 暴露给父组件 =====
defineExpose({
  setMouth(openY) {
    if (!model) return
    const v = Math.max(0, Math.min(1, openY))
    const cm = model.internalModel.coreModel
    for (const id of ['ParamMouthOpenY', 'ParamA']) {
      try { cm.setParameterValueById(id, v) } catch (e) {}
    }
  },

  /** 开始说话：启动持续动作 + 口型追踪 */
  startTalking() {
    if (!model || isTalking) return
    isTalking = true
    talkingMotionIndex = 0
    talkingFrame = 0
    // 立刻播一个自然的开场动作
    try {
      const groups = getMotionGroups(model)
      const g = groups.filter(x => x !== 'Idle')?.[0] || groups[0]
      const motions = getMotionsInGroup(model, g)
      // 挑一个动作（跳过 index 0 避免重复，随机选后续的）
      const startIdx = motions.length > 1 ? 1 + Math.floor(Math.random() * Math.min(motions.length - 1, 3)) : 0
      model.motion(g, startIdx)
    } catch (e) {}
  },

  /** 结束说话 */
  stopTalking() {
    isTalking = false
    talkingMotionIndex = 0
    talkingFrame = 0
    const cm = model?.internalModel?.coreModel
    if (cm) {
      for (const id of ['ParamMouthOpenY', 'ParamA']) {
        try { cm.setParameterValueById(id, 0) } catch (e) {}
      }
    }
  },

  /** 播放指定动作 */
  playMotion(group, index = 0) {
    if (!model) return
    try { model.motion(group, index) } catch (e) {}
  },

  /** 说话期间每帧调用一次 —— 在 VisitorChat 的口型循环里用 */
  onTalkingTick(counter) {
    if (!model || !isTalking) return
    // 每 90 帧换一个说话动作（约 1.5 秒）让动作更丰富
    if (counter % 90 === 0) {
      talkingMotionIndex++
      _playTalkingMotion(talkingMotionIndex)
    }
  }
})
</script>

<style scoped>
.live2d-container {
  width: 100%; height: 100%;
  position: relative;
  display: flex; align-items: flex-end; justify-content: center;
}
canvas { display: block; }

.dh-loading {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  color: rgba(200,192,180,0.25); font-size: 12px; font-weight: 300;
}
.dh-loading-ring {
  width: 22px; height: 22px; border-radius: 50%;
  border: 1px solid rgba(160,132,76,0.15);
  border-top-color: rgba(160,132,76,0.3);
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.dh-fallback {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
}
.dh-fallback-icon { font-size: 40px; color: rgba(160,132,76,0.1); font-family: var(--font-song); }
.dh-fallback-text { font-size: 12px; color: rgba(200,192,180,0.2); }
</style>
