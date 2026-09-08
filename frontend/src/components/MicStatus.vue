<script setup>
import { computed } from 'vue'

// 마이크 상태를 색 + 글로 표시 (policy §6).
const props = defineProps({
  status: { type: String, default: 'idle' }, // idle | listening | processing | speaking | off
  level: { type: Number, default: 0 }, // RMS 0~1 (듣는 중 미터)
})

const LABELS = {
  idle: '말씀하세요',
  listening: '듣고 있어요',
  processing: '생각 중이에요',
  speaking: '읽어드리는 중이에요',
  off: '',
}

const label = computed(() => LABELS[props.status] ?? props.status)
const meter = computed(() => Math.min(100, Math.round(props.level * 400)))
</script>

<template>
  <div v-if="status !== 'off'" class="mic-status" :class="status">
    <span class="dot" />
    <span class="label">{{ label }}</span>
    <span v-if="status === 'listening'" class="meter"><span class="fill" :style="{ width: meter + '%' }" /></span>
  </div>
</template>

<style scoped>
.mic-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 999px;
  font-size: var(--senior-font);
  font-weight: 800;
  background: #eee;
  color: #333;
}

.dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #999;
  flex: none;
}

.mic-status.idle {
  background: var(--ok-bg);
  color: var(--ok);
}

.mic-status.idle .dot {
  background: var(--ok);
}

.mic-status.listening {
  background: var(--bad-bg);
  color: var(--bad);
}

.mic-status.listening .dot {
  background: var(--bad);
  animation: pulse 1s infinite;
}

.mic-status.processing {
  background: var(--warn-bg);
  color: var(--warn);
}

.mic-status.processing .dot {
  background: var(--warn);
  animation: pulse 1.4s infinite;
}

.mic-status.speaking {
  background: #e3ecfb;
  color: #1a56b0;
}

.mic-status.speaking .dot {
  background: #1a56b0;
  animation: pulse 1.2s infinite;
}

.meter {
  flex: 1;
  height: 10px;
  background: rgba(0, 0, 0, 0.08);
  border-radius: 5px;
  overflow: hidden;
}

.meter .fill {
  display: block;
  height: 100%;
  background: var(--bad);
  transition: width 0.05s linear;
}
</style>
