<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
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
import { useBranchTicketStore } from '@/stores/branchTicket'

// 시연 4단계: 창구 요약서. GET /api/summaries/{id} + 3초마다 status 폴링.
// DONE 이 되면 "창구에서 처리됐어요. 수고하셨어요." 를 보여주고 TTS 로 한 번 읽는다.
const DONE_TEXT = '창구에서 처리됐어요. 수고하셨어요.'
const POLL_MS = 3000

const route = useRoute()
const router = useRouter()
const conv = useConversation()
const { player } = conv
const branchTicket = useBranchTicketStore()

const summary = ref(null)
const status = ref(null)
const error = ref('')
const done = ref(false)
const doneAudioUrl = ref(null)
const progressPercent = computed(() => {
  if (!status.value?.total_count) return 0
  return Math.min(100, Math.round((status.value.handled_count / status.value.total_count) * 100))
})
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

function chooseBranch() {
  player.stop()
  router.push({ path: '/branch-ticket', query: { summary: route.params.id } })
}

async function syncActiveBranchTicket() {
  const summaryId = Number(route.params.id)
  if (!Number.isInteger(summaryId) || summaryId <= 0) return
  try {
    await branchTicket.load()
    if (branchTicket.ticket) {
      await branchTicket.issue({ purpose: '창구 요약서 업무', summary_id: summaryId })
    }
  } catch (e) {
    // 요약서 조회는 유지하되, 대기표 동기화 실패는 추후 재시도할 수 있게 로그만 남긴다.
    console.warn('[summary] 대기표 지점 동기화 실패', e)
  }
}

onMounted(async () => {
  conv.session.rememberSummary(route.params.id)
  await syncActiveBranchTicket()
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
    <ToneFrame class="summary-tone" :tone="done ? 'friendly' : 'confirm'">
      <div class="page">
        <div v-if="done" class="done" role="status" aria-live="assertive">
          <p>{{ DONE_TEXT }}</p>
        </div>
        <div v-else class="visit-guide">
          <div>
            <p class="guide-label">은행에 도착하면</p>
            <p class="lead">이 화면을 직원에게 보여주세요</p>
          </div>
        </div>

        <div v-if="error" class="error-box" role="alert">
          <p>{{ error }}</p>
          <BigButton kind="secondary" @click="load">다시 불러오기</BigButton>
        </div>

        <SummaryCard v-if="summary" :summary="summary" size="senior" />

        <div v-if="status" class="progress-card" :class="{ complete: done }" role="status">
          <div class="progress-head">
            <span>창구 처리 상태</span>
            <strong>{{ statusLabel(status.status) }}</strong>
          </div>
          <div
            class="progress-track"
            role="progressbar"
            aria-label="창구 처리 진행률"
            :aria-valuenow="progressPercent"
            aria-valuemin="0"
            aria-valuemax="100"
          >
            <span :style="{ width: `${progressPercent}%` }" />
          </div>
          <p>할 일 {{ status.total_count }}개 중 {{ status.handled_count }}개 처리됐어요</p>
        </div>

        <div class="buttons">
          <BigButton kind="primary" @click="chooseBranch">지점·대기표 선택</BigButton>
          <BigButton kind="secondary" @click="replay">안내 다시 듣기</BigButton>
          <BigButton kind="secondary" @click="goHome">간편 모드 홈</BigButton>
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
  gap: 16px;
  padding: 18px 14px 20px;
}

.visit-guide {
  display: block;
  padding: 16px;
  border: 2px solid #d9b238;
  border-radius: 20px;
  background: #fff;
}

.guide-label {
  margin: 0 0 2px;
  color: #6b6458;
  font-size: 17px;
  font-weight: 800;
}

.lead {
  margin: 0;
  color: #2b2620;
  font-size: 23px;
  font-weight: 900;
  line-height: 1.35;
  word-break: keep-all;
}

.done {
  background: linear-gradient(145deg, #edf9f0, #fff);
  color: var(--ok);
  border: 3px solid #76bf88;
  border-radius: 22px;
  padding: 22px 18px;
  text-align: center;
  font-size: var(--senior-font-lg);
  font-weight: 900;
}

.done p {
  margin: 0;
}

.progress-card {
  padding: 16px 18px;
  border: 2px solid #ded8c9;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 5px 18px rgba(67, 52, 16, 0.08);
}

.progress-card.complete {
  border-color: #76bf88;
  background: #f5fbf6;
}

.progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 20px;
  font-weight: 800;
}

.progress-head strong {
  color: #665219;
  white-space: nowrap;
}

.progress-card.complete .progress-head strong {
  color: var(--ok);
}

.progress-track {
  height: 12px;
  margin-top: 12px;
  overflow: hidden;
  border-radius: 999px;
  background: #ece9df;
}

.progress-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #d4a300;
  transition: width 0.3s ease;
}

.complete .progress-track span {
  background: var(--ok);
}

.progress-card p {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 18px;
  font-weight: 700;
}

.buttons {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

@media (max-width: 360px) {
  .visit-guide {
    padding: 14px;
  }

  .lead {
    font-size: 22px;
  }
}
</style>
