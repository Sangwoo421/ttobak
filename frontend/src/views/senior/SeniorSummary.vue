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
//
// 시각 규칙(design/A_Summary.dc.html · A안 마감본): 맨 위 검정 카드에 6자리 코드를 칸으로 나눠
// 직원이 한 번에 읽게 한다. 아래는 회색 라벨 + 흰 카드 세 구획(하려던 일·여쭤볼 것·가져가실 것).
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
const codeDigits = computed(() => String(summary.value?.code || '').split(''))
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
    <template #right>
      <span class="staff-tag">직원용</span>
    </template>

    <!-- 요약서는 확인 단계가 아니라 결과다. confirm 톤의 굵은 틀은 대화 화면에만 남긴다. -->
    <ToneFrame tone="friendly">
      <div class="page">
        <div v-if="done" class="done" role="status" aria-live="assertive">
          <span class="done-check" aria-hidden="true">
            <svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5" /></svg>
          </span>
          <p>{{ DONE_TEXT }}</p>
        </div>

        <div v-if="error" class="error-box" role="alert">
          <p>{{ error }}</p>
          <BigButton kind="secondary" @click="load">다시 불러오기</BigButton>
        </div>

        <!-- 코드 카드: 직원에게 보여줄 것 하나. 이 화면에서 가장 진한 면. -->
        <section v-if="summary" class="code-card" aria-label="창구 요약서 번호">
          <div class="code-head">
            <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="3" /><path d="M7 9h4" /><path d="M7 13h10" /></svg>
            <p>직원에게 이 번호를 보여주세요</p>
          </div>
          <div class="code-digits num" :aria-label="`요약서 번호 ${summary.code}`">
            <span v-for="(d, i) in codeDigits" :key="i">{{ d }}</span>
          </div>
          <div class="code-meta">
            <div>
              <p class="meta-label">번호표</p>
              <span class="ticket-chip num">{{ summary.ticket_no }}번</span>
            </div>
            <div>
              <p class="meta-label">지점</p>
              <p class="meta-value">{{ summary.branch_name }}</p>
            </div>
          </div>
        </section>

        <SummaryCard v-if="summary" :summary="summary" size="senior" :show-header="false" />

        <section v-if="status" class="progress-card" :class="{ complete: done }" role="status">
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
          <p class="num">할 일 {{ status.total_count }}개 중 {{ status.handled_count }}개 처리됐어요</p>
        </section>

        <p class="foot-note">
          <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="11" width="16" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg>
          이체는 앱이 아니라 창구에서 직원이 도와드려요
        </p>

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
  gap: 20px;
  padding: 6px 18px 24px;
}

.num { font-variant-numeric: tabular-nums; }

.staff-tag {
  padding: 7px 12px;
  border-radius: 999px;
  background: var(--paper, #f3f2ee);
  color: var(--ink-3, #85817a);
  font-size: 13px;
  font-weight: 700;
}

/* ------------------------------------------------------------ 코드 카드 */
.code-card {
  margin: 8px 0 2px;
  padding: 24px 22px 22px;
  border-radius: 24px;
  background: var(--ink, #17161a);
  color: #fff;
  box-shadow: 0 14px 34px rgba(23, 22, 26, 0.22);
}

.code-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.code-head svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: var(--kb-yellow, #ffbc00);
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.code-head p {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #cfcbc1;
}

.code-digits {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 7px;
}

.code-digits span {
  height: 62px;
  border-radius: 14px;
  background: #2a2925;
  color: #fff;
  font-size: 34px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.code-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid #333029;
}

.code-meta > div {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meta-label {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: #8f8a7f;
}

.meta-value {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: #fff;
  line-height: 1.4;
  word-break: keep-all;
}

.ticket-chip {
  align-self: flex-start;
  padding: 5px 12px;
  border-radius: 999px;
  background: var(--kb-yellow, #ffbc00);
  color: var(--ink, #17161a);
  font-size: 18px;
  font-weight: 800;
}

/* ------------------------------------------------------------ 완료 */
.done {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 8px;
  padding: 18px 20px;
  border-radius: 20px;
  background: var(--ok-bg);
  color: var(--ok);
  font-size: var(--senior-font);
  font-weight: 800;
  line-height: 1.4;
  word-break: keep-all;
}

.done p { margin: 0; }

.done-check {
  flex: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--ok);
  display: flex;
  align-items: center;
  justify-content: center;
}

.done-check svg {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: #fff;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* ------------------------------------------------------------ 처리 상태 */
.progress-card {
  padding: 18px 22px 20px;
  border: 1px solid var(--card-line, #e9e6df);
  border-radius: 20px;
  background: #fff;
  box-shadow: var(--soft, 0 1px 2px rgba(23, 22, 26, 0.04), 0 8px 24px rgba(23, 22, 26, 0.05));
}

.progress-card.complete {
  border-color: #cfe6d5;
  background: #f5fbf6;
}

.progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 17px;
  font-weight: 700;
  color: var(--ink-3, #85817a);
}

.progress-head strong {
  color: var(--warn, #8a5a00);
  background: var(--warn-bg, #fff4d1);
  padding: 4px 11px;
  border-radius: 999px;
  font-size: 14px;
  white-space: nowrap;
}

.progress-card.complete .progress-head strong {
  color: var(--ok);
  background: var(--ok-bg);
}

.progress-track {
  height: 10px;
  margin-top: 14px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--paper, #f3f2ee);
}

.progress-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--kb-yellow, #ffbc00);
  transition: width 0.3s ease;
}

.complete .progress-track span {
  background: var(--ok);
}

.progress-card p {
  margin: 10px 0 0;
  color: var(--ink, #17161a);
  font-size: 18px;
  font-weight: 700;
}

.foot-note {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  margin: 0;
  color: var(--ink-4, #9a968c);
  font-size: 15px;
  font-weight: 600;
  text-align: center;
  word-break: keep-all;
}

.foot-note svg {
  flex: none;
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.buttons {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

@media (max-width: 360px) {
  .code-digits span {
    height: 54px;
    font-size: 28px;
  }
}
</style>
