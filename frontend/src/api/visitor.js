import axios from 'axios'
// baseURL 固定 /api，配合vite代理转发到 127.0.0.1:8000
const request = axios.create({
  baseURL: '/api'
})

// 问答接口
export function sendQuestion(data) {
  return request.post('/chat', data)
}

// 后端暂无打分接口，注释停用
 export function submitStarScore(data) {
  return request.post('/chat/score', data)
 }