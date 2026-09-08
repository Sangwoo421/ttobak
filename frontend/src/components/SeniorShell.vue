<script setup>
import DevPanel from './DevPanel.vue'
import { useConversation } from '@/composables/useConversation'

// 어르신 화면 공통 껍데기: 헤더(제목 · 대화 종료 · ⚙) + 개발 패널 + 토스트.
// "대화 종료" 버튼은 어떤 상태에서도 보인다 (policy §6).
defineProps({
  title: { type: String, default: '또박또박' },
  // "그만"은 뭘 그만하는지 처음 보면 알기 어렵다. "대화 종료"가 뭘 끝내는지 명확하다.
  stopLabel: { type: String, default: '대화 종료' },
})
const emit = defineEmits(['stop'])
const conv = useConversation()
const isDev = import.meta.env.DEV
</script>

<template>
  <div class="shell senior">
    <header class="top">
      <div class="title">{{ title }}</div>
      <button type="button" class="stop" @click="emit('stop')">
        <span class="stop-ico" aria-hidden="true">■</span>{{ stopLabel }}
      </button>
      <!-- 개발/측정용 패널. tools/measure 측정 스크립트와 시연 중 마이크 문제 시 텍스트 입력 대체 수단으로 쓰인다.
           실제 사용자(어르신)에게는 필요 없는 도구라 프로덕션 빌드(npm run build)에서는 아예 숨긴다. -->
      <button
        v-if="isDev"
        type="button"
        class="gear"
        title="개발 패널"
        aria-label="개발 패널"
        @click="conv.devOpen.value = !conv.devOpen.value"
      >⚙</button>
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

.title {
  flex: 1;
  font-size: 24px;
  font-weight: 900;
  color: #1b1b1b;
}

/* 최소 72px/22px 는 정책(senior-mode-policy.md §6) 최소 기준이라 줄이면 안 된다 */
.stop {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 72px;
  min-width: 100px;
  padding: 0 18px;
  border-radius: 999px;
  border: none;
  background: var(--danger);
  color: #fff;
  font-size: 22px;
  font-weight: 900;
  box-shadow: 0 3px 10px rgba(217, 48, 37, 0.35);
}

.stop-ico {
  font-size: 12px;
}

.stop:active {
  background: #b9271d;
}

.gear {
  width: 48px;
  height: 48px;
  flex: none;
  border-radius: 50%;
  border: 0;
  background: rgba(0, 0, 0, 0.12);
  color: rgba(0, 0, 0, 0.55);
  font-size: 24px;
  padding: 0;
}

.stop:focus-visible,
.gear:focus-visible {
  outline: 5px solid #1a56b0;
  outline-offset: 3px;
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
    white-space: nowrap;
  }

  .stop {
    min-width: 80px;
    padding: 0 10px;
    font-size: 22px;
  }
}
</style>
