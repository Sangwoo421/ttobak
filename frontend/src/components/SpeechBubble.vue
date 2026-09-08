<script setup>
// 말풍선. 음성 응답 텍스트는 항상 화면에도 크게 (policy §6 청각 보조).
defineProps({
  role: { type: String, required: true }, // assistant | user
  text: { type: String, default: '' },
  tone: { type: String, default: 'friendly' },
})
</script>

<template>
  <div class="bubble-row" :class="role">
    <div class="bubble" :class="[role, `tone-${tone}`]">
      <span v-if="role === 'assistant'" class="who">또박또박</span>
      <p>{{ text }}</p>
    </div>
  </div>
</template>

<style scoped>
.bubble-row {
  display: flex;
  margin: 8px 0;
}

.bubble-row.assistant {
  justify-content: flex-start;
}

.bubble-row.user {
  justify-content: flex-end;
}

.bubble {
  max-width: 92%;
  padding: 14px 18px;
  border-radius: 20px;
  font-size: var(--senior-font);
  line-height: 1.45;
  box-shadow: var(--shadow);
  word-break: keep-all;
}

.bubble p {
  margin: 0;
  white-space: pre-wrap;
}

.bubble.assistant {
  background: var(--card);
  border-bottom-left-radius: 6px;
}

.bubble.user {
  background: var(--kb-yellow-soft);
  border-bottom-right-radius: 6px;
}

.bubble.assistant.tone-confirm {
  background: #fff;
  border: 3px solid var(--confirm-border);
  color: var(--confirm-text);
  font-size: var(--senior-font-lg);
  font-weight: 700;
}

.who {
  display: block;
  font-size: 14px;
  color: var(--muted);
  margin-bottom: 4px;
  font-weight: 700;
}
</style>
