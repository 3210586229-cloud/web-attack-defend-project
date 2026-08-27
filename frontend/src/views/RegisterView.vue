<script setup>
import { reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { apiError, http } from '../api/http'

const router = useRouter()
const form = reactive({ username: '', password: '', confirm_password: '' })
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  if (form.password !== form.confirm_password) { error.value = '两次密码不一致'; return }
  loading.value = true
  try { await http.post('/register', form); router.push('/login') }
  catch (err) { error.value = apiError(err, '注册失败') }
  finally { loading.value = false }
}
</script>

<template>
  <form class="surface form-card" @submit.prevent="submit">
    <h1>创建账号</h1><p>注册后即可开始管理文件</p>
    <p class="form-error">{{ error }}</p>
    <div class="field"><label for="username">用户名</label><input id="username" v-model.trim="form.username" required autocomplete="username" /></div>
    <div class="field"><label for="password">密码</label><input id="password" v-model="form.password" required type="password" autocomplete="new-password" /></div>
    <div class="field"><label for="confirm-password">确认密码</label><input id="confirm-password" v-model="form.confirm_password" required type="password" autocomplete="new-password" /></div>
    <button class="button button-primary" :disabled="loading">{{ loading ? '注册中...' : '注册' }}</button>
    <p class="form-footer">已经有账号？<RouterLink to="/login">返回登录</RouterLink></p>
  </form>
</template>
