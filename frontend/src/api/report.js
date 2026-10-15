import request from './request'

// 获取报告统计数据
export function getReportData(period = 'daily') {
  return request.get('/report/data', { params: { period } })
}

// 获取 AI 分析报告
export function getReportAnalysis(period = 'daily') {
  return request.get('/report/analysis', { params: { period } })
}
