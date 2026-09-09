// 어르신 홈 "들어오고 나간 돈 듣기" 카드의 뱃지·부제 표시 규칙.
//
// 이 카드가 세는 것은 "아직 안 들은 알림(미청취)" 개수다 — 백엔드 countUnheard 기준.
// 최근 거래 목록의 길이(홈 목록에 뿌리는 그 배열)와는 무관하다. 예전에는 목록 길이를
// 그대로 뱃지에 썼는데, 목록은 청취 여부와 상관없이 최근 6건을 주므로 항상 6이 떴다.

/**
 * 미청취 개수 → 뱃지 노출 여부와 부제 문구.
 * @param {number} count 미청취 알림 개수
 * @returns {{ count: number, showBadge: boolean, subtitle: string }}
 */
export function unheardBadge(count) {
  const n = Number.isFinite(count) && count > 0 ? Math.floor(count) : 0
  return {
    count: n,
    // 0건이면 뱃지를 숨긴다. 어르신 화면에 "0" 이 뜨거나 "0건" 이 보이면 안 된다.
    showBadge: n > 0,
    subtitle: n > 0 ? `새로 온 알림 ${n}건` : '새로 온 알림이 없어요',
  }
}

/**
 * 백엔드 GET /api/users/{id}/briefing 응답에서 미청취 총계를 뽑는다.
 * unheard_count 가 있으면 그대로 쓰고, 없으면(구버전 응답) items 길이 + remaining_count 로 복원한다.
 * @param {object|null} briefing
 * @returns {number}
 */
export function unheardCountFromBriefing(briefing) {
  if (!briefing || typeof briefing !== 'object') return 0
  if (Number.isFinite(briefing.unheard_count)) return Math.max(0, Math.floor(briefing.unheard_count))
  const items = Array.isArray(briefing.items) ? briefing.items.length : 0
  const remaining = Number.isFinite(briefing.remaining_count) ? briefing.remaining_count : 0
  return Math.max(0, items + remaining)
}
