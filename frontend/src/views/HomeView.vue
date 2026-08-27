<template>
  <section class="hero">
    <div class="hero-copy">
      <h1>你的文件，随时可取</h1>
      <p>集中管理图片、视频、文档和学习资料，支持快速搜索、分类浏览和一键上传。</p>
      <div class="hero-actions">
        <RouterLink class="button button-primary" to="/upload">开始上传</RouterLink>
        <RouterLink class="button button-light" to="/login">登录后管理文件</RouterLink>
      </div>
    </div>
    <div class="stats-panel" aria-label="网盘概览">
      <div class="stat"><strong>42.6 GB</strong><span>可用空间</span></div>
      <div class="stat"><strong>24 / 7</strong><span>随时访问</span></div>
      <div class="stat"><strong>安全</strong><span>个人文件隔离存储</span></div>
    </div>
  </section>
  <section class="surface welcome-panel" style="margin-top: 22px">
    <h2>从这里开始</h2>
    <p class="muted">登录后可以上传、下载和管理属于你的文件。</p>
    <div class="hero-actions">
      <RouterLink class="button button-primary" to="/register">创建账号</RouterLink>
      <RouterLink class="button button-light" to="/login">已有账号，直接登录</RouterLink>
    </div>
  </section>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>
