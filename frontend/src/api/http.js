import axios from 'axios'

export const http = axios.create({ baseURL: '/api', withCredentials: true })

export async function getCurrentUser() {
  try {
    const { data } = await http.get('/me')
    return data.user
  } catch {
    return null
  }
}

export async function logout() {
  await http.post('/logout')
}

export function apiError(error, fallback = '操作失败，请稍后重试') {
  return error?.response?.data?.error || fallback
}
