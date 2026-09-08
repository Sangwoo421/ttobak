<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import SeniorShell from '@/components/SeniorShell.vue'
import ToneFrame from '@/components/ToneFrame.vue'
import BigButton from '@/components/BigButton.vue'
import MicButton from '@/components/MicButton.vue'
import MicStatus from '@/components/MicStatus.vue'
import SpeechBubble from '@/components/SpeechBubble.vue'
import LevelBadge from '@/components/LevelBadge.vue'
import { useConversation } from '@/composables/useConversation'

// 시연 3단계: 대화 화면. 말풍선 + 마이크 상태 + 큰 마이크 + ui.buttons(+ CLARIFY 면 choices).
// tone=confirm 이면 ToneFrame 이 화면 전체를 바꾸고 버튼은 맞아요/아니에요만 크게.
const router = useRouter()
const conv = useConversation()
const { session, recorder } = conv

const listEl = ref(null)
const isConfirm = computed(() => session.tone === 'confirm')
const disabled = computed(() => session.pending || conv.busy.value)

onMounted(() => {
  if (!session.hasSession) router.replace('/senior/briefing')
})

watch(
  () => [session.messages.length, conv.hint.value],
  () => nextTick(() => listEl.value?.scrollTo({ top: listEl.value.scrollHeight, behavior: 'smooth' })),
  { immediate: true },
)

function onStop() {
  if (conv.ended.value || !session.hasSession) return router.push('/mock/home')
  conv.pressButton('STOP')
}
</script>

<template>
  <SeniorShell :title="isConfirm ? '확인해 주세요' : '또박또박'" @stop="onStop">
    <ToneFrame :tone="session.tone">
      <div class="chat">
        <!-- 브리핑한 3건 (CONFIRM 톤에서는 숨겨 화면을 단순하게) -->
        <div v-if="!isConfirm && session.briefing?.items?.length" class="items-strip">
          <div v-for="it in session.briefing.items" :key="it.ordinal" class="chip">
            <span class="n">{{ it.ordinal }}</span>
            <span class="l">{{ it.short_label }}</span>
            <LevelBadge :level="it.level" />
          </div>
        </div>

        <div ref="listEl" class="messages">
          <SpeechBubble v-for="m in session.messages" :key="m.id" :role="m.role" :text="m.text" :tone="m.tone" />
          <p v-if="conv.hint.value" class="hint">{{ conv.hint.value }}</p>
        </div>

        <div class="bottom" :class="{ confirm: isConfirm }">
          <template v-if="conv.ended.value">
            <p class="end-text">다음에 또 불러 주세요</p>
            <BigButton kind="primary" @click="router.push('/mock/home')">처음으로</BigButton>
          </template>

          <template v-else>
            <MicStatus :status="conv.micStatus.value" :level="recorder.level.value" />

            <div v-if="session.choices.length" class="choices">
              <BigButton v-for="c in session.choices" :key="c.id" kind="secondary" :disabled="disabled" @click="conv.pickChoice(c.id)">{{ c.label }}</BigButton>
            </div>

            <div class="buttons" :class="{ two: isConfirm }">
              <BigButton
                v-for="b in session.mainButtons"
                :key="b.id"
                :kind="b.kind || 'secondary'"
                :size="isConfirm ? 'xl' : 'lg'"
                :disabled="disabled"
                @click="conv.pressButton(b.id)"
              >
                {{ b.label }}
              </BigButton>
            </div>

            <MicButton :status="conv.micStatus.value" :disabled="disabled" :size="isConfirm ? 'md' : 'lg'" @click="conv.toggleMic()" />
          </template>
        </div>
      </div>
    </ToneFrame>
  </SeniorShell>
</template>

<style scoped>
.chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.items-strip {
  display: flex;
  gap: 6px;
  padding: 10px 12px 4px;
  overflow-x: auto;
  scrollbar-width: none;
}

.chip {
  flex: none;
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 6px 10px 6px 6px;
  font-size: 16px;
  font-weight: 700;
}

.chip .n {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--kb-yellow);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
}

.chip :deep(.level-badge) {
  font-size: 13px;
  padding: 2px 8px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 8px 14px 16px;
  min-height: 160px;
  max-height: calc(100vh - 420px);
}

.hint {
  text-align: center;
  color: var(--bad);
  font-weight: 800;
  font-size: 20px;
  margin: 10px 0 0;
}

.bottom {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px 14px 16px;
  background: rgba(255, 255, 255, 0.5);
  border-top: 1px solid var(--line);
}

.bottom.confirm {
  background: transparent;
  border-top: 0;
}

.choices,
.buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.buttons.two {
  gap: 14px;
}

.end-text {
  text-align: center;
  font-size: var(--senior-font-xl);
  font-weight: 900;
  padding: 20px 0;
}
</style>
