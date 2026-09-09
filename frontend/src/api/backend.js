// 백엔드 (docs/contracts/openapi-backend.yaml) 래퍼. JSON 은 snake_case 그대로 쓴다.
import { http, USE_MOCK } from './http'
import { mockBackend } from './mock'

/** POST /api/auth/simple-login → AuthSession */
export async function simpleLogin(user_id, pin) {
  if (USE_MOCK) return mockBackend.simpleLogin({ user_id, pin })
  const { data } = await http.post('/api/auth/simple-login', { user_id, pin })
  return data
}

/** GET /api/auth/session → AuthUser */
export async function getAuthSession() {
  if (USE_MOCK) return mockBackend.getAuthSession()
  const { data } = await http.get('/api/auth/session')
  return data
}

/** POST /api/auth/logout */
export async function logoutSession() {
  if (USE_MOCK) return mockBackend.logoutSession()
  await http.post('/api/auth/logout')
}

/** GET /api/branches → BankBranch[] */
export async function getBranches() {
  if (USE_MOCK) return mockBackend.getBranches()
  const { data } = await http.get('/api/branches')
  return data
}

/** GET /api/branch-tickets/active → BranchTicket | null */
export async function getActiveBranchTicket(user_id = 1) {
  if (USE_MOCK) return mockBackend.getActiveBranchTicket(user_id)
  const { data } = await http.get('/api/branch-tickets/active', { params: { user_id } })
  return data || null
}

/** POST /api/branches/{id}/tickets → BranchTicket */
export async function issueBranchTicket(branch_id, { user_id = 1, summary_id = null, purpose = '일반 상담' } = {}) {
  if (USE_MOCK) return mockBackend.issueBranchTicket(branch_id, { user_id, summary_id, purpose })
  const { data } = await http.post(`/api/branches/${branch_id}/tickets`, { user_id, summary_id, purpose })
  return data
}

/** DELETE /api/branch-tickets/{id} → BranchTicket */
export async function cancelBranchTicket(ticket_id) {
  if (USE_MOCK) return mockBackend.cancelBranchTicket(ticket_id)
  const { data } = await http.delete(`/api/branch-tickets/${ticket_id}`)
  return data
}

/** GET /api/users/{id}/briefing (화면에서는 AI 서버가 대신 부르므로 참고용) */
export async function getBriefing(user_id = 1) {
  if (USE_MOCK) return mockBackend.briefing()
  const { data } = await http.get(`/api/users/${user_id}/briefing`)
  return data
}

/** GET /api/users/{id}/transactions → BriefingItem[] (청취 여부와 무관한 최근 거래)
 *  브리핑은 미청취 3건뿐이라 한 번 들으면 비어 버린다. 홈·내역 화면은 이쪽을 쓴다. */
export async function getTransactions(user_id = 1, limit = 10) {
  if (USE_MOCK) return (await mockBackend.briefing()).items.slice(0, limit)
  const { data } = await http.get(`/api/users/${user_id}/transactions`, { params: { limit } })
  return data
}

/** GET /api/summaries/{id} → Summary */
export async function getSummary(summary_id) {
  if (USE_MOCK) return mockBackend.getSummary(summary_id)
  const { data } = await http.get(`/api/summaries/${summary_id}`)
  return data
}

/** GET /api/summaries/by-code/{code} → Summary */
export async function getSummaryByCode(code) {
  if (USE_MOCK) return mockBackend.getSummaryByCode(code)
  const { data } = await http.get(`/api/summaries/by-code/${encodeURIComponent(code)}`)
  return data
}

/** GET /api/summaries/{id}/status → SummaryStatus */
export async function getSummaryStatus(summary_id) {
  if (USE_MOCK) return mockBackend.getSummaryStatus(summary_id)
  const { data } = await http.get(`/api/summaries/${summary_id}/status`)
  return data
}

/** GET /api/staff/summaries?status= → StaffSummaryListItem[] */
export async function listStaffSummaries(status) {
  if (USE_MOCK) return mockBackend.listStaffSummaries(status)
  const { data } = await http.get('/api/staff/summaries', { params: status ? { status } : {} })
  return data
}

/** PATCH /api/staff/summaries/{id}/items/{item_id} { handled } → Summary */
export async function patchSummaryItem(summary_id, item_id, handled) {
  if (USE_MOCK) return mockBackend.patchSummaryItem(summary_id, item_id, handled)
  const { data } = await http.patch(`/api/staff/summaries/${summary_id}/items/${item_id}`, { handled })
  return data
}

/** GET /api/health */
export async function backendHealth() {
  if (USE_MOCK) return { status: 'mock' }
  const { data } = await http.get('/api/health')
  return data
}
