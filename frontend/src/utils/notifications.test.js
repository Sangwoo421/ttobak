import { describe, it, expect } from 'vitest'
import { unheardBadge, unheardCountFromBriefing } from './notifications'

// 회귀 방지: 어르신 홈 "들어오고 나간 돈 듣기" 카드의 뱃지·부제.
// 예전 버그 — 최근 거래 목록 길이(항상 6)를 뱃지에 그대로 썼다.
// 이제는 미청취 개수(countUnheard)만 봐야 하고, 0건이면 뱃지를 숨긴다.
describe('unheardBadge', () => {
  it('미청취 0건이면 뱃지를 숨기고 부제가 "새로 온 알림이 없어요"', () => {
    expect(unheardBadge(0)).toEqual({
      count: 0,
      showBadge: false,
      subtitle: '새로 온 알림이 없어요',
    })
  })

  it('미청취 1건이면 뱃지 노출 + "새로 온 알림 1건"', () => {
    expect(unheardBadge(1)).toEqual({
      count: 1,
      showBadge: true,
      subtitle: '새로 온 알림 1건',
    })
  })

  it('미청취 3건이면 뱃지 노출 + "새로 온 알림 3건"', () => {
    expect(unheardBadge(3)).toEqual({
      count: 3,
      showBadge: true,
      subtitle: '새로 온 알림 3건',
    })
  })

  it('음수·NaN·undefined 는 0건으로 취급해 뱃지를 숨긴다', () => {
    for (const bad of [-2, NaN, undefined, null, 'x']) {
      const r = unheardBadge(bad)
      expect(r.showBadge).toBe(false)
      expect(r.subtitle).toBe('새로 온 알림이 없어요')
    }
  })
})

describe('unheardCountFromBriefing', () => {
  it('unheard_count 필드가 있으면 그대로 쓴다', () => {
    expect(unheardCountFromBriefing({ unheard_count: 3, items: [], remaining_count: 0 })).toBe(3)
    expect(unheardCountFromBriefing({ unheard_count: 0, items: [], remaining_count: 0 })).toBe(0)
  })

  it('unheard_count 가 없으면 items 길이 + remaining_count 로 복원한다 (구버전 응답)', () => {
    expect(unheardCountFromBriefing({ items: [1], remaining_count: 0 })).toBe(1)
    expect(unheardCountFromBriefing({ items: [1, 2, 3], remaining_count: 0 })).toBe(3)
    expect(unheardCountFromBriefing({ items: [1, 2, 3], remaining_count: 3 })).toBe(6)
    expect(unheardCountFromBriefing({ items: [], remaining_count: 0 })).toBe(0)
  })

  it('null·빈 응답이면 0', () => {
    expect(unheardCountFromBriefing(null)).toBe(0)
    expect(unheardCountFromBriefing(undefined)).toBe(0)
    expect(unheardCountFromBriefing({})).toBe(0)
  })
})

// 화면에 실제로 뿌려지는 조합을 미청취 0 / 1 / 3 세 경우로 못박는다.
describe('브리핑 응답 → 홈 카드 표시 (통합)', () => {
  const cases = [
    { name: '미청취 0건', briefing: { unheard_count: 0, items: [], remaining_count: 0 }, showBadge: false, subtitle: '새로 온 알림이 없어요', count: 0 },
    { name: '미청취 1건', briefing: { unheard_count: 1, items: [1], remaining_count: 0 }, showBadge: true, subtitle: '새로 온 알림 1건', count: 1 },
    { name: '미청취 3건', briefing: { unheard_count: 3, items: [1, 2, 3], remaining_count: 0 }, showBadge: true, subtitle: '새로 온 알림 3건', count: 3 },
  ]

  for (const c of cases) {
    it(c.name, () => {
      const badge = unheardBadge(unheardCountFromBriefing(c.briefing))
      expect(badge.showBadge).toBe(c.showBadge)
      expect(badge.subtitle).toBe(c.subtitle)
      expect(badge.count).toBe(c.count)
    })
  }
})
