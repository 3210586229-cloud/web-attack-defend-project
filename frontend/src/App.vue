<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { ref } from 'vue'
import { logout } from './api/http'

const loggedOut = ref(false)

async function signOut() {
  await logout()
  loggedOut.value = true
  window.location.href = '/'
}
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink class="brand" to="/">
        <span class="brand-mark">云</span>
        <span>纯大子网盘</span>
      </RouterLink>
      <nav class="nav-links" aria-label="主导航">
        <RouterLink to="/">首页</RouterLink>
        <RouterLink to="/profile">个人主页</RouterLink>
        <RouterLink to="/files">我的文件</RouterLink>
      </nav>
      <div class="top-actions">
        <RouterLink class="button button-light" to="/login">登录</RouterLink>
        <RouterLink class="button button-primary" to="/register">注册</RouterLink>
        <button v-if="!loggedOut" class="avatar-button" title="退出登录" @click="signOut">退</button>
      </div>
    </header>
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>
