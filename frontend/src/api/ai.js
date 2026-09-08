// AI 서버 (docs/contracts/openapi-ai.yaml) 래퍼. JSON 은 snake_case 그대로 쓴다.
import { http, USE_MOCK } from './http'
import { mockAi } from './mock'

/** POST /ai/session/start → SessionStartResponse
 *  transaction_id 를 주면 세 건을 다 읽지 않고 그 거래 한 건만 읽고 설명한다 (어르신 모드 내역 탭). */
export async function startSession({ user_id = 1, notification_id = null, transaction_id = null, mode = 'layered' } = {}) {
  if (USE_MOCK) return mockAi.sessionStart()
  const { data } = await http.post('/ai/session/start', { user_id, notification_id, transaction_id, mode })
  return data
}

/** POST /ai/stt (multipart: audio, session_id) → { text, hints_used, duration_ms, provider } */
export async function stt(blob, session_id) {
  if (USE_MOCK) return mockAi.stt(blob)
  const form = new FormData()
  const ext = (blob.type || 'audio/webm').split('/')[1]?.split(';')[0] || 'webm'
  form.append('audio', blob, blob.name || `speech.${ext}`)
  form.append('session_id', session_id)
  const { data } = await http.post('/ai/stt', form, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 90_000 })
  return data
}

/** POST /ai/turn { session_id, text | button_id | choice_id } → TurnResponse */
export async function turn({ session_id, text = null, button_id = null, choice_id = null }) {
  if (USE_MOCK) return mockAi.turn({ text, button_id, choice_id })
  const { data } = await http.post('/ai/turn', { session_id, text, button_id, choice_id })
  return data
}

/** POST /ai/tts { text, tone } → { audio_url, cached } */
export async function tts(text, tone = 'friendly') {
  if (USE_MOCK) return mockAi.tts(text, tone)
  const { data } = await http.post('/ai/tts', { text, tone })
  return data
}

/** POST /ai/session/{id}/summary → SessionSummaryResponse (턴의 GO_COUNTER 가 같은 일을 하므로 화면에서는 보통 안 쓴다) */
export async function sessionSummary(session_id) {
  if (USE_MOCK) return mockAi.sessionSummary()
  const { data } = await http.post(`/ai/session/${encodeURIComponent(session_id)}/summary`)
  return data
}

/** GET /ai/session/{id}/debug (개발 패널용) */
export async function sessionDebug(session_id) {
  if (USE_MOCK) return { session_id, state: 'MOCK', mode: 'mock', candidates: [], turns: [] }
  const { data } = await http.get(`/ai/session/${encodeURIComponent(session_id)}/debug`)
  return data
}

/** GET /ai/health */
export async function aiHealth() {
  if (USE_MOCK) return { status: 'mock' }
  const { data } = await http.get('/ai/health')
  return data
}
