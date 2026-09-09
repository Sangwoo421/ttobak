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
//
// 시각 규칙(design/A_Chat.dc.html · A안 마감본): 대화는 회색 종이 위에 바로 놓인다(패널 테두리 없음).
// 하단은 흰 면 + 머리카락 선. 듣는 중 표시 → 검정 마이크 → 선택 버튼 → 글 입력 순.
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
// 거래 한 건을 눌러 들어왔을 때(브리핑 항목이 하나뿐) 어떤 알림을 듣고 있는지 위에 칩 하나로 남긴다.
const contextChip = computed(() => {
  const items = session.briefing?.items || []
  return items.length === 1 ? items[0].short_label : ''
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
  if (route.query.start === 'true') return startDirectChat({ suppressAutoListen: true })
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
    <template #right>
      <span v-if="session.counterCount" class="counter-pill" aria-label="창구 목록에 담긴 항목">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 6h13" /><path d="M8 12h13" /><path d="M8 18h13" /><path d="M3 6h.01" /><path d="M3 12h.01" /><path d="M3 18h.01" /></svg>
        창구 목록 {{ session.counterCount }}
      </span>
    </template>

    <ToneFrame :tone="session.tone">
      <div class="chat">
        <div ref="listEl" class="messages" role="log" aria-live="polite" aria-relevant="additions text">
          <div v-if="startError" class="start-error" role="alert">
            <p>{{ startError }}</p>
            <BigButton kind="secondary" @click="startDirectChat">다시 연결하기</BigButton>
          </div>
          <p v-else-if="starting" class="starting">챗봇을 준비하고 있어요…</p>
          <template v-else>
            <span v-if="contextChip" class="context-chip">듣고 있는 알림 · {{ contextChip }}</span>
            <SpeechBubble v-for="m in session.messages" :key="m.id" :role="m.role" :text="m.text" :tone="m.tone" />
          </template>
          <p v-if="conv.hint.value" class="hint" role="alert">{{ conv.hint.value }}</p>
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
            <p v-if="isConfirm || session.state === 'CLARIFY'" class="voice-guide">{{ voiceGuide }}</p>

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

            <form
              v-if="!isConfirm"
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
                placeholder="글로 물어보세요"
                :disabled="disabled"
              />
              <button type="submit" :disabled="disabled || !typedText.trim()">보내기</button>
            </form>
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

.counter-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 13px 8px 11px;
  border-radius: 999px;
  background: var(--warn-bg, #fff4d1);
  color: var(--warn, #8a5a00);
  font-size: 14px;
  font-weight: 700;
  white-space: nowrap;
}

.counter-pill svg {
  width: 17px;
  height: 17px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2.4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* 대화는 종이 위에 바로. 패널을 따로 두르지 않는다. */
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 18px 18px 14px;
  min-height: 150px;
  max-height: calc(100vh - 470px);
  display: flex;
  flex-direction: column;
}

.context-chip {
  align-self: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: #e9e7e0;
  color: var(--ink-3, #85817a);
  font-size: 13px;
  font-weight: 700;
  word-break: keep-all;
  text-align: center;
}

.hint {
  text-align: center;
  color: var(--bad);
  font-weight: 800;
  font-size: var(--senior-font);
  margin: 14px 0 0;
}

.starting,
.start-error {
  margin: 24px 0;
  padding: 18px;
  border-radius: 20px;
  background: #fff;
  border: 1px solid var(--card-line, #e9e6df);
  box-shadow: var(--soft, 0 1px 2px rgba(23, 22, 26, 0.04), 0 8px 24px rgba(23, 22, 26, 0.05));
  text-align: center;
  font-size: var(--senior-font);
  font-weight: 800;
}

.start-error {
  color: var(--bad);
  border-color: var(--bad);
}

.bottom {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 18px 22px;
  background: #fff;
  border-top: 1px solid #edebe5;
}

.bottom.confirm {
  background: transparent;
  border-top: 0;
}

.voice-guide {
  margin: -4px 4px 0;
  color: var(--ink-3, #85817a);
  font-size: 17px;
  font-weight: 700;
  line-height: 1.4;
  text-align: center;
  word-break: keep-all;
}

.bottom.confirm .voice-guide {
  color: var(--confirm-text);
  font-size: var(--senior-font);
  font-weight: 800;
}

.choices,
.buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 확인 단계의 예/아니오, 담기/아니요 같은 두 개짜리는 나란히 */
.buttons.two {
  flex-direction: row;
  gap: 10px;
}

.buttons.two > * {
  flex: 1;
}

.text-composer {
  display: flex;
  gap: 8px;
  align-items: stretch;
  padding-top: 2px;
}

.text-composer input {
  min-width: 0;
  min-height: 60px;
  flex: 1;
  border: 1px solid var(--secondary-border, #e6e3dc);
  border-radius: 15px;
  background: var(--field, #f8f7f4);
  color: var(--ink, #17161a);
  padding: 0 16px;
  font: inherit;
  font-size: 17px;
}

.text-composer input::placeholder {
  color: var(--ink-3, #85817a);
}

.text-composer button {
  min-height: 60px;
  flex: none;
  border: 1px solid var(--secondary-border, #e6e3dc);
  border-radius: 15px;
  background: #fff;
  color: #6b675e;
  padding: 0 20px;
  font-size: 17px;
  font-weight: 700;
}

.text-composer input:focus-visible,
.text-composer button:focus-visible {
  outline: 4px solid #1a56b0;
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
  font-size: var(--senior-font-lg);
  font-weight: 800;
  padding: 20px 0;
}
</style>
