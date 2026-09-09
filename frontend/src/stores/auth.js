import { defineStore } from 'pinia'
import { getAuthSession, logoutSession, simpleLogin } from '@/api/backend'

const KEY = 'ttobak.auth.session'

function loadSession() {
  try {
    const raw = sessionStorage.getItem(KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveSession(session) {
  try {
    if (session) sessionStorage.setItem(KEY, JSON.stringify(session))
    else sessionStorage.removeItem(KEY)
  } catch {
    /* 저장이 막혀도 현재 화면에서는 로그인 상태를 유지한다 */
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    session: loadSession(),
    restoring: false,
    restored: false,
  }),

  getters: {
    authenticated: (state) => Boolean(state.session?.access_token),
    userName: (state) => state.session?.user_name || '',
    userId: (state) => state.session?.user_id || 1,
  },

  actions: {
    async login(pin) {
      const session = await simpleLogin(1, pin)
      this.session = session
      this.restored = true
      saveSession(session)
      return session
    },

    async restore() {
      if (this.restored || this.restoring) return this.authenticated
      this.restoring = true
      try {
        if (!this.session?.access_token) return false
        const user = await getAuthSession()
        this.session = { ...this.session, ...user }
        saveSession(this.session)
        return true
      } catch {
        this.clear()
        return false
      } finally {
        this.restoring = false
        this.restored = true
      }
    },

    async logout() {
      try {
        if (this.authenticated) await logoutSession()
      } finally {
        this.clear()
      }
    },

    clear() {
      this.session = null
      saveSession(null)
    },
  },
})
