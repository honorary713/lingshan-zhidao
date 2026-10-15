import request from './request'

export function getBlacklist(params) {
  return request.get('/blacklist', { params })
}

export function addBlacklist(data) {
  return request.post('/blacklist', data)
}

export function removeBlacklist(id) {
  return request.delete(`/blacklist/${id}`)
}
