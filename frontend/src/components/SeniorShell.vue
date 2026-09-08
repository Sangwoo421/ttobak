<script setup>
import DevPanel from './DevPanel.vue'
import { useConversation } from '@/composables/useConversation'

// 어르신 화면 공통 껍데기: 헤더(제목 · 그만 · ⚙) + 개발 패널 + 토스트.
// "그만" 버튼은 어떤 상태에서도 보인다 (policy §6).
defineProps({
  title: { type: String, default: '또박또박' },
  stopLabel: { type: String, default: '그만' },
})
const emit = defineEmits(['stop'])
const conv = useConversation()
</script>

<template>
  <div class="shell senior">
    <header class="top">
      <div class="title">{{ title }}</div>
      <button type="button" class="stop" @click="emit('stop')">{{ stopLabel }}</button>
      <button type="button" class="gear" title="개발 패널" aria-label="개발 패널" @click="conv.devOpen.value = !conv.devOpen.value">⚙</button>
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

.stop {
  min-height: 72px;
  min-width: 110px;
  padding: 0 20px;
  border-radius: var(--radius);
  border: 3px solid var(--danger);
  background: #fff;
  color: var(--danger);
  font-size: 24px;
  font-weight: 900;
}

.gear {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 0;
  background: rgba(0, 0, 0, 0.12);
  color: rgba(0, 0, 0, 0.55);
  font-size: 18px;
  padding: 0;
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
</style>
