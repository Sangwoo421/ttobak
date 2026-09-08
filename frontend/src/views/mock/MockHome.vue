<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { won } from '@/utils/format'
import { useAudioPlayer } from '@/composables/useAudioPlayer'
import SeniorHome from './SeniorHome.vue'
import { useAppModeStore } from '@/stores/appMode'

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

function openChat() {
  player.unlock()
  router.push({ path: '/senior/chat', query: { start: 'true' } })
}

// 어르신 모드는 앱의 모드다. 화면을 옮겨 다녀도 유지되어야 하므로 스토어에 있다.
const appMode = useAppModeStore()

// 이체·조회·카드처럼 기존 앱이 이미 하는 일은 만들지 않는다(기획서 "적용 형태").
// 다만 아무 반응이 없으면 덜 만든 것처럼 보이므로, 경계라는 사실을 화면이 직접 말한다.
const notice = ref('')
let noticeTimer = null
function outOfScope(label) {
  notice.value = `${label}는 기존 KB스타뱅킹 기능이라 이번 프로토타입에서는 만들지 않았어요.`
  clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => { notice.value = '' }, 2600)
}
</script>

<template>
  <SeniorHome v-if="appMode.seniorMode" :account="account" @exit="appMode.disable()" />

  <div v-else class="kb-home">
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
      <button type="button" class="senior-toggle" @click="appMode.enable()">👵 어르신 모드</button>
    </header>

    <section class="balance">
      <div class="acc-name">{{ account.name }}</div>
      <div class="acc-no">{{ account.number }}</div>
      <div class="acc-balance">{{ won(account.balance) }}</div>
      <div class="acc-actions">
        <button type="button" @click="outOfScope('이체')">이체</button>
        <button type="button" @click="outOfScope('내역 조회')">내역</button>
      </div>
    </section>

    <section class="chat-entry">
      <button type="button" @click="openChat">
        <span class="chat-icon" aria-hidden="true">🎙</span>
        <span class="chat-copy">
          <strong>또박또박 챗봇</strong>
          <small>말하거나 글로 편하게 물어보세요</small>
        </span>
        <span class="chat-arrow" aria-hidden="true">›</span>
      </button>
    </section>

    <section class="quick">
      <button v-for="q in quick" :key="q.label" type="button" class="quick-btn" @click="outOfScope(q.label)">
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
      <button v-for="(t, i) in tabs" :key="t" type="button" :class="{ on: i === 0 }"
              @click="i === 0 ? null : outOfScope(t)">{{ t }}</button>
    </nav>

    <router-link class="staff-link" to="/staff">직원 화면 →</router-link>

    <transition name="fade">
      <p v-if="notice" class="scope-notice">{{ notice }}</p>
    </transition>
  </div>
</template>

<style scoped>
.kb-home {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  flex: 1;
  background: #f5f5f3;
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

.chat-entry {
  margin: 4px 16px 8px;
}

.chat-entry button {
  width: 100%;
  min-height: 82px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 3px solid #1b1b1b;
  border-radius: 18px;
  background: #fff;
  color: #1b1b1b;
  padding: 12px 16px;
  text-align: left;
  box-shadow: var(--shadow);
}

.chat-entry button:focus-visible {
  outline: 5px solid #1a56b0;
  outline-offset: 3px;
}

.chat-icon {
  width: 48px;
  height: 48px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--kb-yellow);
  font-size: 24px;
}

.chat-copy {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.chat-copy strong {
  font-size: 20px;
  font-weight: 900;
}

.chat-copy small {
  color: #666;
  font-size: 14px;
  font-weight: 700;
}

.chat-arrow {
  flex: none;
  font-size: 34px;
  font-weight: 700;
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

/* 프레임 안에서 스크롤되므로 absolute 로는 내용을 따라 올라간다. sticky 로 바닥에 붙인다. */
.tabbar {
  position: sticky;
  bottom: 0;
  z-index: 4;
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
  align-self: flex-end;
  margin: 0 12px 6px;
  font-size: 11px;
  color: #aaa;
  text-decoration: none;
}
/* 어르신 모드 진입. 기획서의 "기존 앱 안의 부가 모드" 전제가 화면에서 보여야 한다. */
.senior-toggle {
  min-height: 40px;
  padding: 0 14px;
  border: 2px solid #6b4e00;
  border-radius: 999px;
  background: #fff8e1;
  font-size: 15px;
  font-weight: 800;
  color: #6b4e00;
  cursor: pointer;
}
.senior-toggle:active { background: #ffe9a8; }

/* 만들지 않은 기존 앱 기능을 눌렀을 때. 침묵보다 경계를 밝히는 편이 낫다. */
.scope-notice {
  position: sticky;
  bottom: 62px;
  z-index: 5;
  margin: 0 16px -46px; /* 탭바 위에 떠 보이되 레이아웃을 밀지 않는다 */
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(27, 27, 27, 0.92);
  color: #fff;
  font-size: 15px;
  line-height: 1.45;
  text-align: center;
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.18s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
