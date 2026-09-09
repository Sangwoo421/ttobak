<script setup>
import { levelLabel } from '@/utils/format'

// classification.level 배지: CONFIRMED 확인됨 / PARTIAL 일부 확인 / UNKNOWN 확인 안 됨
defineProps({
  level: { type: String, default: 'UNKNOWN' },
})
</script>

<template>
  <span class="level-badge" :class="level">{{ levelLabel(level) }}</span>
</template>

<style scoped>
/* 상태는 색 면적을 작게 가져간다. 거래 이름(21px)이 주인공이고 이 배지는 곁말이라
   같은 크기로 키우면 줄이 두 개의 제목처럼 읽힌다. 내용은 어차피 음성으로도 나간다. */
.level-badge {
  display: inline-block;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 15px;
  font-weight: 700;
  white-space: nowrap;
}

.level-badge.CONFIRMED {
  background: var(--ok-bg);
  color: var(--ok);
}

.level-badge.PARTIAL {
  background: var(--warn-bg);
  color: var(--warn);
}

.level-badge.UNKNOWN {
  background: var(--bad-bg);
  color: var(--bad);
}
</style>
