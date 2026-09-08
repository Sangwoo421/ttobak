// 표시용 포맷 유틸. 숫자를 한국어 수사로 "읽는" 것은 AI 서버 책임이고, 여기서는 화면 표기만 한다.

/** 300000 → "300,000원" */
export function won(n) {
  if (n === null || n === undefined || n === '') return '-'
  const num = Number(n)
  if (Number.isNaN(num)) return String(n)
  return num.toLocaleString('ko-KR') + '원'
}

/** "2026-09-08T14:32:10" → "2026-09-08 14:32" */
export function dateTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso)
  const p = (v) => String(v).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

/** 서수 라벨 1 → "첫째" */
export function ordinalLabel(n) {
  return ['', '첫째', '둘째', '셋째', '넷째', '다섯째'][n] || `${n}번째`
}

/** 요약서 status → 한글 */
export function statusLabel(status) {
  return { OPEN: '접수됨', IN_PROGRESS: '처리 중', DONE: '처리 완료' }[status] || status || '-'
}

/** classification level → 한글 */
export function levelLabel(level) {
  return { CONFIRMED: '확인됨', PARTIAL: '일부 확인', UNKNOWN: '확인 안 됨' }[level] || level || '-'
}
