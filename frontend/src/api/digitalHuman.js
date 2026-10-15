import request from './request'

export function getConfig() {
  return request.get('/digital-human/config')
}

export function updateConfig(data) {
  return request.put('/digital-human/config', data)
}

// 敏感词
export function getSensitiveWords(params) {
  return request.get('/sensitive-words', { params })
}

export function addSensitiveWord(data) {
  return request.post('/sensitive-words', data)
}

export function updateSensitiveWord(id, data) {
  return request.put(`/sensitive-words/${id}`, data)
}

export function deleteSensitiveWord(id) {
  return request.delete(`/sensitive-words/${id}`)
}

export function batchImportSensitiveWords(data) {
  return request.post('/sensitive-words/batch', data)
}
