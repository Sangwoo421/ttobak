<script setup>
// 어르신용 큰 버튼. policy §6: 최소 높이 72px, 글자 22px 이상.
// A안 마감본: primary 는 노란 면, secondary 는 흰 면 + 1px 테두리. 굵은 테두리와 그림자는 쓰지 않는다.
defineProps({
  kind: { type: String, default: 'secondary' }, // primary | secondary | danger
  size: { type: String, default: 'lg' }, // lg (76px) | xl (96px, confirm 톤)
  disabled: { type: Boolean, default: false },
  block: { type: Boolean, default: true },
})
defineEmits(['click'])
</script>

<template>
  <button type="button" class="big-btn" :class="[kind, size, { block }]" :disabled="disabled" @click="$emit('click')">
    <slot />
  </button>
</template>

<style scoped>
/* A안: 강조색은 노랑 하나. 테두리를 두껍게 두르는 대신 면과 여백으로 구분한다.
   두꺼운 테두리는 버튼이 많아질수록 화면이 격자처럼 보여 오히려 읽기 어려웠다. */
.big-btn {
  min-height: 76px;
  padding: 12px 20px;
  border-radius: 18px;
  border: 1px solid transparent;
  font-size: 21px;
  font-weight: 800;
  letter-spacing: -0.4px;
  line-height: 1.3;
  word-break: keep-all;
  transition: transform 0.08s ease, filter 0.1s ease;
  -webkit-tap-highlight-color: transparent;
}

.big-btn.block {
  width: 100%;
  display: block;
}

.big-btn:active {
  transform: scale(0.985);
  filter: brightness(0.96);
}

.big-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.big-btn:focus-visible {
  outline: 5px solid #1a56b0;
  outline-offset: 3px;
}

.big-btn.primary {
  background: var(--kb-yellow);
  color: var(--ink);
  border-color: transparent;
}

.big-btn.secondary {
  background: #fff;
  color: var(--ink-2);
  border-color: #e6e3dc;
}

.big-btn.danger {
  background: #fff;
  color: var(--danger);
  border-color: var(--danger);
}

/* 확인 단계(policy §3)에서만 쓰는 크기. 여기서는 화면이 통째로 달라져야 하므로 키운다. */
.big-btn.xl {
  min-height: 92px;
  font-size: 26px;
  border-radius: 20px;
}
</style>
