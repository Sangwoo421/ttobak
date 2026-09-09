// @vitest-environment happy-dom
//
// 회귀 방지: 거래 한 건을 눌러 대화로 들어가면(/senior/chat?tx=101) 메시지 영역이
// "챗봇을 준비하고 있어요…" 에서 멈추던 버그.
//
// 원인: startDirectChat() 이 `await conv.begin()` 뒤 finally 에서 starting=false 로 되돌렸는데,
// tx= 경로는 자동 마이크가 켜져 있어 begin() 의 프로미스가 대화가 끝날 때까지 resolve 되지
// 않는다(begin → startListening → runTurn → afterTurn → startListening 재귀). 그래서 finally 가
// 영영 안 돌고 로딩 표시가 갇혔다.
//
// 고침: begin() 이 세션 응답 직후(재생 전) 부르는 onStarted 콜백에서 starting=false + URL 정리.
// 이 테스트는 "begin() 이 resolve 되지 않아도 onStarted 만 불리면 로딩이 걷힌다" 를 못박는다.

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'

const replace = vi.fn()
const push = vi.fn()
let routeQuery = {}

vi.mock('vue-router', () => ({
  useRouter: () => ({ replace, push }),
  useRoute: () => ({ query: routeQuery }),
}))

let conv // 컴포넌트가 useConversation() 으로 받는 객체
vi.mock('@/composables/useConversation', () => ({
  useConversation: () => conv,
}))

// 목이 걸린 뒤에 import 해야 한다.
const { default: SeniorChat } = await import('@/views/senior/SeniorChat.vue')

const STUBS = {
  SeniorShell: { template: '<div><slot /><slot name="right" /></div>' },
  ToneFrame: { template: '<div><slot /></div>' },
  SpeechBubble: true,
  BigButton: true,
  MicButton: true,
  MicStatus: true,
}

/** begin() 을 손으로 제어할 수 있는 conv 목을 만든다. */
function makeConv({ hasSession = false } = {}) {
  let capturedOnStarted = null
  let resolveBegin = null
  let rejectBegin = null

  const begin = vi.fn((opts = {}) => {
    capturedOnStarted = opts.onStarted
    return new Promise((res, rej) => {
      resolveBegin = res
      rejectBegin = rej
    })
  })

  conv = {
    session: {
      tone: 'friendly',
      mainButtons: [],
      briefing: null,
      messages: [],
      counterCount: 0,
      choices: [],
      state: 'LISTENING',
      pending: false,
      hasSession,
    },
    recorder: { level: ref(0) },
    autoListen: ref(true),
    busy: ref(false),
    ended: ref(false),
    stopping: ref(false),
    hint: ref(''),
    micStatus: ref('idle'),
    begin,
    toggleMic: vi.fn(),
    pressButton: vi.fn(),
    pickChoice: vi.fn(),
    sendTypedText: vi.fn(),
  }

  return {
    begin,
    fireOnStarted: (resp = {}) => capturedOnStarted?.(resp),
    resolveBegin: () => resolveBegin?.({}),
    rejectBegin: (err) => rejectBegin?.(err),
    get onStartedArg() {
      return begin.mock.calls[0]?.[0]?.onStarted
    },
  }
}

const loadingShown = (w) => w.find('.starting').exists()

beforeEach(() => {
  replace.mockClear()
  push.mockClear()
  routeQuery = {}
})

describe('SeniorChat startDirectChat — 로딩 표시(starting) 해제 시점', () => {
  it('?tx=101: begin() 이 resolve 되지 않아도 onStarted 가 불리면 로딩이 걷힌다', async () => {
    routeQuery = { tx: '101' }
    const h = makeConv()
    const wrapper = mount(SeniorChat, { global: { stubs: STUBS } })
    await flushPromises()

    // begin 은 onStarted 콜백을 받아야 한다
    expect(h.begin).toHaveBeenCalledTimes(1)
    expect(typeof h.onStartedArg).toBe('function')
    expect(h.begin.mock.calls[0][0]).toMatchObject({ transaction_id: 101, playBriefing: true })

    // 세션 응답 전 — 로딩 표시 유지
    expect(loadingShown(wrapper)).toBe(true)

    // 세션 응답 도착(재생 전). begin() 프로미스는 여전히 pending.
    h.fireOnStarted({ briefing: null })
    await flushPromises()

    expect(loadingShown(wrapper)).toBe(false)
    expect(replace).toHaveBeenCalledWith('/senior/chat')

    // begin() 은 끝내 resolve 되지 않는다 — 그래도 로딩이 다시 나오면 안 된다(=버그 재현 방지)
    await flushPromises()
    expect(loadingShown(wrapper)).toBe(false)
  })

  it('?tx=101: begin() 이 실패하면 catch 에서 starting=false 로 풀고 에러를 보여준다', async () => {
    routeQuery = { tx: '101' }
    const h = makeConv()
    const wrapper = mount(SeniorChat, { global: { stubs: STUBS } })
    await flushPromises()
    expect(loadingShown(wrapper)).toBe(true)

    h.rejectBegin(new Error('boom'))
    await flushPromises()

    expect(loadingShown(wrapper)).toBe(false)
    expect(wrapper.find('.start-error').exists()).toBe(true)
  })

  it('?start=true: onStarted 가 로딩을 걷고, autoListen 복원은 begin() 종료(finally)까지 기다린다', async () => {
    routeQuery = { start: 'true' }
    const h = makeConv({ hasSession: false })
    const wrapper = mount(SeniorChat, { global: { stubs: STUBS } })
    await flushPromises()

    // 진입 첫 자동 마이크를 막기 위해 autoListen 을 꺼 둔 상태
    expect(conv.autoListen.value).toBe(false)
    expect(typeof h.onStartedArg).toBe('function')

    h.fireOnStarted({})
    await flushPromises()
    expect(loadingShown(wrapper)).toBe(false)
    expect(replace).toHaveBeenCalledWith('/senior/chat')
    // begin() 이 아직 안 끝났으므로 억제 상태는 그대로
    expect(conv.autoListen.value).toBe(false)

    h.resolveBegin()
    await flushPromises()
    // finally 에서 원래 값(true)으로 복원
    expect(conv.autoListen.value).toBe(true)
  })

  it('브리핑에서 진입(이미 세션 있음, tx·start 없음): startDirectChat 을 아예 안 타고 로딩도 없다', async () => {
    routeQuery = {}
    const h = makeConv({ hasSession: true })
    const wrapper = mount(SeniorChat, { global: { stubs: STUBS } })
    await flushPromises()

    expect(h.begin).not.toHaveBeenCalled()
    expect(replace).not.toHaveBeenCalled()
    expect(loadingShown(wrapper)).toBe(false)
  })
})
