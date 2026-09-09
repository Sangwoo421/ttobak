import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'
import './styles/base.css'

const pinia = createPinia()

router.beforeEach(async (to) => {
  const auth = useAuthStore(pinia)
  await auth.restore()

  if (to.meta.requiresAuth && !auth.authenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.path === '/login' && auth.authenticated) return '/mock/home'
})

createApp(App).use(pinia).use(router).mount('#app')
