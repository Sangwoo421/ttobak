<script setup>
import { computed } from 'vue'

// 큰 마이크 버튼. 이 화면의 주 입력 수단이라 가장 진한 면(검정)을 여기 하나에만 쓴다.
// 듣는 중이면 빨갛게 (누르면 바로 끝내고 보낸다).
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
      <svg viewBox="0 0 24 24" width="30" height="30" fill="none" stroke="currentColor"
           stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 3a3 3 0 0 1 3 3v5a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3z" />
        <path d="M19 11a7 7 0 0 1-14 0" />
        <path d="M12 18v3" />
      </svg>
    </span>
    <span class="txt">{{ label }}</span>
  </button>
</template>

<style scoped>
.mic-btn {
  width: 100%;
  min-height: 88px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 13px;
  border-radius: 22px;
  border: none;
  background: var(--ink);
  color: #fff;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.5px;
  box-shadow: 0 10px 26px rgba(23, 22, 26, 0.22);
  transition: transform 0.08s ease, background 0.15s ease;
}

.mic-btn:active {
  transform: scale(0.985);
}

.mic-btn.md {
  min-height: 76px;
  font-size: 22px;
  border-radius: 18px;
}

.mic-btn:disabled {
  opacity: 0.45;
  box-shadow: none;
}

.mic-btn:focus-visible {
  outline: 5px solid #1a56b0;
  outline-offset: 3px;
}

.mic-btn.listening {
  background: var(--bad);
  box-shadow: 0 10px 26px rgba(197, 34, 31, 0.28);
}

.mic-btn.processing {
  background: #6b675e;
  box-shadow: none;
}

.icon {
  display: inline-flex;
}
</style>
