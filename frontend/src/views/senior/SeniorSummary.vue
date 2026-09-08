<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SeniorShell from '@/components/SeniorShell.vue'
import BigButton from '@/components/BigButton.vue'
import SummaryCard from '@/components/SummaryCard.vue'
import { getSummary, getSummaryStatus } from '@/api/backend'
import { tts } from '@/api/ai'
import { useConversation } from '@/composables/useConversation'
import { errorMessage } from '@/api/http'
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
let timer = null

async function load() {
  error.value = ''
  try {
    summary.value = await getSummary(route.params.id)
  } catch (e) {
    error.value = errorMessage(e)
  }
}

async function poll() {
  try {
    const s = await getSummaryStatus(route.params.id)
    status.value = s
    if (s.status === 'DONE' && !done.value) {
      done.value = true
      stopPolling()
      await load()
      const { audio_url } = await tts(DONE_TEXT, 'friendly')
      await player.play(audio_url)
    }
  } catch (e) {
    console.warn('[summary] status 폴링 실패', e)
  }
}

function stopPolling() {
  if (timer) clearInterval(timer)
  timer = null
}

function goHome() {
  player.stop()
  router.push('/mock/home')
}

onMounted(async () => {
  await load()
  await poll()
  if (!done.value) timer = setInterval(poll, POLL_MS)
})

onUnmounted(stopPolling)
</script>

<template>
  <SeniorShell title="창구 요약서" @stop="goHome">
    <div class="page">
      <div v-if="done" class="done">
        <div class="done-icon">✓</div>
        <p>{{ DONE_TEXT }}</p>
      </div>
      <p v-else class="lead">창구에서 이 화면을 보여주세요.</p>

      <div v-if="error" class="error-box">
        <p>{{ error }}</p>
        <BigButton kind="secondary" @click="load">다시 불러오기</BigButton>
      </div>

      <SummaryCard v-if="summary" :summary="summary" size="senior" />

      <p v-if="status" class="muted small">처리 {{ status.handled_count }} / {{ status.total_count }} · {{ statusLabel(status.status) }}</p>

      <div class="buttons">
        <BigButton kind="secondary" @click="conv.replayLast()">다시 들려주세요</BigButton>
        <BigButton kind="primary" @click="goHome">처음으로</BigButton>
      </div>
    </div>
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
  font-size: 18px;
  text-align: center;
}

.buttons {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>
