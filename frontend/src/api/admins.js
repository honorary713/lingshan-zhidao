import request from './request'

export function getAdmins(params) {
  return request.get('/admins', { params })
}

export function createAdmin(data) {
  return request.post('/admins', data)
}

export function updateAdmin(id, data) {
  return request.put(`/admins/${id}`, data)
}

export function deleteAdmin(id) {
  return request.delete(`/admins/${id}`)
}

export function resetPassword(id, newPassword) {
  return request.put(`/admins/${id}/password`, { new_password: newPassword })
}
