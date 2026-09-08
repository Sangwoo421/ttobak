<script setup>
import { useRouter } from 'vue-router'
import { won } from '@/utils/format'
import { useAudioPlayer } from '@/composables/useAudioPlayer'

// KB스타뱅킹 느낌의 정적 홈 목업. 위쪽 푸시 알림 배너를 누르면 어르신 모드 브리핑으로 들어간다.
// (담당 조태석) 시연 1단계. 여기서는 어떤 API 도 부르지 않는다.
const router = useRouter()
const player = useAudioPlayer()

const account = { name: 'KB국민ONE통장', number: '123-45-****67', balance: 1234560 }
const recent = [
  { id: 101, title: '김철수', sub: '어제 15:12 · 이체', amount: 300000, type: 'IN' },
  { id: 102, title: '한국전력공사', sub: '오늘 08:30 · 자동이체', amount: 42000, type: 'OUT' },
  { id: 103, title: '대한정보통신', sub: '오늘 09:10 · 자동이체', amount: 19000, type: 'OUT' },
]
const quick = [
  { icon: '↗', label: '이체' },
  { icon: '≡', label: '조회' },
  { icon: '▭', label: '카드' },
  { icon: '⋯', label: '더보기' },
]
const tabs = ['홈', '자산', '상품', '혜택', '전체']

function openBriefing() {
  player.unlock() // 사용자 제스처 안에서 오디오를 한 번 깨워 두면 이후 자동재생이 잘 된다
  router.push('/senior/briefing')
}
</script>

<template>
  <div class="kb-home">
    <!-- 푸시 알림 배너 -->
    <button type="button" class="push" @click="openBriefing">
      <span class="app-icon">KB</span>
      <span class="push-body">
        <span class="push-head"><b>KB스타뱅킹</b><span class="when">방금</span></span>
        <span class="push-text">입금 {{ won(300000) }} 김철수 · 방금</span>
        <span class="push-sub">눌러서 음성으로 들어보세요</span>
      </span>
    </button>

    <header class="kb-top">
      <span class="logo"><span class="star">★</span>KB스타뱅킹</span>
      <span class="bell">🔔</span>
    </header>

    <section class="balance">
      <div class="acc-name">{{ account.name }}</div>
      <div class="acc-no">{{ account.number }}</div>
      <div class="acc-balance">{{ won(account.balance) }}</div>
      <div class="acc-actions">
        <button type="button">이체</button>
        <button type="button">내역</button>
      </div>
    </section>

    <section class="quick">
      <button v-for="q in quick" :key="q.label" type="button" class="quick-btn">
        <span class="q-icon">{{ q.icon }}</span>
        <span>{{ q.label }}</span>
      </button>
    </section>

    <section class="recent">
      <h3>최근 거래</h3>
      <div v-for="r in recent" :key="r.id" class="row">
        <div>
          <div class="t">{{ r.title }}</div>
          <div class="s">{{ r.sub }}</div>
        </div>
        <div class="amt" :class="r.type">{{ r.type === 'IN' ? '+' : '-' }}{{ won(r.amount) }}</div>
      </div>
    </section>

    <div class="spacer" />

    <nav class="tabbar">
      <button v-for="(t, i) in tabs" :key="t" type="button" :class="{ on: i === 0 }">{{ t }}</button>
    </nav>

    <router-link class="staff-link" to="/staff">직원 화면 →</router-link>
  </div>
</template>

<style scoped>
.kb-home {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  flex: 1;
  background: #f5f5f3;
  padding-bottom: 70px;
  position: relative;
}

/* 푸시 알림 */
.push {
  margin: 10px 10px 4px;
  display: flex;
  gap: 12px;
  align-items: center;
  text-align: left;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid #ddd;
  border-radius: 18px;
  padding: 12px 14px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
  animation: slide 0.45s ease-out;
  font-family: inherit;
}

@keyframes slide {
  from {
    transform: translateY(-120%);
    opacity: 0;
  }
  to {
    transform: none;
    opacity: 1;
  }
}

.app-icon {
  flex: none;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: var(--kb-yellow);
  color: var(--kb-brown);
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.push-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.push-head {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #333;
}

.when {
  color: #888;
}

.push-text {
  font-size: 17px;
  font-weight: 800;
  color: #111;
}

.push-sub {
  font-size: 12px;
  color: #777;
}

.kb-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px 8px;
  font-size: 18px;
  font-weight: 900;
  color: var(--kb-brown);
}

.star {
  color: var(--kb-yellow);
  margin-right: 4px;
}

.balance {
  margin: 8px 16px;
  padding: 20px;
  border-radius: 18px;
  background: var(--kb-yellow);
  color: #2b2620;
  box-shadow: var(--shadow);
}

.acc-name {
  font-weight: 800;
}

.acc-no {
  font-size: 13px;
  opacity: 0.75;
  margin-bottom: 14px;
}

.acc-balance {
  font-size: 30px;
  font-weight: 900;
  margin-bottom: 14px;
}

.acc-actions {
  display: flex;
  gap: 8px;
}

.acc-actions button {
  flex: 1;
  padding: 10px;
  border-radius: 10px;
  border: 0;
  background: rgba(255, 255, 255, 0.7);
  font-weight: 800;
  font-size: 15px;
}

.quick {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin: 10px 16px;
}

.quick-btn {
  background: #fff;
  border: 1px solid #eee;
  border-radius: 14px;
  padding: 12px 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: #333;
}

.q-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--kb-yellow-soft);
  color: var(--kb-brown);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.recent {
  margin: 8px 16px;
  background: #fff;
  border-radius: 16px;
  padding: 14px 16px;
  border: 1px solid #eee;
}

.recent h3 {
  margin: 0 0 8px;
  font-size: 15px;
  color: #555;
}

.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-top: 1px solid #f0f0f0;
}

.row:first-of-type {
  border-top: 0;
}

.t {
  font-weight: 800;
  font-size: 15px;
}

.s {
  font-size: 12px;
  color: #888;
}

.amt {
  font-weight: 900;
}

.amt.IN {
  color: #1a56b0;
}

.amt.OUT {
  color: #333;
}

.spacer {
  flex: 1;
}

.tabbar {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  background: #fff;
  border-top: 1px solid #e5e5e5;
  padding: 8px 0 12px;
}

.tabbar button {
  border: 0;
  background: none;
  font-size: 12px;
  color: #888;
  font-weight: 700;
  padding: 6px 0;
}

.tabbar button.on {
  color: var(--kb-brown);
}

.staff-link {
  position: absolute;
  right: 12px;
  bottom: 56px;
  font-size: 11px;
  color: #aaa;
  text-decoration: none;
}
</style>
