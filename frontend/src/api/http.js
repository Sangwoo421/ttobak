import axios from 'axios'

/** true 면 서버를 부르지 않고 docs/contracts/examples 의 JSON 을 돌려준다 (.env.local 의 VITE_USE_MOCK). */
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

// baseURL 을 비워 두면 같은 origin 의 /api, /ai 로 나간다 → dev 는 vite proxy, 운영은 nginx 가 프록시.
export const http = axios.create({
  baseURL: '',
  timeout: 60_000,
  headers: { Accept: 'application/json' },
})

/** 어르신 화면용 오류 문구.
 *  상태코드나 브라우저 원문("Network Error", "timeout of 60000ms exceeded")을 그대로 보여주면
 *  이 사용자층에는 아무 도움이 안 되고, 디지털 약자 대상 서비스에서 특히 나쁘게 읽힌다.
 *  기술적 상세는 콘솔로 보내고 화면에는 한 문장만 남긴다. */
export function seniorErrorMessage(err) {
  if (err) console.warn('[senior]', err)
  return '지금 연결이 안 돼요. 잠시 뒤에 다시 해보세요.'
}

/** axios 오류 → 사람이 읽을 메시지 (직원 화면·개발자 패널용. 상세를 그대로 보여준다) */
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
