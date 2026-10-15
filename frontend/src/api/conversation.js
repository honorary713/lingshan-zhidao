import request from './request'

export function getConversations(params) {
  return request.get('/conversations', { params })
}

export function getConversationDetail(id) {
  return request.get(`/conversations/${id}`)
}


export function moveToPending(convId) {
  return request.post(`/conversations/move-pending/${convId}`)
}