<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SeniorShell from '@/components/SeniorShell.vue'
import ToneFrame from '@/components/ToneFrame.vue'
import BigButton from '@/components/BigButton.vue'
import MicButton from '@/components/MicButton.vue'
import MicStatus from '@/components/MicStatus.vue'
import SpeechBubble from '@/components/SpeechBubble.vue'
import LevelBadge from '@/components/LevelBadge.vue'
import { useConversation } from '@/composables/useConversation'
import { errorMessage } from '@/api/http'

// 시연 3단계: 대화 화면. 말풍선 + 마이크 상태 + 큰 마이크 + ui.buttons(+ CLARIFY 면 choices).
// tone=confirm 이면 ToneFrame 이 화면 전체를 바꾸고 버튼은 맞아요/아니에요만 크게.
const router = useRouter()
const route = useRoute()
const conv = useConversation()
const { session, recorder } = conv

const listEl = ref(null)
const typedText = ref('')
const starting = ref(false)
const startError = ref('')
const isConfirm = computed(() => session.tone === 'confirm')
const disabled = computed(() => starting.value || session.pending || conv.busy.value)
const voiceGuide = computed(() => {
  if (conv.micStatus.value === 'listening') return '천천히 말씀하세요. 말씀을 마치면 자동으로 알아들어요.'
  if (conv.micStatus.value === 'processing') return '말씀하신 내용을 확인하고 있어요.'
  if (conv.micStatus.value === 'speaking') return '답변을 읽어드리고 있어요.'
  if (session.state === 'CLARIFY') return '아래에서 하려던 일을 골라주세요.'
  if (isConfirm.value) return '내용이 맞는지 말하거나 큰 버튼으로 알려주세요.'
  return '마이크를 누르고 궁금한 내용을 말씀하세요.'
})

/** start=true 면 브리핑 없이 바로 대화. tx=101 이면 그 거래 한 건을 읽고 대화로 이어간다. */
async function startDirectChat({ transaction_id = null } = {}) {
  starting.value = true
  startError.value = ''
  try {
    // 거래를 눌러 들어온 경우에는 그 건을 읽어줘야 하므로 음성을 재생한다.
    await conv.begin({ user_id: 1, transaction_id, playBriefing: !!transaction_id })
    await router.replace('/senior/chat')
  } catch (e) {
    startError.value = errorMessage(e)
  } finally {
    starting.value = false
  }
}

/** 홈에서 "창구 갈 일 정리"로 바로 들어온 경우: 세션을 열고 곧장 요약서로 간다. */
async function startCounter() {
  await startDirectChat()
  if (!startError.value) await conv.pressButton('GO_COUNTER')
}

onMounted(() => {
  const tx = Number(route.query.tx)
  if (Number.isFinite(tx) && tx > 0) return startDirectChat({ transaction_id: tx })
  if (route.query.counter === 'true') return startCounter()
  if (route.query.start === 'true') return startDirectChat()
  if (!session.hasSession) router.replace('/senior/briefing')
})

watch(
  () => [session.messages.length, conv.hint.value],
  () => nextTick(() => listEl.value?.scrollTo({ top: listEl.value.scrollHeight, behavior: 'smooth' })),
  { immediate: true },
)

async function sendText() {
  const text = typedText.value.trim()
  if (!text || disabled.value) return
  typedText.value = ''
  await conv.sendTypedText(text)
}
</script>

<template>
  <SeniorShell :title="isConfirm ? '확인해 주세요' : '물어보기'">
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

        <div ref="listEl" class="messages" role="log" aria-live="polite" aria-relevant="additions text">
          <div v-if="startError" class="start-error" role="alert">
            <p>{{ startError }}</p>
            <BigButton kind="secondary" @click="startDirectChat">다시 연결하기</BigButton>
          </div>
          <p v-else-if="starting" class="starting">챗봇을 준비하고 있어요…</p>
          <SpeechBubble v-for="m in session.messages" :key="m.id" :role="m.role" :text="m.text" :tone="m.tone" />
          <p v-if="conv.hint.value" class="hint" role="alert">{{ conv.hint.value }}</p>
        </div>

        <div v-if="!startError" class="bottom" :class="{ confirm: isConfirm }">
          <template v-if="conv.ended.value">
            <p class="end-text">다음에 또 불러 주세요</p>
            <BigButton kind="primary" @click="router.push('/mock/home')">홈으로</BigButton>
          </template>

          <template v-else>
            <MicStatus :status="conv.micStatus.value" :level="recorder.level.value" />
            <p class="voice-guide">{{ voiceGuide }}</p>

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

            <form class="text-composer" aria-label="글로 대화하기" @submit.prevent="sendText">
              <label for="senior-chat-text" class="sr-only">궁금한 내용 입력</label>
              <input
                id="senior-chat-text"
                v-model="typedText"
                type="text"
                inputmode="text"
                autocomplete="off"
                placeholder="여기에 글로 물어보세요"
                :disabled="disabled"
              />
              <button type="submit" :disabled="disabled || !typedText.trim()">보내기</button>
            </form>

            <MicButton
              v-if="session.state !== 'CLARIFY'"
              :status="conv.micStatus.value"
              :disabled="disabled"
              :size="isConfirm ? 'md' : 'lg'"
              @click="conv.toggleMic()"
            />
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
  font-size: var(--senior-font);
  font-weight: 700;
}

.chip .n {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--kb-yellow);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
}

.chip :deep(.level-badge) {
  font-size: 18px;
  padding: 4px 8px;
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
  font-size: var(--senior-font);
  margin: 10px 0 0;
}

.starting,
.start-error {
  margin: 24px 0;
  padding: 18px;
  border-radius: var(--radius);
  background: var(--card);
  box-shadow: var(--shadow);
  text-align: center;
  font-size: var(--senior-font);
  font-weight: 800;
}

.start-error {
  color: var(--bad);
  border: 3px solid var(--bad);
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

.voice-guide {
  margin: -2px 4px 2px;
  color: var(--muted);
  font-size: var(--senior-font);
  font-weight: 700;
  line-height: 1.4;
  text-align: center;
  word-break: keep-all;
}

.bottom.confirm .voice-guide {
  color: var(--confirm-text);
  font-weight: 900;
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

.text-composer {
  display: flex;
  gap: 8px;
  align-items: stretch;
}

.text-composer input {
  min-width: 0;
  min-height: 72px;
  flex: 1;
  border: 3px solid var(--secondary-border);
  border-radius: var(--radius);
  background: #fff;
  color: var(--text);
  padding: 12px 14px;
  font: inherit;
  font-size: var(--senior-font);
}

.text-composer input::placeholder {
  color: var(--muted);
}

.text-composer button {
  min-height: 72px;
  flex: none;
  border: 3px solid var(--kb-yellow-dark);
  border-radius: var(--radius);
  background: var(--kb-yellow);
  color: #1b1b1b;
  padding: 10px 16px;
  font-size: var(--senior-font);
  font-weight: 900;
}

.text-composer input:focus-visible,
.text-composer button:focus-visible {
  outline: 5px solid #1a56b0;
  outline-offset: 2px;
}

.text-composer input:disabled,
.text-composer button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.end-text {
  text-align: center;
  font-size: var(--senior-font-xl);
  font-weight: 900;
  padding: 20px 0;
}
</style>
