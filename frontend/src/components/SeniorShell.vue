<script setup>
import { useRouter } from 'vue-router'
import DevPanel from './DevPanel.vue'
import { useConversation } from '@/composables/useConversation'

// 어르신 화면 공통 껍데기: 헤더(뒤로가기 · 제목 · 오른쪽 슬롯) + 개발 패널 + 토스트.
//
// 헤더에는 나가는 길 하나만 둔다. 예전에는 뒤로가기와 "그만"이 나란히 있었는데, 어르신
// 입장에서는 둘 다 "이 화면에서 나가기"라 구분이 안 되고 policy §6 의 "한 화면에 버튼 3개
// 이하"도 넘겼다. 상담 화면의 "그만" 버튼도 제거해 뒤로가기만 종료 동작을 맡는다.
//
// 시각 규칙(design/A_Chat.dc.html · A안 마감본): 흰 헤더 + 머리카락 선, 테두리 있는 뒤로가기,
// 색은 노랑 하나. 여기서 정한 CSS 변수를 BigButton·SpeechBubble·MicButton 이 그대로 쓴다.
defineProps({
  // 제목은 서비스 이름이 아니라 '지금 이 화면에서 뭘 하는지'를 말한다.
  title: { type: String, default: '물어보기' },
  back: { type: Boolean, default: true },
})
const conv = useConversation()
const router = useRouter()

// history.back() 이 아니라 홈으로 보낸다. 뒤로 가면 방금 끝낸 대화나 요약서로 돌아가
// 어르신이 같은 화면을 반복해서 보게 된다. 돌아갈 곳은 항상 어르신 모드 홈이다.
function goHome() {
  conv.interrupt?.() // 재생·녹음을 멈추고 나간다
  router.push('/mock/home')
}

// 개발자 패널은 시연 안전장치(녹음 클립 입력·침묵 대기 전환·debug)라 꼭 필요하지만
// 제품 기능이 아니다. 심사위원 눈에 정체불명의 톱니바퀴가 보이면 안 되므로 제목을
// 길게 눌러야 열리게 숨긴다.
let pressTimer = null
function holdStart() {
  clearTimeout(pressTimer)
  pressTimer = setTimeout(() => { conv.devOpen.value = !conv.devOpen.value }, 1500)
}
function holdEnd() {
  clearTimeout(pressTimer)
}
</script>

<template>
  <div class="shell senior">
    <header class="top">
      <!-- 화살표는 글자(←) 대신 SVG 로 그린다. 글자는 폰트마다 글리프가 em 박스 안에서
           치우쳐 있어 버튼 정중앙에 오지 않는다. -->
      <button v-if="back" type="button" class="back" aria-label="홈으로 돌아가기" @click="goHome">
        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
          <path d="M15 5 L8 12 L15 19" fill="none" stroke="currentColor"
                stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <h1
        class="title"
        @pointerdown="holdStart"
        @pointerup="holdEnd"
        @pointerleave="holdEnd"
        @pointercancel="holdEnd"
        @contextmenu.prevent
      >{{ title }}</h1>
      <div class="right"><slot name="right" /></div>
    </header>

    <DevPanel v-if="conv.devOpen.value" />

    <main class="content">
      <slot />
    </main>

    <transition name="toast">
      <div v-if="conv.toast.value" class="toast">{{ conv.toast.value }}</div>
    </transition>
  </div>
</template>

<style scoped>
.shell {
  /* 확인 톤(policy §3)만 이 화면에서 따로 잡는다. 나머지 색은 base.css 의 A안 팔레트를 그대로 쓴다. */
  --confirm-bg: #fbf9f4;
  --confirm-border: #17161a;
  --confirm-text: #17161a;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 100%;
  background: var(--paper);
}

/* 머리글은 돌아가는 길과 지금 뭘 하는 화면인지, 둘만. */
.top {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  background: #fff;
  border-bottom: 1px solid #edebe5;
  position: sticky;
  top: 0;
  z-index: 5;
}

.back {
  width: 48px;
  height: 48px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  border: 1px solid #e6e3dc;
  background: #fff;
  color: #3d3a34;
  padding: 0;
  cursor: pointer;
}

.back svg {
  width: 24px;
  height: 24px;
  display: block;
}

.back:active {
  background: var(--paper);
}

.back:focus-visible {
  outline: 5px solid #1a56b0;
  outline-offset: 3px;
}

.title {
  flex: 1;
  margin: 0;
  font-size: 23px;
  font-weight: 800;
  color: var(--ink);
  letter-spacing: -0.5px;
  line-height: 1.25;
  /* "들어오고 나 / 간 돈" 처럼 단어 중간에서 깨지지 않게 어절 단위로만 접는다 */
  word-break: keep-all;
  overflow-wrap: break-word;
  user-select: none;
  -webkit-user-select: none;
  cursor: default;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.toast {
  position: absolute;
  left: 50%;
  bottom: 120px;
  transform: translateX(-50%);
  background: var(--ink);
  color: #fff;
  border: none;
  padding: 14px 22px;
  border-radius: 999px;
  font-size: 19px;
  font-weight: 700;
  box-shadow: 0 12px 30px rgba(23, 22, 26, 0.3);
  z-index: 20;
  white-space: nowrap;
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

@media (max-width: 360px) {
  .top {
    gap: 10px;
    padding: 12px 14px;
  }

  .title {
    font-size: 21px;
  }

  .back {
    width: 44px;
    height: 44px;
  }

  .back svg {
    width: 22px;
    height: 22px;
  }
}
</style>
