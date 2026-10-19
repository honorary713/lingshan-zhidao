<template>
  <div class="home-memo">
    <div class="page">
      <!-- ===== 顶栏：手账页眉 ===== -->
      <header class="topbar">
        <span class="brand-seal serif">石</span>
        <span class="brand serif">校园智导手账<small>UPC FRESHMAN GUIDE</small></span>
        <nav class="topnav">
          <a href="#stub" class="nl">随身票据</a>
          <a href="#photos" class="nl">地标贴图</a>
          <a href="#memo" class="nl">备忘页</a>
          <span class="nl admin" @click="goAdmin">管理后台</span>
        </nav>
      </header>

      <!-- ===== Hero：手账摊开双页 ===== -->
      <section class="hero">
        <div class="hero-left">
          <p class="date-line">2026 年秋 · 青岛校区 · 长江西路 66 号</p>
          <h1 class="hero-title serif">新生入学<span class="stamp serif">已备案</span></h1>
          <p class="hero-sub">
            这本手账替你把报到、住宿、选课、奖助的琐碎都记好了。
            有拿不准的，直接问 AI 导览员。
          </p>
          <div class="hero-actions">
            <a class="btn-primary" @click="goChat">
              向 AI 导览员提问
              <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="#F5F1E6" stroke-width="1.7" stroke-linecap="round">
                <path d="M4 12h15M13 6l6 6-6 6" />
              </svg>
            </a>
            <a class="btn-ghost" @click="goGuide">翻开校园手绘地图</a>
          </div>
          <span class="margin-note">FRESHMAN MEMO · VOL.01</span>
        </div>
        <div class="hero-right">
          <p class="ticket-label">报到检票口 · CHECK-IN</p>
          <div class="ticket">
            <div class="ticket-head">
              <span>入学报到单</span><span class="mono">NO.2026-001</span>
            </div>
            <div class="ticket-body">
              <div class="ticket-main">
                <div class="ticket-row">
                  <div><span class="tk">日期</span><span class="tv">8 月 28 日</span></div>
                  <div><span class="tk">地点</span><span class="tv">中国石油大学（华东）</span></div>
                  <div><span class="tk">首站</span><span class="tv">宿舍安顿</span></div>
                </div>
                <div class="ticket-row">
                  <div><span class="tk">必带</span><span class="tv">录取通知书 · 身份证 · 档案</span></div>
                </div>
              </div>
              <div class="ticket-stub">
                <span class="mono">08:00</span>
                <span>开始检票</span>
                <span>凭通知书入场</span>
              </div>
            </div>
          </div>
          <p class="qa-hint">
            不确定要带什么？<b>问一句"报到需要带什么"</b>，AI 会照着学生手册给你念一遍清单。
          </p>
        </div>
      </section>

      <!-- ===== 随身票据：行李牌 ===== -->
      <section id="stub" class="sec">
        <h2 class="sec-h serif">随身票据</h2>
        <p class="sec-p">四张行李牌，钉在宿舍门口就不会忘</p>
        <div class="stub-row">
          <div class="luggage"><span class="lg-hole"></span><b>报到时间</b><p>8 月下旬至 9 月初<br>以录取通知书为准</p></div>
          <div class="luggage"><span class="lg-hole"></span><b>学费与资助</b><p>线上缴费、绿色通道<br>贷款助学金同步受理</p></div>
          <div class="luggage"><span class="lg-hole"></span><b>学校地址</b><p>青岛市黄岛区<br>长江西路 66 号</p></div>
          <div class="luggage"><span class="lg-hole"></span><b>到校交通</b><p>青岛站/北站/机场<br>地铁直达校门口</p></div>
        </div>
      </section>

      <!-- ===== 地标贴图 ===== -->
      <section id="photos" class="sec">
        <h2 class="sec-h serif">地标贴图页</h2>
        <p class="sec-p">六处新生最常去的地方，都贴好了</p>
        <div class="photo-wall">
          <figure v-for="(spot, i) in landmarks" :key="i" class="polaroid" :class="'p' + (i + 1)">
            <img :src="spot.img" :alt="spot.name" @error="onImgError">
            <figcaption><b>{{ spot.name }}</b><span>{{ spot.desc }}</span></figcaption>
          </figure>
        </div>
      </section>

      <!-- ===== 备忘页 ===== -->
      <section id="memo" class="sec">
        <h2 class="sec-h serif">写在最后</h2>
        <div class="memo-box">
          <p>这本手账里的每一页，都能向 <b>AI 导览员</b>再问一句——它读过学生手册、培养方案和校园知识库。</p>
          <a class="btn-primary" @click="goChat">翻开手账，问第一个问题</a>
          <p class="memo-foot">中国石油大学（华东） · AI 数字人校园导览系统 · <span class="admin-link" @click="goAdmin">管理后台入口</span></p>
        </div>
      </section>

      <footer class="memo-footer">校园智导手账 · 2026 秋 · 青岛校区</footer>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
function goChat() { router.push('/visitor') }
function goGuide() { router.push('/guide') }
function goAdmin() { router.push('/login') }

const landmarks = [
  { name: '南门', desc: '报到第一站', img: '/images/campus/nanmen.jpg' },
  { name: '图书馆', desc: '借阅与自习', img: '/images/campus/tushuguan.jpg' },
  { name: '荟萃广场', desc: '社团招新', img: '/images/campus/huicui.jpg' },
  { name: '行政楼', desc: '办手续', img: '/images/campus/xingzheng.jpg' },
  { name: '体育馆', desc: '体测与赛事', img: '/images/campus/tiyuguan.jpg' },
  { name: '校史馆', desc: '学校沿革', img: '/images/campus/xiaoshiguan.jpg' },
]

function onImgError(e) {
  const el = e.target
  if (!el.dataset.fallback) {
    el.dataset.fallback = '1'
    el.src = '/images/campus_map.jpg'
  }
}
</script>

<style scoped>
/* ============================================
   校园智导 · 首页 — 方向 B「新生手账」
   纸白 × 靛蓝油墨 × 印泥红 · 票据结构
   ============================================ */

.home-memo {
  background: #F3EFE6;
  color: #2A3242;
  font-family: var(--font-sans);
  line-height: 1.7;
  -webkit-font-smoothing: antialiased;
  position: relative;
  min-height: 100vh;
}

/* 极淡纸面噪点网格 */
.home-memo::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  opacity: .5;
  background-image: radial-gradient(rgba(31, 58, 95, .05) 1px, transparent 1px);
  background-size: 22px 22px;
}

.serif { font-family: var(--font-song); }
.mono {
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  letter-spacing: .05em;
}

.page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 26px;
  position: relative;
  z-index: 1;
}

/* ===== 顶栏：手账页眉 ===== */
.topbar {
  padding: 20px 0 14px;
  border-bottom: 2px dashed rgba(31, 58, 95, .22);
  display: flex;
  align-items: baseline;
  gap: 14px;
}

.brand-seal {
  width: 44px; height: 44px;
  border: 2.5px solid #B5432A;
  border-radius: 6px;
  color: #B5432A;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 800;
  transform: rotate(-6deg);
  align-self: center;
  flex-shrink: 0;
}

.brand {
  font-size: 21px;
  font-weight: 700;
  color: #1F3A5F;
  letter-spacing: .04em;
}
.brand small {
  font-size: 12px;
  color: #7A8B99;
  font-weight: 400;
  margin-left: 8px;
  letter-spacing: .08em;
}

.topnav { margin-left: auto; display: flex; gap: 20px; }
.nl {
  font-size: 13px;
  color: #2A3242;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  padding-bottom: 2px;
  cursor: pointer;
}
.nl:hover { border-color: #1F3A5F; }
.nl.admin { color: #7A8B99; }

/* ===== Hero：手账摊开双页 ===== */
.hero {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  margin-top: 34px;
  background: #FBF9F3;
  border: 1px solid rgba(31, 58, 95, .22);
  box-shadow: 0 2px 14px rgba(31, 58, 95, .08);
  position: relative;
}
/* 中缝装订线 */
.hero::before {
  content: '';
  position: absolute;
  top: 0; bottom: 0;
  left: 41.6%;
  border-left: 2px dashed rgba(31, 58, 95, .22);
}

.hero-left {
  padding: 52px 44px 44px 30px;
  position: relative;
}
.date-line {
  font-size: 12.5px;
  color: #7A8B99;
  letter-spacing: .1em;
  margin-bottom: 22px;
}
.hero-title {
  font-size: clamp(32px, 3.4vw, 44px);
  font-weight: 800;
  color: #1F3A5F;
  line-height: 1.3;
  letter-spacing: .02em;
}
.hero-title .stamp {
  display: inline-block;
  color: #B5432A;
  border: 2px solid #B5432A;
  border-radius: 4px;
  padding: 0 6px;
  transform: rotate(-4deg);
  font-size: .55em;
  vertical-align: middle;
  margin-left: 8px;
  letter-spacing: .1em;
}
.hero-sub {
  margin-top: 20px;
  font-size: 14.5px;
  color: #57637A;
  max-width: 26em;
}
.hero-actions {
  margin-top: 34px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: fit-content;
}
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: #1F3A5F;
  color: #F5F1E6;
  font-size: 15px;
  padding: 13px 26px;
  border-radius: 4px;
  cursor: pointer;
  box-shadow: 2px 2px 0 #B5432A;
  transition: transform .2s, box-shadow .2s;
  width: fit-content;
}
.btn-primary:hover {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 #B5432A;
}
.btn-ghost {
  font-size: 13.5px;
  color: #1F3A5F;
  cursor: pointer;
  width: fit-content;
  border-bottom: 1px dashed #1F3A5F;
  padding-bottom: 2px;
}
.margin-note {
  position: absolute;
  left: -8px;
  bottom: 26px;
  transform: rotate(-90deg);
  transform-origin: left bottom;
  font-size: 11px;
  color: #7A8B99;
  letter-spacing: .24em;
}

/* 右页：报到检票口 */
.hero-right {
  padding: 52px 34px 44px 46px;
  display: flex;
  flex-direction: column;
}
.ticket-label {
  font-size: 12.5px;
  color: #7A8B99;
  letter-spacing: .16em;
  margin-bottom: 18px;
}
.ticket {
  background: #fff;
  border: 1.5px solid #1F3A5F;
  border-radius: 6px;
  position: relative;
  overflow: hidden;
}
.ticket::before, .ticket::after {
  content: '';
  position: absolute;
  width: 18px; height: 18px;
  border-radius: 50%;
  background: #F3EFE6;
  border: 1.5px solid #1F3A5F;
  top: 50%;
  transform: translateY(-50%);
}
.ticket::before { left: -10px; }
.ticket::after { right: -10px; }
.ticket-head {
  background: #1F3A5F;
  color: #F5F1E6;
  padding: 10px 18px;
  font-size: 13px;
  letter-spacing: .14em;
  display: flex;
  justify-content: space-between;
}
.ticket-body { display: flex; }
.ticket-main { flex: 1; padding: 18px 20px; }
.ticket-row { display: flex; gap: 22px; margin-bottom: 10px; }
.tk {
  font-size: 11px;
  color: #7A8B99;
  letter-spacing: .1em;
  display: block;
}
.tv { font-size: 13px; color: #2A3242; font-weight: 600; white-space: nowrap; }
.ticket-stub {
  width: 118px;
  border-left: 1.5px dashed #1F3A5F;
  padding: 18px 14px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  background: #F8F5EC;
}
.ticket-stub .mono { font-size: 20px; font-weight: 700; color: #B5432A; }
.ticket-stub span { font-size: 10.5px; color: #7A8B99; letter-spacing: .06em; }
.qa-hint {
  margin-top: 26px;
  font-size: 13.5px;
  color: #57637A;
  background: #F3EFE6;
  border-left: 3px solid #7A8B99;
  padding: 12px 16px;
}
.qa-hint b { color: #1F3A5F; }

@media (max-width: 880px) {
  .hero { grid-template-columns: 1fr; }
  .hero::before { display: none; }
  .hero-left { padding: 40px 26px 28px; }
  .hero-right { padding: 28px 26px 40px; }
  .margin-note { display: none; }
  .topnav { gap: 12px; }
  .brand small { display: none; }
}

/* ===== 正文区块 ===== */
.sec { margin-top: 88px; }
.sec-h {
  font-size: clamp(24px, 2.6vw, 30px);
  font-weight: 700;
  color: #1F3A5F;
  letter-spacing: .05em;
}
.sec-p {
  font-size: 13.5px;
  color: #7A8B99;
  margin: 8px 0 34px;
  letter-spacing: .04em;
}

/* 行李牌 */
.stub-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }
.luggage {
  background: #fff;
  border: 1.5px solid #1F3A5F;
  border-radius: 8px;
  padding: 22px 18px 18px;
  position: relative;
  box-shadow: 2px 3px 0 rgba(31, 58, 95, .12);
}
.lg-hole {
  position: absolute;
  top: -9px;
  left: 50%;
  transform: translateX(-50%);
  width: 16px; height: 16px;
  border-radius: 50%;
  background: #F3EFE6;
  border: 1.5px solid #1F3A5F;
}
.luggage b {
  display: block;
  font-size: 15px;
  color: #1F3A5F;
  letter-spacing: .06em;
  margin-bottom: 8px;
}
.luggage p { font-size: 13px; color: #57637A; line-height: 1.75; }
.stub-row .luggage:nth-child(2n) { transform: rotate(.8deg); }
.stub-row .luggage:nth-child(2n+1) { transform: rotate(-.6deg); }

/* 拍立得贴图墙 */
.photo-wall {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 34px 26px;
}
.polaroid {
  background: #fff;
  padding: 10px 10px 14px;
  box-shadow: 0 3px 12px rgba(31, 58, 95, .14);
  border: 1px solid rgba(31, 58, 95, .08);
  transition: transform .3s;
}
.polaroid img {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  background: #D8DFE6;
  display: block;
}
.polaroid figcaption {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 10px 4px 2px;
}
.polaroid figcaption b { font-size: 15px; color: #2A3242; letter-spacing: .05em; }
.polaroid figcaption span { font-size: 11.5px; color: #7A8B99; }
.p1 { transform: rotate(-2.2deg); }
.p2 { transform: rotate(1.4deg); }
.p3 { transform: rotate(-1deg); }
.p4 { transform: rotate(1.8deg); }
.p5 { transform: rotate(-1.5deg); }
.p6 { transform: rotate(.9deg); }
.polaroid:hover { transform: rotate(0) scale(1.03); }

/* 备忘页 */
.memo-box {
  border: 2px dashed rgba(31, 58, 95, .22);
  border-radius: 10px;
  padding: 44px 40px;
  display: flex;
  flex-direction: column;
  gap: 22px;
  align-items: flex-start;
  background: #FBF9F3;
}
.memo-box p { font-size: 15px; color: #57637A; }
.memo-box b { color: #1F3A5F; }
.memo-foot {
  font-size: 11.5px !important;
  color: #7A8B99 !important;
  margin-top: 8px;
}
.admin-link { cursor: pointer; border-bottom: 1px dashed #7A8B99; }
.admin-link:hover { color: #1F3A5F; border-color: #1F3A5F; }

.memo-footer {
  margin-top: 80px;
  padding: 26px 0 34px;
  border-top: 2px dashed rgba(31, 58, 95, .22);
  font-size: 12px;
  color: #7A8B99;
  letter-spacing: .05em;
}

@media (max-width: 880px) {
  .stub-row { grid-template-columns: 1fr 1fr; }
  .photo-wall { grid-template-columns: 1fr 1fr; }
  .memo-box { padding: 32px 24px; }
}
</style>
