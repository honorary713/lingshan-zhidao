import request from './request'

export function getOverview(period = 'daily') {
  return request.get('/stats/overview', { params: { period } })
}

export function getHotQuestions(limit = 20) {
  return request.get('/stats/hot-questions', { params: { limit } })
}

export function getAccuracy(period = 'daily') {
  return request.get('/stats/accuracy', { params: { period } })
}


export function getSatisfaction(days = 30) {
  return request.get('/stats/satisfaction', { params: { days } })
}
export function tapVisitor() {
  return request.post('/stats/visitor-tap')
}

export function getVisitorCounts() {
  return request.get('/stats/visitor-counts')
}
