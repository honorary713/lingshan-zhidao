<template>
  <div class="page-container">
    <PageHeader title="游客感受度报告">
      <el-radio-group v-model="period" @change="loadAll">
        <el-radio-button value="daily">今日</el-radio-button>
        <el-radio-button value="weekly">本周</el-radio-button>
        <el-radio-button value="monthly">本月</el-radio-button>
      </el-radio-group>
      <el-button type="primary" style="margin-left:12px" @click="loadAll" :loading="loading">
        刷新数据
      </el-button>
    </PageHeader>

    <!-- 核心指标 -->
    <div class="stats-cards">
      <StatsCard :icon="ChatDotRound" bg-color="rgba(196,84,62,0.85)" :value="data.total_questions" label="提问总数" />
      <StatsCard :icon="Star" bg-color="rgba(90,158,111,0.85)" :value="data.avg_rating + '分'" label="平均评分" />
      <StatsCard :icon="TrendCharts" bg-color="rgba(196,155,76,0.85)" :value="data.positive_rate + '%'" label="好评率" />
      <StatsCard :icon="Warning" bg-color="rgba(196,84,62,0.9)" :value="data.pending_unresolved" label="待解决问题" />
    </div>

    <!-- 图表区 -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="12">
        <el-card>
          <template #header>情感趋势（近30天评分走势）</template>
          <div ref="trendChartRef" style="height:300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>评分分布</template>
          <div ref="pieChartRef" style="height:300px"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 关注点 + AI报告 -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="10">
        <el-card>
          <template #header>🔥 游客关注点 TOP8</template>
          <div v-if="data.hot_questions && data.hot_questions.length" style="max-height:340px;overflow-y:auto">
            <div v-for="(h, i) in data.hot_questions" :key="i"
              style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #f0f0f0">
              <span style="color:#909399;width:24px">{{ i + 1 }}.</span>
              <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ h.question }}</span>
              <el-tag size="small" type="primary">{{ h.count }}次</el-tag>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      <el-col :span="14">
        <el-card>
          <template #header>🤖 AI 智能分析</template>
          <div v-loading="aiLoading">
            <!-- 游客关注点分析 -->
            <div style="margin-bottom:16px">
              <h4 style="color:#409EFF;margin:0 0 6px 0">📋 游客关注点分析</h4>
              <p style="color:#606266;line-height:1.8;white-space:pre-wrap">{{ aiResult.analysis }}</p>
            </div>
            <!-- 情感趋势总结 -->
            <div style="margin-bottom:16px">
              <h4 style="color:#67C23A;margin:0 0 6px 0">📈 情感趋势总结</h4>
              <p style="color:#606266;line-height:1.8;white-space:pre-wrap">{{ aiResult.sentiment }}</p>
            </div>
            <!-- 服务建议 -->
            <div>
              <h4 style="color:#E6A23C;margin:0 0 6px 0">💡 服务改进建议</h4>
              <ul style="color:#606266;line-height:2;padding-left:16px">
                <li v-for="(s, i) in aiResult.suggestions" :key="i">{{ s }}</li>
              </ul>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { ChatDotRound, Star, TrendCharts, Warning } from '@element-plus/icons-vue'
import PageHeader from '../components/PageHeader.vue'
import StatsCard from '../components/StatsCard.vue'
import { getReportAnalysis } from '../api/report'

const period = ref('daily')
const loading = ref(false)
const aiLoading = ref(false)

const data = reactive({
  total_questions: 0, avg_rating: 0, positive_rate: 0, pending_unresolved: 0,
  hot_questions: [], rating_dist: { excellent: 0, good: 0, fair: 0, poor: 0 },
  sentiment_trend: []
})

const aiResult = reactive({
  analysis: '请先点击"刷新数据"生成报告',
  sentiment: '',
  suggestions: []
})

const trendChartRef = ref(null)
const pieChartRef = ref(null)

let trendChart = null
let pieChart = null

onMounted(() => loadAll())

function handleResize() {
  try { trendChart?.resize() } catch (e) { /* ignore */ }
  try { pieChart?.resize() } catch (e) { /* ignore */ }
}
window.addEventListener('resize', handleResize)

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  try { trendChart?.dispose() } catch (e) { /* ignore */ }
  try { pieChart?.dispose() } catch (e) { /* ignore */ }
  trendChart = null
  pieChart = null
})

async function loadAll() {
  loading.value = true
  aiLoading.value = true
  try {
    const res = await getReportAnalysis(period.value)
    // 填充统计数据
    Object.assign(data, res.data)
    renderCharts()
    // 填充 AI 分析
    Object.assign(aiResult, res.ai)
  } catch {
    // 静默处理
  }
  loading.value = false
  aiLoading.value = false
}

function renderCharts() {
  // 情感趋势折线图
  if (trendChartRef.value && data.sentiment_trend && data.sentiment_trend.length > 0) {
    if (!trendChart) {
      const existing = echarts.getInstanceByDom(trendChartRef.value)
      trendChart = existing || echarts.init(trendChartRef.value)
    }
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 45, right: 20, top: 20, bottom: 35 },
      xAxis: { type: 'category', data: data.sentiment_trend.map(t => t.date.slice(5)), axisLabel: { rotate: 45, fontSize: 10 } },
      yAxis: { type: 'value', min: 0, max: 5 },
      series: [{
        name: '平均评分', type: 'line', data: data.sentiment_trend.map(t => t.avg_rating),
        smooth: true, itemStyle: { color: '#b8943c' }, lineStyle: { width: 2 }
      }]
    })
  }

  // 评分分布饼图
  if (pieChartRef.value) {
    if (!pieChart) {
      const existing = echarts.getInstanceByDom(pieChartRef.value)
      pieChart = existing || echarts.init(pieChartRef.value)
    }
    const d = data.rating_dist
    const pieData = [
      { value: d.excellent, name: '好评(5分)', itemStyle: { color: '#5a9e6f' } },
      { value: d.good, name: '较好(4分)', itemStyle: { color: '#c49b4c' } },
      { value: d.fair, name: '一般(3分)', itemStyle: { color: '#d4953c' } },
      { value: d.poor, name: '差评(1-2分)', itemStyle: { color: '#c4543e' } }
    ]
    pieChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c}条 ({d}%)' },
      legend: { orient: 'vertical', right: 10, top: 'center', itemGap: 16, textStyle: { fontSize: 13 } },
      series: [{
        type: 'pie', radius: ['50%', '75%'], center: ['35%', '50%'],
        label: { show: true, fontSize: 11, formatter: '{b}\n{d}%' },
        data: pieData
      }]
    })
  }
}
</script>
