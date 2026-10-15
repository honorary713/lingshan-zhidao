import request from './request'

// API 密钥
export function getApiKeys(params) {
  return request.get('/system/api-keys', { params })
}

export function createApiKey(data) {
  return request.post('/system/api-keys', data)
}

export function updateApiKey(id, data) {
  return request.put(`/system/api-keys/${id}`, data)
}

export function deleteApiKey(id) {
  return request.delete(`/system/api-keys/${id}`)
}

// 系统配置
export function getSystemConfigs() {
  return request.get('/system/configs')
}

export function updateSystemConfigs(configs) {
  return request.put('/system/configs', { configs })
}

// 操作日志
export function getLogs(params) {
  return request.get('/logs', { params })
}
