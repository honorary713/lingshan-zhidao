import request from './request'

// FAQ
export function getFaqs(params) {
  return request.get('/faqs', { params })
}

export function createFaq(data) {
  return request.post('/faqs', data)
}

export function updateFaq(id, data) {
  return request.put(`/faqs/${id}`, data)
}

export function deleteFaq(id) {
  return request.delete(`/faqs/${id}`)
}

// 新增：同步FAQ向量知识库
export function rebuildFaqIndex() {
  return request.post('/faqs/rebuild-index')
}

// 未解决问题
export function getUnresolvedQuestions(params) {
  return request.get('/unresolved-questions', { params })
}

export function resolveQuestion(id, data) {
  return request.put(`/unresolved-questions/${id}/resolve`, data)
}

export function ignoreQuestion(id) {
  return request.put(`/unresolved-questions/${id}/ignore`)
}

export function deleteUnresolvedQuestion(id) {
  return request.delete(`/unresolved-questions/${id}`)
}

// 全局知识库（原有景区文档向量）
export function rebuildKnowledgeBase() {
  return request.post('/knowledge-base/rebuild')
}

export function getKnowledgeBaseStatus() {
  return request.get('/knowledge-base/status')
}