<script setup>
import { computed } from 'vue'

// 큰 마이크 버튼. 듣는 중이면 빨갛게 (누르면 바로 끝내고 보낸다).
const props = defineProps({
  status: { type: String, default: 'idle' }, // idle | listening | processing | speaking
  disabled: { type: Boolean, default: false },
  size: { type: String, default: 'lg' }, // lg | md
  // 쉬고 있을 때의 문구를 상황에 맞게 바꾼다. 못 알아들은 뒤라면 "다시 말하기"가 맞다.
  idleLabel: { type: String, default: '' },
})
defineEmits(['click'])

const label = computed(() => {
  if (props.status === 'idle' || props.status === 'speaking') return props.idleLabel || '눌러서 말하기'
  return { listening: '다 말했어요', processing: '잠깐만요' }[props.status] || '말하기'
})
</script>

<template>
  <button
    type="button"
    class="mic-btn"
    :class="[status, size]"
    :disabled="disabled || status === 'processing'"
    :aria-label="label"
    @click="$emit('click')"
  >
    <span class="icon" aria-hidden="true">
      <svg viewBox="0 0 24 24" width="36" height="36" fill="currentColor">
        <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2z" />
      </svg>
    </span>
    <span class="txt">{{ label }}</span>
  </button>
</template>

<style scoped>
.mic-btn {
  width: 100%;
  min-height: 84px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border-radius: 999px;
  border: 4px solid #1b1b1b;
  background: #1b1b1b;
  color: #fff;
  font-size: 24px;
  font-weight: 900;
  transition: background 0.15s ease;
}

.mic-btn.md {
  min-height: 72px;
  font-size: 22px;
}

.mic-btn:disabled {
  opacity: 0.5;
}

.mic-btn:focus-visible {
  outline: 5px solid #1a56b0;
  outline-offset: 3px;
}

.mic-btn.listening {
  background: var(--bad);
  border-color: var(--bad);
  animation: pulse 1.2s infinite;
}

.mic-btn.processing {
  background: #777;
  border-color: #777;
}

.icon {
  display: inline-flex;
}
</style>
