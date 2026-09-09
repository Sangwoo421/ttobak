<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SeniorShell from '@/components/SeniorShell.vue'
import ToneFrame from '@/components/ToneFrame.vue'
import BigButton from '@/components/BigButton.vue'
import SummaryCard from '@/components/SummaryCard.vue'
import { getSummary, getSummaryStatus } from '@/api/backend'
import { tts } from '@/api/ai'
import { useConversation } from '@/composables/useConversation'
import { seniorErrorMessage } from '@/api/http'
import { statusLabel } from '@/utils/format'

// 시연 4단계: 창구 요약서. GET /api/summaries/{id} + 3초마다 status 폴링.
// DONE 이 되면 "창구에서 처리됐어요. 수고하셨어요." 를 보여주고 TTS 로 한 번 읽는다.
const DONE_TEXT = '창구에서 처리됐어요. 수고하셨어요.'
const POLL_MS = 3000

const route = useRoute()
const router = useRouter()
const conv = useConversation()
const { player } = conv

const summary = ref(null)
const status = ref(null)
const error = ref('')
const done = ref(false)
const doneAudioUrl = ref(null)
let timer = null
let polling = false
let active = true

async function load() {
  error.value = ''
  try {
    summary.value = await getSummary(route.params.id)
  } catch (e) {
    error.value = seniorErrorMessage(e)
  }
}

async function poll() {
  if (!active || polling || done.value) return
  polling = true
  try {
    const s = await getSummaryStatus(route.params.id)
    if (!active) return
    status.value = s
    if (summary.value) summary.value = { ...summary.value, status: s.status }
    if (s.status === 'DONE' && !done.value) {
      done.value = true
      stopPolling()
      await load()
      if (!active) return
      try {
        const { audio_url } = await tts(DONE_TEXT, 'friendly')
        doneAudioUrl.value = audio_url
        if (active) await player.play(audio_url)
      } catch (e) {
        console.warn('[summary] 완료 음성 재생 실패', e)
      }
    }
  } catch (e) {
    console.warn('[summary] status 폴링 실패', e)
  } finally {
    polling = false
    if (active && !done.value) timer = setTimeout(poll, POLL_MS)
  }
}

function stopPolling() {
  if (timer) clearTimeout(timer)
  timer = null
}

async function replay() {
  if (done.value && doneAudioUrl.value) return player.play(doneAudioUrl.value)
  return conv.replayLast()
}

function goHome() {
  player.stop()
  router.push('/mock/home')
}

onMounted(async () => {
  await load()
  if (active) await poll()
})

onUnmounted(() => {
  active = false
  stopPolling()
  player.stop()
})
</script>

<template>
  <SeniorShell title="창구 요약서">
    <ToneFrame :tone="done ? 'friendly' : 'confirm'">
      <div class="page">
        <div v-if="done" class="done" role="status" aria-live="assertive">
          <div class="done-icon" aria-hidden="true">✓</div>
          <p>{{ DONE_TEXT }}</p>
        </div>
        <p v-else class="lead">창구에서 이 화면을 보여주세요.</p>

        <div v-if="error" class="error-box" role="alert">
          <p>{{ error }}</p>
          <BigButton kind="secondary" @click="load">다시 불러오기</BigButton>
        </div>

        <SummaryCard v-if="summary" :summary="summary" size="senior" />

        <p v-if="status" class="muted small" role="status">처리 {{ status.handled_count }} / {{ status.total_count }} · {{ statusLabel(status.status) }}</p>

        <div class="buttons">
          <BigButton kind="secondary" @click="replay">다시 들려주세요</BigButton>
          <BigButton kind="primary" @click="goHome">처음으로</BigButton>
        </div>
      </div>
    </ToneFrame>
  </SeniorShell>
</template>

<style scoped>
.page {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
}

.lead {
  font-size: var(--senior-font-lg);
  font-weight: 800;
  text-align: center;
  margin: 4px 0;
}

.done {
  background: var(--ok-bg);
  color: var(--ok);
  border: 4px solid var(--ok);
  border-radius: var(--radius);
  padding: 18px;
  text-align: center;
  font-size: var(--senior-font-lg);
  font-weight: 900;
}

.done p {
  margin: 0;
}

.done-icon {
  font-size: 48px;
  line-height: 1;
  margin-bottom: 6px;
}

.small {
  font-size: var(--senior-font);
  text-align: center;
}

.buttons {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>
