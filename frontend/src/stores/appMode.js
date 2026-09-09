import { defineStore } from 'pinia'

// 어르신 모드는 화면 하나의 상태가 아니라 앱의 모드다.
// 한 번 켜면 "모드 끄기"를 누르기 전까지 유지되고, 그동안에는 어르신 모드 홈이 메인 화면이다.
// 화면을 옮겨 다녀도 풀리면 안 되므로 스토어에 두고, 새로고침에도 살아남게 localStorage 에 남긴다.
const KEY = 'ttobak.seniorMode'

function load() {
  try {
    return localStorage.getItem(KEY) === '1'
  } catch {
    return false // 시크릿 모드 등에서 접근이 막혀도 앱은 떠야 한다
  }
}

function save(on) {
  try {
    localStorage.setItem(KEY, on ? '1' : '0')
  } catch {
    /* 저장 못 해도 이번 세션 동안은 동작한다 */
  }
}

export const useAppModeStore = defineStore('appMode', {
  state: () => ({
    seniorMode: load(),
  }),

  actions: {
    enable() {
      this.seniorMode = true
      save(true)
    },
    disable() {
      this.seniorMode = false
      save(false)
    },
    toggle() {
      this.seniorMode ? this.disable() : this.enable()
    },
  },
})
