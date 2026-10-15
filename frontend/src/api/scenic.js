import request from './request'

// 景区
export function getScenicAreas(params) {
  return request.get('/scenic-areas', { params })
}

export function createScenicArea(data) {
  return request.post('/scenic-areas', data)
}

export function updateScenicArea(id, data) {
  return request.put(`/scenic-areas/${id}`, data)
}

export function deleteScenicArea(id) {
  return request.delete(`/scenic-areas/${id}`)
}

// 景点
export function getScenicSpots(params) {
  return request.get('/scenic-spots', { params })
}

export function createScenicSpot(data) {
  return request.post('/scenic-spots', data)
}

export function updateScenicSpot(id, data) {
  return request.put(`/scenic-spots/${id}`, data)
}

export function deleteScenicSpot(id) {
  return request.delete(`/scenic-spots/${id}`)
}
