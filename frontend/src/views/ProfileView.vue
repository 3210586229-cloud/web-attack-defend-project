<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { getCurrentUser, http } from '../api/http'

const username = ref('')
const files = ref([])
onMounted(async () => {
  const user = await getCurrentUser()
  username.value = user?.username || ''
  try { files.value = (await http.get('/files')).data.files.slice(0, 4) } catch { files.value = [] }
})
</script>

<template>
  <div class="dashboard">
    <aside class="sidebar">
      <div class="surface side-card"><h3>文件空间</h3><div class="side-links"><RouterLink class="router-link-active" to="/profile">概览</RouterLink><RouterLink to="/files">全部文件</RouterLink><RouterLink to="/upload">上传文件</RouterLink></div></div>
      <div class="surface side-card"><h3>空间使用</h3><strong>42.6 GB</strong><div class="progress-bar"><span /></div><small class="muted">已使用 42%</small></div>
    </aside>
    <section class="content-stack">
      <div class="surface welcome-panel"><h2>{{ username }} 的个人网盘</h2><p class="muted">集中管理你的课程资料、图片、视频和个人文件。</p><div class="hero-actions"><RouterLink class="button button-primary" to="/upload">开始上传</RouterLink><RouterLink class="button button-light" to="/files">查看全部文件</RouterLink></div></div>
      <div class="surface" style="padding: 20px"><div class="toolbar"><h2>最近文件</h2><RouterLink class="button button-light" to="/files">查看全部</RouterLink></div><div v-if="files.length" class="table-wrap"><table class="file-table"><thead><tr><th>名称</th><th>大小</th></tr></thead><tbody><tr v-for="file in files" :key="file.name"><td class="file-name">{{ file.name }}</td><td>{{ formatSize(file.size) }}</td></tr></tbody></table></div><div v-else class="empty-state">还没有上传文件</div></div>
    </section>
  </div>
</template>

<script>
export default { methods: { formatSize(bytes) { if (!bytes) return '0 B'; const units = ['B', 'KB', 'MB', 'GB']; const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1); return `${(bytes / 1024 ** index).toFixed(index ? 1 : 0)} ${units[index]}` } } }
</script>
