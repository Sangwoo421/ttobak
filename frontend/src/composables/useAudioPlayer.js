// 공용 <audio> 하나로 서버 음성(audio_url)을 재생한다.
//   play(url) → Promise: ended(또는 오류/stop) 시 resolve. 목 모드면 재생 없이 즉시 resolve.
//   stop()    → 재생 중지 + 대기 중인 play() resolve
import { ref, readonly } from 'vue'
import { USE_MOCK } from '@/api/http'

// 목 모드에서 "읽어드리는 중" 상태를 눈으로 확인하고 싶으면 이 값을 늘린다 (ms).
const MOCK_AUDIO_MS = 0

const playing = ref(false)
const currentUrl = ref(null)

let audio = null
let pendingResolve = null

function ensureAudio() {
  if (audio) return audio
  audio = new Audio()
  audio.preload = 'auto'
  audio.addEventListener('ended', finish)
  audio.addEventListener('error', finish)
  return audio
}

function finish() {
  playing.value = false
  currentUrl.value = null
  const r = pendingResolve
  pendingResolve = null
  r?.()
}

function stop() {
  if (audio && !audio.paused) {
    try {
      audio.pause()
      audio.currentTime = 0
    } catch {
      /* ignore */
    }
  }
  finish()
}

function play(url) {
  stop()
  if (!url || USE_MOCK || url.startsWith('mock:')) {
    playing.value = true
    return new Promise((resolve) =>
      setTimeout(() => {
        playing.value = false
        resolve()
      }, MOCK_AUDIO_MS),
    )
  }
  const el = ensureAudio()
  return new Promise((resolve) => {
    pendingResolve = resolve
    currentUrl.value = url
    playing.value = true
    el.src = url
    el.play().catch(() => {
      // 자동재생 차단 등: 재생 없이 진행 (화면에 텍스트가 항상 크게 있으므로 시연은 계속된다)
      console.warn('[audio] play 실패, 건너뜀:', url)
      finish()
    })
  })
}

/** 사용자 제스처 직후 한 번 호출해 두면 이후 자동재생 차단이 줄어든다 */
function unlock() {
  try {
    const el = ensureAudio()
    el.muted = true
    const p = el.play()
    if (p?.catch) p.catch(() => {})
    el.pause()
    el.muted = false
  } catch {
    /* ignore */
  }
}

export function useAudioPlayer() {
  return { playing: readonly(playing), currentUrl: readonly(currentUrl), play, stop, unlock }
}
