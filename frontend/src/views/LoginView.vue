<script setup>
import { reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { apiError, http } from '../api/http'

const router = useRouter()
const form = reactive({ username: '', password: '' })
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await http.post('/login', form)
    router.push('/profile')
  } catch (err) {
    error.value = apiError(err, '用户名或密码错误')
  } finally { loading.value = false }
}
</script>

<template>
  <form class="surface form-card" @submit.prevent="submit">
    <h1>欢迎回来</h1><p>登录你的个人网盘</p>
    <p class="form-error">{{ error }}</p>
    <div class="field"><label for="username">用户名</label><input id="username" v-model.trim="form.username" required autocomplete="username" /></div>
    <div class="field"><label for="password">密码</label><input id="password" v-model="form.password" required type="password" autocomplete="current-password" /></div>
    <button class="button button-primary" :disabled="loading">{{ loading ? '登录中...' : '登录' }}</button>
    <p class="form-footer">还没有账号？<RouterLink to="/register">立即注册</RouterLink></p>
  </form>
</template>
