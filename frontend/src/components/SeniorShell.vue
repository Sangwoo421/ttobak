<script setup>
import { useRouter } from 'vue-router'
import DevPanel from './DevPanel.vue'
import { useConversation } from '@/composables/useConversation'

// 어르신 화면 공통 껍데기: 헤더(뒤로가기 · 제목) + 개발 패널 + 토스트.
//
// 헤더에는 나가는 길 하나만 둔다. 예전에는 뒤로가기와 "그만"이 나란히 있었는데, 어르신
// 입장에서는 둘 다 "이 화면에서 나가기"라 구분이 안 되고 policy §6 의 "한 화면에 버튼 3개
// 이하"도 넘겼다. 대화를 끝내는 "그만"은 음성과 대화 중 큰 버튼으로 그대로 남아 있다.
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
                stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />
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
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 100%;
}

.top {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--kb-yellow);
  position: sticky;
  top: 0;
  z-index: 5;
}

.back {
  width: 52px;
  height: 52px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  border: 2px solid rgba(0, 0, 0, 0.28);
  background: rgba(255, 255, 255, 0.85);
  color: #1b1b1b;
  padding: 0;
  cursor: pointer;
}

.back svg {
  width: 26px;
  height: 26px;
  display: block;
}

.back:active {
  background: #fff;
}

.back:focus-visible {
  outline: 5px solid #1a56b0;
  outline-offset: 3px;
}

.title {
  flex: 1;
  margin: 0;
  font-size: 24px;
  font-weight: 900;
  color: #1b1b1b;
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
  background: #222;
  color: #fff;
  padding: 14px 22px;
  border-radius: 999px;
  font-size: 22px;
  font-weight: 800;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
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
    gap: 4px;
    padding: 8px;
  }

  .title {
    font-size: 22px;
  }

  .back {
    width: 46px;
    height: 46px;
  }

  .back svg {
    width: 23px;
    height: 23px;
  }
}
</style>
