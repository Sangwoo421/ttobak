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
    <!-- 앱 말풍선 위에만 이름표를 둔다. 누가 말했는지가 첫 줄에서 읽힌다. -->
    <span v-if="role === 'assistant'" class="who">또박또박</span>
    <div class="bubble" :class="[role, `tone-${tone}`]" :aria-label="role === 'assistant' ? `또박또박: ${text}` : `나: ${text}`">
      <p>{{ text }}</p>
    </div>
  </div>
</template>

<style scoped>
/* 꼬리를 그리지 않고 말한 쪽 아래 모서리만 각지게 해서 방향을 낸다.
   꼬리는 글자 크기가 커질수록 삐뚤어져 보이고, 어르신 화면은 글자가 크다. */
.bubble-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 14px 0;
}

.bubble-row.assistant {
  align-items: flex-start;
  max-width: 92%;
}

.bubble-row.user {
  align-items: flex-end;
  max-width: 84%;
  margin-left: auto;
}

.who {
  margin-left: 6px;
  font-size: 15px;
  font-weight: 700;
  color: var(--ink-4);
}

.bubble {
  padding: 18px 20px;
  font-size: var(--senior-font);
  line-height: 1.6;
  letter-spacing: -0.3px;
  word-break: keep-all;
}

.bubble p {
  margin: 0;
  white-space: pre-wrap;
}

.bubble.assistant {
  background: var(--card);
  border: 1px solid var(--card-line);
  border-radius: 22px 22px 22px 8px;
  color: var(--ink);
  box-shadow: 0 1px 2px rgba(23, 22, 26, 0.04), 0 6px 18px rgba(23, 22, 26, 0.04);
}

.bubble.user {
  background: var(--kb-yellow);
  border-radius: 22px 22px 8px 22px;
  color: var(--ink);
  box-shadow: 0 1px 2px rgba(120, 85, 0, 0.1), 0 6px 18px rgba(255, 188, 0, 0.22);
}

/* 확인 단계에서는 말풍선 자체가 달라져야 한다 (policy §3). 테두리를 진하게, 글자를 키운다. */
.bubble.assistant.tone-confirm {
  border: 3px solid var(--confirm-border);
  border-radius: 22px;
  color: var(--confirm-text);
  font-size: var(--senior-font-lg);
  font-weight: 700;
  box-shadow: none;
}
</style>
