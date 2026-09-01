import axios from 'axios'

export const http = axios.create({ baseURL: '/api', withCredentials: true })

let csrfToken = ''

http.interceptors.request.use(async (config) => {
  if (!csrfToken && !config.url?.endsWith('/csrf')) {
    const response = await http.get('/csrf')
    csrfToken = response.data.csrf_token
  }
  if (csrfToken && ['post', 'put', 'patch', 'delete'].includes(config.method)) {
    config.headers['X-CSRF-Token'] = csrfToken
  }
  return config
})

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
