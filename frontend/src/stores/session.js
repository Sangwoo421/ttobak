// 대화 세션 상태 (pinia). 서버 응답 필드는 snake_case 그대로 보관한다.
// 오디오 재생·마이크는 여기서 다루지 않는다 → composables/useConversation.js 가 조합한다.
import { defineStore } from 'pinia'
import * as ai from '@/api/ai'

let msgSeq = 0

export const useSessionStore = defineStore('session', {
  state: () => ({
    session_id: null,
    state: 'IDLE', // BRIEFING | LISTENING | EXPLAIN | OFFER_ADD_QUESTION | SLOT_* | CONFIRM | CLARIFY | SUMMARY | DONE | END
    startState: 'LISTENING', // 브리핑 재생이 끝난 뒤 올라갈 상태. 거래 한 건이 확인 불가면 OFFER_ADD_QUESTION
    tone: 'friendly', // friendly | confirm
    messages: [], // { id, role: 'assistant'|'user', text, tone, at }
    buttons: [], // ui.buttons
    choices: [], // ui.choices (CLARIFY 일 때만)
    listen: false, // ui.listen: true 면 음성 끝난 뒤 마이크 자동 시작
    lastDebug: null, // 마지막 턴의 debug
    lastTurn: null, // 마지막 TurnResponse 원본
    briefing: null, // SessionStartResponse.briefing
    silenceMs: 2000, // 서버가 준 VAD 침묵 대기값 (ui.silence_ms)
    silenceOverride: null, // 개발 패널 강제값 (예: 700 = baseline 비교)
    pending: false, // STT/턴 요청 진행 중
    error: null,
    turnCount: 0,
  }),

  getters: {
    effectiveSilenceMs: (s) => s.silenceOverride ?? s.silenceMs ?? 2000,
    isConfirm: (s) => s.tone === 'confirm',
    hasSession: (s) => !!s.session_id,
    /** 화면 하단에 그릴 버튼 (STOP 은 헤더에 항상 따로 있으므로 뺀다) */
    mainButtons: (s) => (s.buttons || []).filter((b) => b.id !== 'STOP'),
  },

  actions: {
    reset() {
      const silenceOverride = this.silenceOverride
      this.$reset()
      this.silenceOverride = silenceOverride
    },

    pushMessage(role, text, tone = 'friendly') {
      this.messages.push({ id: ++msgSeq, role, text, tone, at: Date.now() })
    },

    /** POST /ai/session/start */
    async start({ user_id = 1, notification_id = null, transaction_id = null, mode = 'layered' } = {}) {
      this.reset()
      this.pending = true
      this.error = null
      try {
        const resp = await ai.startSession({ user_id, notification_id, transaction_id, mode })
        this.session_id = resp.session_id
        this.state = 'BRIEFING' // 재생이 끝나면 화면이 resp.state(LISTENING) 로 올린다
        this.startState = resp.state || 'LISTENING'
        this.tone = resp.tone || 'friendly'
        this.briefing = resp.briefing
        this.buttons = resp.ui?.buttons || []
        this.choices = []
        // 읽어준 뒤 바로 듣기 시작할지. 버튼을 눌러야 말할 수 있으면 탭이 한 번 더 늘어난다.
        this.listen = resp.ui?.listen !== false
        this.silenceMs = resp.ui?.silence_ms || 2000
        if (resp.briefing?.text) this.pushMessage('assistant', resp.briefing.text, this.tone)
        return resp
      } catch (e) {
        this.error = e
        throw e
      } finally {
        this.pending = false
      }
    },

    /** 브리핑 음성이 끝났을 때 */
    briefingEnded() {
      if (this.state === 'BRIEFING') this.state = this.startState || 'LISTENING'
    },

    async _turn(body, userLabel) {
      if (!this.session_id) throw new Error('세션이 없어요')
      this.pending = true
      this.error = null
      if (userLabel) this.pushMessage('user', userLabel)
      try {
        const resp = await ai.turn({ session_id: this.session_id, ...body })
        this.applyTurn(resp)
        return resp
      } catch (e) {
        this.error = e
        throw e
      } finally {
        this.pending = false
      }
    },

    /** 텍스트(STT 결과 또는 타이핑) 턴 */
    sendText(text) {
      return this._turn({ text }, text)
    },

    /** 버튼 턴. 말풍선에는 버튼 라벨을 남긴다 */
    sendButton(button_id) {
      const label = (this.buttons || []).find((b) => b.id === button_id)?.label || { STOP: '대화 종료' }[button_id] || button_id
      return this._turn({ button_id }, label)
    },

    /** CLARIFY 선택지 턴 */
    sendChoice(choice_id) {
      const label = (this.choices || []).find((c) => c.id === choice_id)?.label || choice_id
      return this._turn({ choice_id }, label)
    },

    /** 녹음 Blob → STT → 텍스트 턴. STT 가 빈 문자열이면 null 을 돌려주고 턴을 보내지 않는다 */
    async sendAudio(blob) {
      if (!this.session_id) throw new Error('세션이 없어요')
      this.pending = true
      this.error = null
      try {
        const { text } = await ai.stt(blob, this.session_id)
        if (!text || !text.trim()) return null
        return await this.sendText(text.trim())
      } catch (e) {
        this.error = e
        throw e
      } finally {
        this.pending = false
      }
    },

    /** TurnResponse 를 상태에 반영 */
    applyTurn(resp) {
      this.turnCount += 1
      this.lastTurn = resp
      this.state = resp.state || this.state
      this.tone = resp.tone || 'friendly'
      this.buttons = resp.ui?.buttons || []
      this.choices = resp.ui?.choices || []
      this.listen = !!resp.ui?.listen
      this.lastDebug = resp.debug || null
      if (resp.assistant_text) this.pushMessage('assistant', resp.assistant_text, this.tone)
    },
  },
})
