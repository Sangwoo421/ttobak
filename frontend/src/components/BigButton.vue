<script setup>
// 어르신용 큰 버튼. policy §6: 최소 높이 72px, 글자 22px 이상.
defineProps({
  kind: { type: String, default: 'secondary' }, // primary | secondary | danger
  size: { type: String, default: 'lg' }, // lg (72px) | xl (96px, confirm 톤)
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
.big-btn {
  min-height: 72px;
  padding: 12px 20px;
  border-radius: var(--radius);
  border: 3px solid transparent;
  font-size: 24px;
  font-weight: 800;
  line-height: 1.2;
  transition: transform 0.08s ease, filter 0.1s ease;
  -webkit-tap-highlight-color: transparent;
}

.big-btn.block {
  width: 100%;
  display: block;
}

.big-btn:active {
  transform: scale(0.98);
  filter: brightness(0.95);
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
  background: var(--primary);
  color: var(--primary-text);
  border-color: var(--kb-yellow-dark);
}

.big-btn.secondary {
  background: var(--secondary);
  color: var(--text);
  border-color: var(--secondary-border);
}

.big-btn.danger {
  background: #fff;
  color: var(--danger);
  border-color: var(--danger);
}

.big-btn.xl {
  min-height: 96px;
  font-size: 30px;
  border-width: 4px;
}
</style>
