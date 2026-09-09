<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SeniorShell from '@/components/SeniorShell.vue'
import ToneFrame from '@/components/ToneFrame.vue'
import BigButton from '@/components/BigButton.vue'
import MicButton from '@/components/MicButton.vue'
import MicStatus from '@/components/MicStatus.vue'
import SpeechBubble from '@/components/SpeechBubble.vue'
import { useConversation } from '@/composables/useConversation'
import { seniorErrorMessage } from '@/api/http'

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
// 일반 상담은 ChatGPT처럼 글·음성으로 계속 이어간다.
// 따라서 중복되는 "더 물어보기"와 대화를 끊는 "그만"은 숨기고,
// 확인 단계의 선택과 창구 정리처럼 필요한 행동만 보여준다.
const consultationButtons = computed(() => session.mainButtons.filter((button) => {
  if (button.id === 'STOP') return false
  if (!isConfirm.value && button.id === 'ASK_MORE') return false
  return true
}))
const voiceGuide = computed(() => {
  if (conv.micStatus.value === 'listening') return '천천히 말씀하세요. 말씀을 마치면 자동으로 알아들어요.'
  if (conv.micStatus.value === 'processing') return '말씀하신 내용을 확인하고 있어요.'
  if (conv.micStatus.value === 'speaking') return '답변을 읽어드리고 있어요.'
  if (session.state === 'CLARIFY') return '다시 말씀하시거나, 아래에서 골라주세요.'
  if (isConfirm.value) return '내용이 맞는지 말하거나 큰 버튼으로 알려주세요.'
  return '마이크를 누르고 궁금한 내용을 말씀하세요.'
})

/** start=true 면 브리핑 없이 바로 대화. tx=101 이면 그 거래 한 건을 읽고 대화로 이어간다.
 *
 *  suppressAutoListen=true (홈의 「말로 물어보기」로 진입): 예고 없이 녹음이 시작되면 어르신이
 *  놀라고 첫 시도도 침묵·잡음으로 실패한다. 그래서 진입 시의 첫 자동 마이크만 막는다.
 *  대화가 시작된 뒤의 ui.listen 자동 마이크(되물은 뒤 등)는 그대로 둔다 — autoListen 을 원래대로 되돌린다.
 *  tx= 경로는 flag 를 주지 않으므로 지금 동작(읽어주고 바로 듣기)이 유지된다. */
async function startDirectChat({ transaction_id = null, suppressAutoListen = false } = {}) {
  starting.value = true
  startError.value = ''
  const prevAutoListen = conv.autoListen.value
  if (suppressAutoListen) conv.autoListen.value = false
  try {
    // 거래를 눌러 들어온 경우에는 그 건을 읽어줘야 하므로 음성을 재생한다.
    await conv.begin({ user_id: 1, transaction_id, playBriefing: !!transaction_id })
    await router.replace('/senior/chat')
  } catch (e) {
    startError.value = seniorErrorMessage(e)
  } finally {
    if (suppressAutoListen) conv.autoListen.value = prevAutoListen
    starting.value = false
  }
}

onMounted(() => {
  const tx = Number(route.query.tx)
  if (Number.isFinite(tx) && tx > 0) return startDirectChat({ transaction_id: tx })
  // 이미 진행 중인 대화가 있으면(예: 대기표 화면에서 "창구에서 할 일을 먼저 정리할래요"로
  // 돌아온 경우) 새 세션을 만들지 않고 이어간다 - 그래야 이미 담아둔 요청/질문이 안 날아간다.
  if (route.query.start === 'true' && !session.hasSession) return startDirectChat({ suppressAutoListen: true })
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
        <div class="conversation-panel">
          <div ref="listEl" class="messages" role="log" aria-live="polite" aria-relevant="additions text">
            <div v-if="startError" class="start-error" role="alert">
              <p>{{ startError }}</p>
              <BigButton kind="secondary" @click="startDirectChat">다시 연결하기</BigButton>
            </div>
            <p v-else-if="starting" class="starting">챗봇을 준비하고 있어요…</p>
            <SpeechBubble v-for="m in session.messages" :key="m.id" :role="m.role" :text="m.text" :tone="m.tone" />
            <p v-if="conv.hint.value" class="hint" role="alert">{{ conv.hint.value }}</p>
          </div>

          <form
            v-if="!startError && !conv.ended.value && !conv.stopping.value"
            class="text-composer"
            aria-label="글로 대화하기"
            @submit.prevent="sendText"
          >
            <label for="senior-chat-text" class="sr-only">궁금한 내용 입력</label>
            <input
              id="senior-chat-text"
              v-model="typedText"
              type="text"
              inputmode="text"
              autocomplete="off"
              placeholder="이 안에 글로 물어보세요"
              :disabled="disabled"
            />
            <button type="submit" :disabled="disabled || !typedText.trim()">보내기</button>
          </form>
        </div>

        <div v-if="!startError" class="bottom" :class="{ confirm: isConfirm }">
          <template v-if="conv.ended.value">
            <p class="end-text">다음에 또 불러 주세요</p>
            <BigButton kind="primary" @click="router.push('/mock/home')">홈으로</BigButton>
          </template>

          <template v-else-if="conv.stopping.value">
            <MicStatus status="processing" :level="0" />
            <p class="voice-guide">정리하고 있어요…</p>
          </template>

          <template v-else>
            <MicStatus :status="conv.micStatus.value" :level="recorder.level.value" />
            <p class="voice-guide">{{ voiceGuide }}</p>

            <!-- 말하는 것이 이 서비스의 주 입력 수단이다. 스크롤을 내려야 보이면 안 된다.
                 못 알아들었을 때(CLARIFY)도 숨기지 않는다 — 다시 말해 보는 게 가장 자연스러운
                 복구인데, 선택지 버튼만 남기면 그 길이 막힌다. -->
            <MicButton
              :status="conv.micStatus.value"
              :disabled="disabled"
              :size="isConfirm ? 'md' : 'lg'"
              :idle-label="session.state === 'CLARIFY' ? '다시 말하기' : ''"
              @click="conv.toggleMic()"
            />

            <div v-if="session.choices.length" class="choices">
              <BigButton v-for="c in session.choices" :key="c.id" kind="secondary" :disabled="disabled" @click="conv.pickChoice(c.id)">{{ c.label }}</BigButton>
            </div>

            <div v-if="consultationButtons.length" class="buttons" :class="{ two: isConfirm }">
              <BigButton
                v-for="b in consultationButtons"
                :key="b.id"
                :kind="b.kind || 'secondary'"
                :size="isConfirm ? 'xl' : 'lg'"
                :disabled="disabled"
                @click="conv.pressButton(b.id)"
              >
                {{ b.label }}
              </BigButton>
            </div>

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

.conversation-panel {
  flex: 1;
  min-height: 250px;
  display: flex;
  flex-direction: column;
  margin: 8px 12px 0;
  overflow: hidden;
  border: 2px solid #d8d2c7;
  border-radius: 20px;
  background: #f8f7f3;
  box-shadow: 0 4px 14px rgba(69, 58, 25, 0.07);
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px 14px;
  min-height: 150px;
  max-height: calc(100vh - 500px);
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
  padding: 10px;
  border-top: 2px solid #ddd7cc;
  background: #fff;
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
  color: var(--primary-text);
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
