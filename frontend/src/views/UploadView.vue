<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiError, http } from '../api/http'

const router = useRouter()
const selectedFile = ref(null)
const customName = ref('')
const error = ref('')
const loading = ref(false)
function chooseFile(event) { selectedFile.value = event.target.files[0] || null }
async function submit() {
  error.value = ''
  if (!selectedFile.value) { error.value = '请选择文件'; return }
  const data = new FormData(); data.append('file', selectedFile.value); data.append('customName', customName.value)
  loading.value = true
  try { await http.post('/files', data); router.push('/files') } catch (err) { error.value = apiError(err) } finally { loading.value = false }
}
</script>

<template>
  <form class="surface upload-card" @submit.prevent="submit"><h1 class="page-heading">上传文件</h1><p class="muted">选择文件并保存到你的个人空间。</p><p class="form-error">{{ error }}</p><label class="drop-zone"><strong>{{ selectedFile ? selectedFile.name : '选择要上传的文件' }}</strong><span class="muted">支持任意常见文件格式</span><input type="file" required @change="chooseFile" /></label><div class="field"><label for="custom-name">可选新文件名</label><input id="custom-name" v-model="customName" placeholder="留空则使用原文件名" /></div><button class="button button-primary" :disabled="loading">{{ loading ? '上传中...' : '确认上传' }}</button></form>
</template>
