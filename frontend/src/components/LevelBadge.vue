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
.level-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 18px;
  font-weight: 800;
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
