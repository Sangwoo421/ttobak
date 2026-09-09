// 어르신 대화 오케스트레이션: 세션 스토어 + 녹음기 + 플레이어 + 라우터를 묶는다.
// 브리핑/대화 화면이 같은 인스턴스를 쓰도록 모듈 싱글턴 상태를 갖는다.
//
// 턴 1개의 흐름:  입력(음성/버튼/선택지/타이핑) → /ai/turn → 말풍선 + 음성 재생
//                → 재생 끝 → actions 처리 → ui.listen 이면 마이크 자동 시작
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { useRecorder, RECORDER_DEFAULTS } from './useRecorder'
import { useAudioPlayer } from './useAudioPlayer'
import { seniorErrorMessage } from '@/api/http'

const busy = ref(false) // STT/턴 요청 진행 중
const ended = ref(false) // END 액션을 받았다
const stopping = ref(false) // STOP 을 눌러서 응답을 기다리는 중 (이전 버튼이 잠깐 보이는 걸 막는다)
const toast = ref('')
const hint = ref('') // 마이크 안내 문구 (예: 잘 못 들었어요)
const autoListen = ref(true) // ui.listen 자동 마이크 (시끄러운 곳에서 끌 수 있다)
const vadThreshold = ref(RECORDER_DEFAULTS.threshold)
const showDebug = ref(false)
const devOpen = ref(false)

let toastTimer = null
let routerRef = null

function showToast(text, ms = 2500) {
  toast.value = text
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), ms)
}

// 창구 목록에 담긴 항목은 role='counter' 메시지로 대화 흐름에 남는다.
// SpeechBubble/SeniorChat 을 건드리지 않고 말풍선과 구분(테두리·배경)을 주기 위해
// 전역 스타일을 한 번만 주입한다. 어르신 모드 글자 크기(--senior-font, 22px)와 고대비를 따른다.
function ensureCounterCardStyle() {
  if (typeof document === 'undefined' || document.getElementById('ttobak-counter-card-style')) return
  const el = document.createElement('style')
  el.id = 'ttobak-counter-card-style'
  el.textContent = `
    .bubble-row.counter { justify-content: center; }
    .bubble-row.counter .bubble.counter {
      max-width: 100%;
      width: 100%;
      background: var(--kb-yellow-soft);
      border: 3px solid var(--kb-yellow-dark);
      border-radius: var(--radius);
      color: var(--text);
      font-size: var(--senior-font);
      font-weight: 700;
      line-height: 1.5;
      box-shadow: var(--shadow);
    }
    .bubble-row.counter .bubble.counter p { white-space: pre-wrap; margin: 0; }
  `
  document.head.appendChild(el)
}

export function useConversation() {
  ensureCounterCardStyle()
  const session = useSessionStore()
  const recorder = useRecorder()
  const player = useAudioPlayer()
  // useRouter 는 setup 안에서만 동작 → 처음 setup 에서 잡아 두고 이후 재사용
  const r = useRouter()
  if (r) routerRef = r

  /** 마이크 상태 표시용 */
  const micStatus = computed(() => {
    if (recorder.status.value === 'listening') return 'listening'
    if (recorder.status.value === 'processing' || busy.value || session.pending) return 'processing'
    if (player.playing.value) return 'speaking'
    return 'idle'
  })

  const canInteract = computed(() => !busy.value && !session.pending && recorder.status.value === 'idle')

  /** 세션 시작 + 브리핑 재생. onStarted 는 세션이 생긴 직후(재생 전), resolve 는 재생이 끝난 뒤 (state → LISTENING) */
  async function begin({ onStarted, playBriefing = true, ...opts } = {}) {
    ended.value = false
    hint.value = ''
    player.stop()
    if (recorder.status.value === 'listening') recorder.cancel()
    const resp = await session.start(opts)
    onStarted?.(resp)
    if (playBriefing) await player.play(resp.briefing?.audio_url)
    session.briefingEnded()
    // 읽어주고 나면 바로 듣는다. 어르신이 말하려고 버튼을 또 누르게 하지 않는다.
    if (resp.ui?.listen && autoListen.value && !ended.value) await startListening({ auto: true })
    return resp
  }

  /** 마지막 브리핑/응답 음성을 다시 재생 (서버 턴 없이) */
  async function replayLast() {
    const url = session.lastTurn?.audio_url || session.briefing?.audio_url
    if (url) await player.play(url)
  }

  /** 턴 응답 공통 후처리 */
  async function afterTurn(resp) {
    if (!resp) {
      stopping.value = false
      return
    }
    await player.play(resp.audio_url)
    for (const action of resp.actions || []) {
      switch (action.type) {
        case 'OPEN_SUMMARY': {
          const id = action.payload?.summary_id
          if (id != null) routerRef?.push(`/senior/summary/${id}`)
          stopping.value = false
          return
        }
        case 'END':
          ended.value = true
          stopping.value = false
          return
        case 'ADD_QUESTION':
        case 'ADD_REQUEST':
          // 대화 화면에 사라지지 않는 카드로 남긴다. 토스트는 짧게 같이 띄운다(즉시 확인용).
          session.addCounterItem(action)
          showToast('창구 목록에 담았어요')
          break
        case 'MUTE':
          showToast('다음부터는 읽지 않을게요')
          break
        default:
          break
      }
    }
    // STOP 은 정책상 항상 END 로 끝나야 하지만, 혹시 다른 액션으로 왔더라도 로딩 화면에 갇히지 않게 한다.
    stopping.value = false
    if (resp.ui?.listen && autoListen.value && !ended.value) {
      await startListening({ auto: true })
    }
  }

  async function runTurn(promise) {
    busy.value = true
    hint.value = ''
    try {
      const resp = await promise
      busy.value = false
      if (resp === null) {
        // STT 가 빈 문자열
        stopping.value = false
        hint.value = '잘 못 들었어요. 마이크를 누르고 다시 말씀해 주세요.'
        return null
      }
      await afterTurn(resp)
      return resp
    } catch (e) {
      busy.value = false
      stopping.value = false
      hint.value = seniorErrorMessage(e)
      console.error('[turn]', e)
      return null
    }
  }

  function interrupt() {
    player.stop()
    if (recorder.status.value === 'listening') recorder.cancel()
  }

  /** 버튼 (ASK_MORE / GO_COUNTER / STOP / YES / NO / REPEAT) */
  function pressButton(button_id) {
    if (button_id === 'STOP') stopping.value = true
    interrupt()
    return runTurn(session.sendButton(button_id))
  }

  /** CLARIFY 선택지 */
  function pickChoice(choice_id) {
    interrupt()
    return runTurn(session.sendChoice(choice_id))
  }

  /** 타이핑 텍스트 (개발 패널) */
  function sendTypedText(text) {
    if (!text || !text.trim()) return Promise.resolve(null)
    interrupt()
    return runTurn(session.sendText(text.trim()))
  }

  /** 오디오 파일/Blob (개발 패널 "녹음 클립 입력 모드") */
  function sendAudioBlob(blob) {
    interrupt()
    return runTurn(session.sendAudio(blob))
  }

  /** 마이크 시작 → VAD 로 자동 종료 → STT → 턴
   *
   *  auto=true 는 ui.listen 으로 저절로 켜진 경우다. 사용자가 마이크를 누른 게 아니므로
   *  실패해도 빨간 경고를 띄우지 않는다. 마이크를 못 쓰는 환경(권한 거부·미지원·소음)에서도
   *  큰 버튼과 글 입력으로 같은 일을 할 수 있어야 한다는 게 이 서비스의 전제다.
   */
  async function startListening({ auto = false } = {}) {
    if (recorder.status.value !== 'idle' || busy.value || session.pending || ended.value) return
    player.stop()
    hint.value = ''
    let result
    try {
      result = await recorder.record({ silenceMs: session.effectiveSilenceMs, threshold: vadThreshold.value })
    } catch (e) {
      if (!auto) hint.value = e?.message || '마이크를 시작하지 못했어요. 아래 버튼으로도 하실 수 있어요.'
      return
    }
    if (!result) return // cancel 됨
    if (!result.speechDetected || result.durationMs < RECORDER_DEFAULTS.minMs) {
      if (!auto) hint.value = '말소리를 못 들었어요. 마이크를 누르고 말씀해 주세요.'
      return
    }
    await runTurn(session.sendAudio(result.blob))
  }

  /** 마이크 버튼: 듣는 중이면 바로 끝내고 보내기, 아니면 듣기 시작 */
  function toggleMic() {
    if (recorder.status.value === 'listening') recorder.stop()
    else startListening()
  }

  return {
    session,
    recorder,
    player,
    micStatus,
    canInteract,
    busy,
    ended,
    stopping,
    toast,
    hint,
    autoListen,
    vadThreshold,
    showDebug,
    devOpen,
    begin,
    replayLast,
    pressButton,
    pickChoice,
    sendTypedText,
    sendAudioBlob,
    startListening,
    toggleMic,
    interrupt,
    showToast,
  }
}
