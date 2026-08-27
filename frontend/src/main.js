import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'
import { getCurrentUser } from './api/http'
import HomeView from './views/HomeView.vue'
import LoginView from './views/LoginView.vue'
import RegisterView from './views/RegisterView.vue'
import ProfileView from './views/ProfileView.vue'
import FilesView from './views/FilesView.vue'
import UploadView from './views/UploadView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/login', component: LoginView, meta: { guestOnly: true } },
    { path: '/register', component: RegisterView, meta: { guestOnly: true } },
    { path: '/profile', component: ProfileView, meta: { requiresAuth: true } },
    { path: '/files', component: FilesView, meta: { requiresAuth: true } },
    { path: '/upload', component: UploadView, meta: { requiresAuth: true } },
  ],
})

router.beforeEach(async (to) => {
  const user = await getCurrentUser()
  if (to.meta.requiresAuth && !user) return '/login'
  if (to.meta.guestOnly && user) return '/profile'
})

createApp(App).use(router).mount('#app')
