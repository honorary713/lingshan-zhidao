<template>
  <div class="page-container">
    <PageHeader title="数据大屏">
      <el-button type="success" :icon="UserFilled" @click="handleTapVisitor" :loading="tapping">
        模拟进人 +1
      </el-button>
      <el-radio-group v-model="period" @change="loadAll" style="margin-left:12px">
        <el-radio-button value="daily">今日</el-radio-button>
        <el-radio-button value="weekly">本周</el-radio-button>
      </el-radio-group>
    </PageHeader>

    <!-- ===== 核心指标卡片 ===== -->
    <div class="stats-cards">
      <StatsCard :icon="UserFilled" bg-color="rgba(196,84,62,0.85)"
        :value="period === 'daily' ? overview.today_visitors : overview.week_visitors"
        :label="period === 'daily' ? '今日来访人次' : '本周来访人次'" />
      <StatsCard :icon="ChatDotRound" bg-color="rgba(90,158,111,0.85)"
        :value="overview.today_questions" label="今日提问数" />
      <StatsCard :icon="Star" bg-color="rgba(196,155,76,0.85)"
        :value="overview.avg_rating + '分'" label="平均评分" />
      <StatsCard :icon="DataLine" bg-color="rgba(107,101,96,0.75)"
        :value="overview.positive_rate + '%'" label="好评率" />
    </div>

    <!-- ===== 图表区域 ===== -->
    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="14">
        <el-card>
          <template #header>满意度趋势（近30天）</template>
          <div ref="trendChartRef" style="height:340px"></div>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card>
          <template #header>评分分布</template>
          <div ref="pieChartRef" style="height:340px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="14">
        <el-card>
          <template #header>热门问题 TOP 10</template>
          <div ref="hotChartRef" style="height:320px"></div>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card>
          <template #header>待处理问题</template>
          <div style="text-align:center;padding:40px 0">
            <div style="font-size:48px;color:#c45656;font-weight:bold">{{ overview.pending_unresolved }}</div>
            <div style="color:#909399;margin-top:8px">个待处理问题</div>
            <el-button type="primary" style="margin-top:16px" @click="$router.push('/admin/unresolved-questions')">去处理</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Star, UserFilled, DataLine } from '@element-plus/icons-vue'
import PageHeader from '../components/PageHeader.vue'
import StatsCard from '../components/StatsCard.vue'
import { getOverview, getHotQuestions, getAccuracy, getSatisfaction, tapVisitor } from '../api/stats'

const period = ref('daily')
const router = useRouter()
const tapping = ref(false)

const overview = reactive({
  today_visitors: 0, week_visitors: 0,
  today_questions: 0, avg_rating: 0, positive_rate: 0, pending_unresolved: 0
})

const trendChartRef = ref(null)
const pieChartRef = ref(null)
const hotChartRef = ref(null)

// 记录三个 chart 实例，用于 resize 和 dispose
const chartInstances = []

onMounted(() => loadAll())

// 窗口缩放时同步调整图表尺寸
function handleResize() {
  chartInstances.forEach(c => {
    try { c.resize() } catch (e) { /* ignore */ }
  })
}
window.addEventListener('resize', handleResize)

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstances.forEach(c => {
    try { c.dispose() } catch (e) { /* ignore */ }
  })
  chartInstances.length = 0
})

/** 安全地初始化 ECharts（先检查已有实例，避免重复创建） */
function initChart(domRef) {
  if (!domRef.value) return null
  let instance = echarts.getInstanceByDom(domRef.value)
  if (!instance) {
    instance = echarts.init(domRef.value)
  }
  chartInstances.push(instance)
  return instance
}

async function loadAll() {
  // 概览数据
  try {
    const data = await getOverview(period.value)
    Object.assign(overview, data)
  } catch (e) { console.error('加载概览数据失败:', e) }

  // 满意度趋势
  try {
    const trend = await getSatisfaction(30)
    if (trendChartRef.value) {
      const chart = initChart(trendChartRef)
      if (!chart) return
      chart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: 45, right: 20, top: 20, bottom: 35 },
        xAxis: { type: 'category', data: trend.map(t => t.date.slice(5)), axisLabel: { rotate: 45, fontSize: 10 } },
        yAxis: { type: 'value', min: 0, max: 5 },
        series: [
          { name: '平均评分', type: 'line', data: trend.map(t => t.avg_rating), smooth: true,
            itemStyle: { color: '#b8943c' }, lineStyle: { width: 2 } },
          { name: '问题数', type: 'bar', data: trend.map(t => t.question_count),
            itemStyle: { color: 'rgba(184,148,60,0.15)' } }
        ]
      })
    }
  } catch (e) { console.error('加载满意度趋势失败:', e) }

  // 评分分布饼图
 try {
  const acc = await getAccuracy(period.value)
  if (pieChartRef.value) {
    const chart = initChart(pieChartRef)
    if (!chart) return
    const rawPieData = [
      { value: acc.excellent, name: '好评(5分)', itemStyle: { color: '#5a9e6f' } },
      { value: acc.good, name: '较好(4分)', itemStyle: { color: '#c49b4c' } },
      { value: acc.fair, name: '一般(3分)', itemStyle: { color: '#d4953c' } },
      { value: acc.poor, name: '差评(1-2分)', itemStyle: { color: '#c4543e' } },
    ]

    const pieData = rawPieData.filter(d => d.value > 0)
    const totalRated = (acc.excellent || 0) + (acc.good || 0) + (acc.fair || 0) + (acc.poor || 0)

    if (!pieData.length) {
      // 空状态：显示提示文字
      chart.setOption({
        title: {
          text: '暂无评分数据',
          left: 'center',
          top: 'center',
          textStyle: { color: '#909399', fontSize: 14 }
        },
        series: []
      })
      return
    }

        chart.setOption({
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c}条 ({d}%)'
      },
      legend: {
        orient: 'vertical',
        right: '3%',
        top: 'center',
        itemGap: 16,
        textStyle: { fontSize: 12 },
        formatter: name => {
          const item = rawPieData.find(d => d.name === name)
          const pct = totalRated ? ((item.value / totalRated) * 100).toFixed(0) : 0
          return `${name}  ${item.value}条(${pct}%)`
        }
      },
      title: {
        text: `${totalRated}`,
        subtext: '评分总数',
        left: '35%',                    // 与饼图 center[0] 一致
        top: 'center',
        textAlign: 'center',            // 文字在该 X 位置水平居中
        textVerticalAlign: 'middle',    // 文字在该 Y 位置垂直居中
        textStyle: { fontSize: 26, fontWeight: 'bold', color: '#303133' },
        subtextStyle: { fontSize: 13, color: '#909399' }
      },
      series: [{
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['35%', '50%'],         // 与 title.left 一致
        avoidLabelOverlap: true,
        label: { show: false },         // 去掉外部标签 → 不再截断
        labelLine: { show: false },     // 去掉引导线
        data: pieData
      }]
     })

    // 点击饼图扇区 → 跳转对话记录并按评分筛选
    chart.on('click', (params) => {
      const ratingMap = {
        '好评(5分)': 'good',
        '较好(4分)': 'good',
        '一般(3分)': 'fair',
        '差评(1-2分)': 'poor'
      }
      const rating = ratingMap[params.name]
      if (rating) {
        router.push({ path: '/admin/conversations', query: { rating } })
      }
    })

  }

} catch (e) { console.error('加载评分分布失败:', e) }

  // 热门问题
  try {
    const hot = await getHotQuestions(10)
    if (hotChartRef.value && hot.length > 0) {
      const chart = initChart(hotChartRef)
      if (!chart) return
        const reversedHot = hot.slice().reverse()
      chart.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          formatter: params => {
            const item = reversedHot[params[0].dataIndex]
            return `${item.question}<br/>提问次数: ${params[0].value}`
          }
        },
        grid: { left: 5, right: 25, top: 10, bottom: 5, containLabel: true },
        xAxis: { type: 'value' },
        yAxis: {
          type: 'category',
          data: reversedHot.map(h => h.question.length > 15 ? h.question.slice(0, 15) + '...' : h.question),
          axisLabel: { fontSize: 11 }
        },
        series: [{
          type: 'bar',
          data: reversedHot.map(h => h.count),
          itemStyle: { color: '#b8943c', borderRadius: [0, 4, 4, 0] },
          emphasis: { itemStyle: { color: '#c9a64d' } },
          cursor: 'pointer'
        }]
      })
      // 点击柱子 → 跳转对话记录并按问题关键词筛选
      chart.on('click', (params) => {
        const item = reversedHot[params.dataIndex]
        if (item) {
          router.push({ path: '/admin/conversations', query: { keyword: item.question } })
        }
      })
    }
  } catch (e) { console.error('加载热门问题失败:', e) }
}


async function handleTapVisitor() {
  tapping.value = true
  try {
    const data = await tapVisitor()
   ElMessage.success(`今日已接待 ${data.today_visitors} 人`)
    // 刷新当前数据
    await loadAll()
  } catch {
    ElMessage.error('操作失败')
  }
  tapping.value = false
}
</script>
