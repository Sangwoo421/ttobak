<script setup>
// 톤에 따라 화면 프레임이 바뀐다 (policy §3): confirm 이면 배경색·굵은 테두리.
defineProps({
  tone: { type: String, default: 'friendly' }, // friendly | confirm
})
</script>

<template>
  <div class="tone-frame" :class="`tone-${tone}`">
    <div v-if="tone === 'confirm'" class="confirm-label">확인해 주세요</div>
    <slot />
  </div>
</template>

<style scoped>
.tone-frame {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  transition: background 0.25s ease, border-color 0.25s ease;
  border: 0 solid transparent;
}

.tone-frame.tone-friendly {
  background: var(--bg);
}

.tone-frame.tone-confirm {
  background: var(--confirm-bg);
  border: 8px solid var(--confirm-border);
  color: var(--confirm-text);
}

.confirm-label {
  background: var(--confirm-border);
  color: #fff;
  text-align: center;
  font-weight: 900;
  font-size: 22px;
  padding: 6px;
  letter-spacing: 0.06em;
}
</style>
