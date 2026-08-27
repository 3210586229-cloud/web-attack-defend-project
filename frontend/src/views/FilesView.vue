<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { apiError, http } from '../api/http'

const files = ref([])
const error = ref('')
const loading = ref(true)
const formatSize = (bytes) => { if (!bytes) return '0 B'; const units = ['B', 'KB', 'MB', 'GB']; const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), 3); return `${(bytes / 1024 ** i).toFixed(i ? 1 : 0)} ${units[i]}` }
async function loadFiles() { loading.value = true; try { files.value = (await http.get('/files')).data.files } catch (err) { error.value = apiError(err) } finally { loading.value = false } }
async function removeFile(file) { if (!window.confirm(`确定删除“${file.name}”吗？`)) return; try { await http.delete(`/files/${encodeURIComponent(file.name)}`); await loadFiles() } catch (err) { error.value = apiError(err) } }
onMounted(loadFiles)
</script>

<template>
  <section class="surface" style="padding: 24px"><div class="toolbar"><div><h1 class="page-heading">我的文件</h1><span class="muted">管理你上传的全部文件</span></div><RouterLink class="button button-primary" to="/upload">上传文件</RouterLink></div><p class="form-error">{{ error }}</p><div v-if="loading" class="empty-state">正在加载...</div><div v-else-if="!files.length" class="empty-state">当前还没有上传文件</div><div v-else class="table-wrap"><table class="file-table"><thead><tr><th>文件名</th><th>大小</th><th>更新时间</th><th>操作</th></tr></thead><tbody><tr v-for="file in files" :key="file.name"><td class="file-name">{{ file.name }}</td><td>{{ formatSize(file.size) }}</td><td>{{ new Date(file.updated_at * 1000).toLocaleString() }}</td><td><div class="row-actions"><a :href="`/api/files/${encodeURIComponent(file.name)}/download`">下载</a><button type="button" @click="removeFile(file)">删除</button></div></td></tr></tbody></table></div></section>
</template>
