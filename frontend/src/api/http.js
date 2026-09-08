import axios from 'axios'

/** true 면 서버를 부르지 않고 docs/contracts/examples 의 JSON 을 돌려준다 (.env.local 의 VITE_USE_MOCK). */
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

// baseURL 을 비워 두면 같은 origin 의 /api, /ai 로 나간다 → dev 는 vite proxy, 운영은 nginx 가 프록시.
export const http = axios.create({
  baseURL: '',
  timeout: 60_000,
  headers: { Accept: 'application/json' },
})

/** axios 오류 → 사람이 읽을 메시지 */
export function errorMessage(err) {
  if (!err) return '알 수 없는 오류'
  if (err.response) {
    const status = err.response.status
    const detail = err.response.data?.message || err.response.data?.detail
    return `서버 오류 ${status}${detail ? `: ${detail}` : ''}`
  }
  if (err.request) return '서버에 연결할 수 없어요'
  return err.message || String(err)
}
