// 목(mock) 응답. docs/contracts/examples/*.json 을 그대로 쓴다 (단일 진실).
// 예시에 없는 버튼/선택지 응답만 여기서 최소한으로 합성한다 (dialog-state-machine.md 의 문장 사용).
//
// import.meta.glob 을 쓰는 이유: Docker 빌드 컨텍스트(frontend/)에는 ../docs 가 없어서
// 정적 import 면 빌드가 깨진다. glob 은 파일이 없으면 빈 객체가 되어 빌드가 통과한다.
const files = import.meta.glob('@contracts/*.json', { eager: true, import: 'default' })

function example(name) {
  const key = Object.keys(files).find((k) => k.endsWith(`/${name}.json`))
  if (!key) throw new Error(`목 예시가 없어요: ${name}.json (docs/contracts/examples 필요)`)
  return structuredClone(files[key])
}

const delay = (value, ms = 350) => new Promise((resolve) => setTimeout(() => resolve(value), ms))

// ---------- 세션/턴 ----------
let textTurn = 0 // 텍스트 턴 카운터: 1→ask-tx1, 2→ask-tx3-unknown, 3→request-transfer-confirm, 이후 clarify
let lastState = 'LISTENING'
let lastResp = null

// 시연 대본의 사용자 발화 (목 STT 가 순서대로 돌려준다)
const SCRIPTED_UTTERANCES = [
  '첫 번째 거 그게 뭐야',
  '세 번째 그 정보통신인가 그건 뭐야',
  '아들이 뭐 보내라는데 이십만 원인가',
  '으음 그 저기',
]

const LISTENING_BUTTONS = () => example('session-start').ui.buttons

/** turn-ask-tx1 을 뼈대로 버튼/선택지 응답을 만든다 */
function synth({ text, state = 'LISTENING', tone = 'friendly', buttons, choices = [], listen = true, actions = [], inputKind = 'button', inputValue = null }) {
  const base = example('turn-ask-tx1')
  base.assistant_text = text
  base.audio_url = 'mock://tts'
  base.tone = tone
  base.state = state
  base.ui = { buttons: buttons || LISTENING_BUTTONS(), choices, listen }
  base.actions = actions
  base.debug = {
    ...base.debug,
    turn_no: textTurn + 100,
    input_kind: inputKind,
    user_text: inputValue,
    intent: inputValue,
    intent_confidence: 1.0,
    candidates: [],
    matched_candidate: null,
    match_score: null,
    decision: 'NA',
    path: ['mock'],
    llm_used: false,
    state_before: lastState,
    state_after: state,
  }
  return base
}

function summaryResp(inputKind, inputValue) {
  const s = example('session-summary')
  return synth({
    text: s.spoken_text,
    state: 'SUMMARY',
    tone: 'confirm',
    buttons: [],
    listen: false,
    actions: [{ type: 'OPEN_SUMMARY', payload: { summary_id: s.summary_id, code: s.code, ticket_no: s.ticket_no } }],
    inputKind,
    inputValue,
  })
}

function endResp(inputKind, inputValue) {
  return synth({ text: '네, 다음에 또 불러 주세요.', state: 'END', buttons: [], listen: false, actions: [{ type: 'END' }], inputKind, inputValue })
}

function buttonResp(id) {
  switch (id) {
    case 'YES':
      if (lastState === 'OFFER_ADD_QUESTION')
        return synth({ text: '적어뒀어요. 더 물어보실 것 있으세요?', actions: [{ type: 'ADD_QUESTION', payload: { transaction_id: 103 } }], inputValue: id })
      if (lastState === 'CONFIRM')
        return synth({ text: '이체는 창구에서 직원이 도와드려요. 요약서에 적어둘게요.', actions: [{ type: 'ADD_REQUEST', payload: { confirmed_by_user: true } }], inputValue: id })
      return synth({ text: '네. 더 물어보실 것 있으세요?', inputValue: id })
    case 'NO':
      return synth({ text: '네, 알겠어요. 더 물어보실 것 있으세요?', inputValue: id })
    case 'ASK_MORE':
      return synth({ text: '네, 말씀하세요.', inputValue: id })
    case 'GO_COUNTER':
      return summaryResp('button', id)
    case 'STOP':
      return endResp('button', id)
    case 'REPEAT':
      return lastResp ? { ...structuredClone(lastResp), audio_url: 'mock://tts' } : synth({ text: '다시 말씀드릴게요.', inputValue: id })
    default:
      return synth({ text: '네.', inputValue: id })
  }
}

function choiceResp(id) {
  if (id === 'INTENT:GO_COUNTER') return summaryResp('choice', id)
  if (id === 'INTENT:REQUEST_TRANSFER' || id.startsWith('CP:')) return example('turn-request-transfer-confirm')
  if (id === 'INTENT:ASK_ABOUT_TX' || id.startsWith('TX:')) return example('turn-ask-tx1')
  return synth({ text: '네.', inputKind: 'choice', inputValue: id })
}

export const mockAi = {
  async sessionStart() {
    textTurn = 0
    lastState = 'LISTENING'
    lastResp = null
    resetSummary() // 새 시연마다 요약서를 접수 상태로 되돌린다
    return delay(example('session-start'), 500)
  },

  async stt(blob) {
    const text = SCRIPTED_UTTERANCES[Math.min(textTurn, SCRIPTED_UTTERANCES.length - 1)]
    return delay({ text, hints_used: [], duration_ms: Math.round((blob?.size || 0) / 6), provider: 'mock' }, 600)
  },

  async turn({ text, button_id, choice_id }) {
    let resp
    if (text != null && text !== '') {
      textTurn += 1
      const seq = ['turn-ask-tx1', 'turn-ask-tx3-unknown', 'turn-request-transfer-confirm']
      resp = example(seq[textTurn - 1] || 'turn-clarify')
      resp.debug.user_text = text
    } else if (button_id) {
      resp = buttonResp(button_id)
    } else if (choice_id) {
      resp = choiceResp(choice_id)
    } else {
      resp = synth({ text: '네.' })
    }
    resp.audio_url = 'mock://tts'
    lastState = resp.state
    lastResp = resp
    return delay(resp, 700)
  },

  async tts(text, tone = 'friendly') {
    return delay({ audio_url: 'mock://tts', cached: true, _text: text, _tone: tone }, 100)
  },

  async sessionSummary() {
    return delay(example('session-summary'))
  },
}

// ---------- 요약서 (직원 화면과 어르신 화면이 다른 탭이어도 같이 보이도록 localStorage) ----------
const SUMMARY_KEY = 'ttobak_mock_summary'

function loadSummary() {
  try {
    const raw = localStorage.getItem(SUMMARY_KEY)
    if (raw) return JSON.parse(raw)
  } catch {
    /* ignore */
  }
  return example('summary')
}

function saveSummary(s) {
  try {
    localStorage.setItem(SUMMARY_KEY, JSON.stringify(s))
  } catch {
    /* ignore */
  }
  return s
}

function resetSummary() {
  try {
    localStorage.removeItem(SUMMARY_KEY)
  } catch {
    /* ignore */
  }
}

function recomputeStatus(s) {
  const work = s.items.filter((i) => i.section !== 'PREP')
  const handled = work.filter((i) => i.handled).length
  s.status = handled === 0 ? 'OPEN' : handled === work.length ? 'DONE' : 'IN_PROGRESS'
  return s
}

function notFound() {
  const err = new Error('없음')
  err.response = { status: 404, data: { message: '요약서를 찾을 수 없어요' } }
  return err
}

const MOCK_BRANCHES = [
  {
    id: 1,
    name: 'KB국민은행 종로지점',
    district: '종로구',
    address: '서울 종로구 종로',
    opening_hours: '평일 09:00~16:00',
    waiting_count: 3,
    estimated_wait_minutes: 18,
    next_ticket_no: 15,
  },
  {
    id: 2,
    name: 'KB국민은행 광화문종합금융센터',
    district: '종로구',
    address: '서울 종로구 새문안로',
    opening_hours: '평일 09:00~18:00',
    waiting_count: 2,
    estimated_wait_minutes: 10,
    next_ticket_no: 24,
  },
  {
    id: 3,
    name: 'KB국민은행 서대문지점',
    district: '서대문구',
    address: '서울 서대문구 통일로',
    opening_hours: '평일 09:00~16:00',
    waiting_count: 1,
    estimated_wait_minutes: 7,
    next_ticket_no: 9,
  },
]

const MOCK_TICKET_KEY = 'ttobak.mock.branchTicket'

function loadBranchTicket() {
  try {
    const raw = localStorage.getItem(MOCK_TICKET_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveBranchTicket(ticket) {
  try {
    if (ticket) localStorage.setItem(MOCK_TICKET_KEY, JSON.stringify(ticket))
    else localStorage.removeItem(MOCK_TICKET_KEY)
  } catch {
    /* ignore */
  }
  return ticket
}

function mockError(message, status = 400) {
  const err = new Error(message)
  err.response = { status, data: { message } }
  return err
}

export const mockBackend = {
  async simpleLogin({ user_id, pin }) {
    if (Number(user_id) !== 1 || pin !== '123456') {
      throw mockError('간편비밀번호가 올바르지 않습니다', 401)
    }
    return delay({
      access_token: 'mock-session-token',
      token_type: 'Bearer',
      expires_in_seconds: 1800,
      user_id: 1,
      user_name: '김영자',
    }, 450)
  },
  async getAuthSession() {
    try {
      const session = JSON.parse(sessionStorage.getItem('ttobak.auth.session') || 'null')
      if (session?.access_token === 'mock-session-token') {
        return delay({ user_id: 1, user_name: '김영자' }, 120)
      }
    } catch {
      /* 아래 401 처리 */
    }
    throw mockError('로그인이 필요합니다', 401)
  },
  async logoutSession() {
    return delay(null, 100)
  },
  async getBranches() {
    return delay(MOCK_BRANCHES.map(({ next_ticket_no: _, ...branch }) => ({ ...branch })), 300)
  },
  async getActiveBranchTicket(userId) {
    const ticket = loadBranchTicket()
    if (ticket?.user_id === Number(userId) && ['WAITING', 'CALLED'].includes(ticket.status)) {
      return delay(ticket, 200)
    }
    return delay(null, 200)
  },
  async issueBranchTicket(branchId, { user_id, summary_id, purpose }) {
    const branch = MOCK_BRANCHES.find((item) => item.id === Number(branchId))
    if (!branch) throw mockError('은행 지점을 찾을 수 없습니다', 404)
    const active = loadBranchTicket()
    if (active && ['WAITING', 'CALLED'].includes(active.status)) {
      if (active.branch_id === branch.id) {
        const linked = summary_id ? { ...active, summary_id: Number(summary_id), summary_code: loadSummary().code } : active
        if (summary_id) {
          const summary = loadSummary()
          saveSummary({ ...summary, branch_name: branch.name, ticket_no: active.ticket_no })
          saveBranchTicket(linked)
        }
        return delay(linked)
      }
      throw mockError('이미 사용 중인 대기표가 있습니다', 409)
    }
    const summary = summary_id ? loadSummary() : null
    const ticket = saveBranchTicket({
      id: Date.now(),
      user_id: Number(user_id),
      branch_id: branch.id,
      summary_id: summary ? Number(summary_id) : null,
      summary_code: summary?.code || null,
      branch_name: branch.name,
      branch_address: branch.address,
      ticket_no: branch.next_ticket_no,
      purpose: purpose || '일반 상담',
      status: 'WAITING',
      ahead_count: branch.waiting_count,
      estimated_wait_minutes: branch.estimated_wait_minutes,
      issued_at: new Date().toISOString(),
    })
    if (summary) saveSummary({ ...summary, branch_name: branch.name, ticket_no: ticket.ticket_no })
    return delay(ticket, 450)
  },
  async cancelBranchTicket(ticketId) {
    const ticket = loadBranchTicket()
    if (!ticket || ticket.id !== Number(ticketId)) throw mockError('대기표를 찾을 수 없습니다', 404)
    if (ticket.status !== 'WAITING') throw mockError('지금은 대기표를 취소할 수 없습니다', 409)
    return delay(saveBranchTicket({ ...ticket, status: 'CANCELLED' }), 300)
  },
  async briefing() {
    return delay(example('briefing'))
  },
  async getSummary(id) {
    const s = loadSummary()
    if (Number(id) !== s.id) throw notFound()
    return delay(s)
  },
  async getSummaryByCode(code) {
    const s = loadSummary()
    if (String(code) !== s.code) throw notFound()
    return delay(s)
  },
  async getSummaryStatus(id) {
    const s = recomputeStatus(loadSummary())
    if (Number(id) !== s.id) throw notFound()
    const work = s.items.filter((i) => i.section !== 'PREP')
    const handledItems = work.filter((i) => i.handled)
    return delay({
      id: s.id,
      status: s.status,
      handled_count: handledItems.length,
      total_count: work.length,
      last_handled_at: handledItems.map((i) => i.handled_at).sort().pop() || null,
    })
  },
  async listStaffSummaries(status) {
    const s = recomputeStatus(loadSummary())
    const row = { id: s.id, code: s.code, ticket_no: s.ticket_no, user_name: s.user_name, status: s.status, created_at: s.created_at, item_count: s.items.filter((i) => i.section !== 'PREP').length }
    return delay(!status || status === s.status ? [row] : [])
  },
  async patchSummaryItem(summaryId, itemId, handled) {
    const s = loadSummary()
    if (Number(summaryId) !== s.id) throw notFound()
    const item = s.items.find((i) => i.id === Number(itemId))
    if (!item) throw notFound()
    item.handled = !!handled
    item.handled_at = handled ? new Date().toISOString().slice(0, 19) : null
    return delay(saveSummary(recomputeStatus(s)))
  },
}
