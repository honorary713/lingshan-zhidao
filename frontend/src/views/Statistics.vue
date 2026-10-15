<template>
  <div class="page-container">
    <PageHeader title="数据统计">
      <el-radio-group v-model="period" @change="loadAll">
        <el-radio-button value="daily">今日</el-radio-button>
        <el-radio-button value="weekly">本周</el-radio-button>
        <el-radio-button value="monthly">本月</el-radio-button>
      </el-radio-group>
    </PageHeader>

    <div class="stats-cards">
      <StatsCard :icon="ChatDotRound" bg-color="rgba(196,84,62,0.85)" :value="overview.total_questions" label="提问总数" />
      <StatsCard :icon="UserFilled" bg-color="rgba(90,158,111,0.85)" :value="overview.total_sessions" label="会话数" />
      <StatsCard :icon="Star" bg-color="rgba(196,155,76,0.85)" :value="overview.avg_rating+'分'" label="平均评分" />
      <StatsCard :icon="TrendCharts" bg-color="rgba(107,101,96,0.75)" :value="overview.positive_rate+'%'" label="好评率" />
    </div>

    <el-row :gutter="20" style="margin-top:20px">
      <el-col :span="14">
        <el-card><template #header>满意度趋势（近30天）</template><div ref="trendChartRef" style="height:340px"></div></el-card>
      </el-col>
      <el-col :span="10">
        <el-card><template #header>热门问题 TOP 15</template>
          <div v-if="hotQuestions.length" style="max-height:340px;overflow-y:auto">
            <div v-for="(h, i) in hotQuestions" :key="i" style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f0f0f0">
              <span style="color:#909399;margin-right:8px">{{ i+1 }}.</span>
              <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ h.question }}</span>
              <el-tag size="small">{{ h.count }}次</el-tag>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { ChatDotRound, UserFilled, Star, TrendCharts } from '@element-plus/icons-vue'
import PageHeader from '../components/PageHeader.vue'
import StatsCard from '../components/StatsCard.vue'
import { getOverview, getHotQuestions, getSatisfaction } from '../api/stats'

const period = ref('daily')
const overview = reactive({ total_questions: 0, total_sessions: 0, avg_rating: 0, positive_rate: 0 })
const hotQuestions = ref([])
const trendChartRef = ref(null)

let trendChartInstance = null

onMounted(() => loadAll())

function handleResize() {
  try { trendChartInstance?.resize() } catch (e) { /* ignore */ }
}
window.addEventListener('resize', handleResize)

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  try { trendChartInstance?.dispose() } catch (e) { /* ignore */ }
  trendChartInstance = null
})

async function loadAll() {
  try { Object.assign(overview, await getOverview(period.value)) } catch (e) { console.error('加载概览数据失败:', e) }
  try { hotQuestions.value = await getHotQuestions(15) } catch (e) { console.error('加载热门问题失败:', e) }

  try {
    const trend = await getSatisfaction(30)
    if (trendChartRef.value) {
      if (!trendChartInstance) {
        const existing = echarts.getInstanceByDom(trendChartRef.value)
        trendChartInstance = existing || echarts.init(trendChartRef.value)
      }
      trendChartInstance.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: 40, right: 40, top: 20, bottom: 30 },
        xAxis: { type: 'category', data: trend.map(t => t.date.slice(5)), axisLabel: { rotate: 45, fontSize: 10 } },
        yAxis: { type: 'value', min: 0, max: 5 },
        series: [
          { name: '平均评分', type: 'line', data: trend.map(t => t.avg_rating), smooth: true, itemStyle: { color: '#b8943c' } },
          { name: '问题数', type: 'bar', data: trend.map(t => t.question_count), itemStyle: { color: 'rgba(184,148,60,0.15)' }, yAxisIndex: 0 }
        ]
      })
    }
  } catch (e) { console.error('加载满意度趋势失败:', e) }
}
</script>
