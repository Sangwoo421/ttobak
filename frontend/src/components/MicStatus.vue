<script setup>
import { computed } from 'vue'

// 마이크 상태를 색 + 글로 표시 (policy §6).
const props = defineProps({
  status: { type: String, default: 'idle' }, // idle | listening | processing | speaking | off
  level: { type: Number, default: 0 }, // RMS 0~1 (듣는 중 미터)
})

const LABELS = {
  idle: '말씀하세요',
  listening: '듣고 있어요, 말씀하세요',
  processing: '생각 중이에요',
  speaking: '읽어드리는 중이에요',
  off: '',
}

const label = computed(() => LABELS[props.status] ?? props.status)
// 막대는 늘 같은 리듬으로 흔들리고, 목소리 크기는 그 진폭을 키운다.
// 소리가 없을 때 완전히 멈추면 "고장 났나" 싶어져서 최소 진폭을 남겨 둔다.
const amp = computed(() => Math.min(1.7, 0.62 + props.level * 2.4).toFixed(2))
</script>

<template>
  <div v-if="status !== 'off'" class="mic-status" :class="status" role="status" aria-live="polite">
    <!-- 듣는 중일 때만 움직인다. 화면에서 움직이는 것이 여기 하나뿐이라 눈이 바로 온다. -->
    <span v-if="status === 'listening'" class="bars" :style="{ transform: `scaleY(${amp})` }" aria-hidden="true">
      <span class="bar" /><span class="bar" /><span class="bar" /><span class="bar" />
    </span>
    <span v-else class="dot" aria-hidden="true" />
    <span class="label">{{ label }}</span>
  </div>
</template>

<style scoped>
.mic-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 24px;
  font-size: 18px;
  font-weight: 700;
  color: var(--ink-3);
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--ink-5);
  flex: none;
}

.bars {
  display: flex;
  align-items: center;
  gap: 3px;
  height: 18px;
  flex: none;
  transform-origin: center;
  transition: transform 0.08s linear;
}

.bar {
  width: 4px;
  border-radius: 2px;
  background: var(--ok);
  animation: bar 1.1s ease-in-out infinite;
}

.bar:nth-child(2) { animation-delay: 0.18s; }
.bar:nth-child(3) { animation-delay: 0.36s; }
.bar:nth-child(4) { animation-delay: 0.54s; }

@keyframes bar {
  0%, 100% { height: 6px; }
  50% { height: 18px; }
}

@media (prefers-reduced-motion: reduce) {
  .bar { animation: none; height: 14px; }
}

.mic-status.idle { color: var(--ink-3); }
.mic-status.listening { color: var(--ok); }
.mic-status.processing { color: var(--warn); }
.mic-status.speaking { color: #1a56b0; }

.mic-status.processing .dot,
.mic-status.speaking .dot {
  background: currentColor;
  animation: pulse 1.3s infinite;
}
</style>
