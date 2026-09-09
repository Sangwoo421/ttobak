<script setup>
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import SeniorShell from '@/components/SeniorShell.vue'
import BigButton from '@/components/BigButton.vue'
import { useBranchTicketStore } from '@/stores/branchTicket'
import { errorMessage } from '@/api/http'

const router = useRouter()
const route = useRoute()
const store = useBranchTicketStore()
const { branches, selectedBranch, selectedBranchId, ticket, loading } = storeToRefs(store)
const error = ref('')
const cancelling = ref(false)
const summaryId = computed(() => {
  const value = Number(route.query.summary)
  return Number.isInteger(value) && value > 0 ? value : null
})

const ticketStatus = computed(() => ({
  WAITING: '차례를 기다리고 있어요',
  CALLED: '지금 창구로 가세요',
  DONE: '상담이 끝났어요',
  CANCELLED: '취소한 대기표예요',
}[ticket.value?.status] || '상태를 확인하고 있어요'))

async function load() {
  error.value = ''
  try {
    await store.load()
    // 요약서가 대화 시작 과정에서 초기화됐어도 현재 대기표의 지점을 다시 반영한다.
    if (summaryId.value && ticket.value) {
      await store.issue({ purpose: '창구 요약서 업무', summary_id: summaryId.value })
    }
  } catch (e) {
    error.value = errorMessage(e)
  }
}

async function issue() {
  if (!selectedBranchId.value) return
  error.value = ''
  try {
    await store.issue({
      purpose: summaryId.value ? '창구 요약서 업무' : '일반 상담',
      summary_id: summaryId.value,
    })
  } catch (e) {
    error.value = errorMessage(e)
  }
}

async function cancel() {
  error.value = ''
  try {
    await store.cancel()
    cancelling.value = false
  } catch (e) {
    error.value = errorMessage(e)
  }
}

function openCounterChat() {
  router.push({ path: '/senior/chat', query: { start: 'true' } })
}

onMounted(load)
</script>

<template>
  <SeniorShell title="은행 대기표">
    <div class="ticket-page">
      <div v-if="error" class="error-box" role="alert">
        <p>{{ error }}</p>
        <BigButton kind="secondary" @click="load">다시 불러오기</BigButton>
      </div>

      <p v-if="loading && !branches.length && !ticket" class="loading">은행 지점을 찾고 있어요…</p>

      <template v-else-if="ticket">
        <section class="ticket-card" aria-labelledby="ticket-title">
          <div class="ticket-label">모바일 번호표</div>
          <p id="ticket-title" class="ticket-number"><span>{{ ticket.ticket_no }}</span>번</p>
          <p class="ticket-status">{{ ticketStatus }}</p>

          <div class="wait-grid">
            <div><span>내 앞에</span><strong>{{ ticket.ahead_count }}명</strong></div>
            <div><span>예상 대기</span><strong>약 {{ ticket.estimated_wait_minutes }}분</strong></div>
          </div>

          <div class="ticket-branch">
            <div>
              <b>{{ ticket.branch_name }}</b>
              <span>{{ ticket.branch_address }}</span>
            </div>
          </div>

        </section>

        <aside class="arrival-note">
          <b>은행에 도착하면</b>
          <span>번호표를 다시 뽑지 말고 이 화면을 보여주세요.</span>
        </aside>

        <div v-if="cancelling" class="cancel-confirm" role="alertdialog" aria-labelledby="cancel-title">
          <p id="cancel-title">이 대기표를 취소할까요?</p>
          <div>
            <BigButton kind="danger" :disabled="loading" @click="cancel">취소할게요</BigButton>
            <BigButton kind="secondary" :disabled="loading" @click="cancelling = false">아니요</BigButton>
          </div>
        </div>

        <div v-else class="ticket-actions">
          <BigButton kind="primary" @click="router.push('/mock/home')">홈으로</BigButton>
          <BigButton kind="secondary" @click="cancelling = true">대기표 취소</BigButton>
        </div>
      </template>

      <template v-else>
        <section class="intro">
          <div>
            <h2>방문할 지점을 골라주세요</h2>
            <p>대기 인원이 적은 순서로 확인할 수 있어요.</p>
          </div>
        </section>

        <p class="demo-label">시연용 대기 현황</p>

        <div class="branch-list">
          <button
            v-for="branch in branches"
            :key="branch.id"
            type="button"
            class="branch-card"
            :class="{ selected: selectedBranchId === branch.id }"
            :aria-pressed="selectedBranchId === branch.id"
            @click="store.select(branch.id)"
          >
            <span class="select-mark" aria-hidden="true" />
            <span class="branch-copy">
              <b>{{ branch.name.replace('KB국민은행 ', '') }}</b>
              <small>{{ branch.address }} · {{ branch.opening_hours }}</small>
            </span>
            <span class="branch-wait">
              <strong>{{ branch.waiting_count }}명</strong>
              <small>약 {{ branch.estimated_wait_minutes }}분</small>
            </span>
          </button>
        </div>

        <div class="selection-summary" :class="{ empty: !selectedBranch }">
          <template v-if="selectedBranch">
            <span>선택한 지점</span>
            <b>{{ selectedBranch.name.replace('KB국민은행 ', '') }}</b>
          </template>
          <span v-else>먼저 방문할 지점을 눌러주세요</span>
        </div>

        <div class="issue-actions">
          <BigButton kind="primary" :disabled="!selectedBranch || loading" @click="issue">
            {{ loading ? '대기표를 받고 있어요…' : '이 지점 대기표 받기' }}
          </BigButton>
          <button type="button" class="counter-link" @click="openCounterChat">창구에서 할 일을 먼저 정리할래요 →</button>
        </div>
      </template>
    </div>
  </SeniorShell>
</template>

<style scoped>
.ticket-page {
  min-height: 100%;
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
  background: #f5f5f3;
}

.loading {
  margin: auto;
  color: var(--muted);
  font-size: 22px;
  font-weight: 800;
  text-align: center;
}

.intro {
  display: block;
  padding: 15px;
  border: 2px solid #d9b238;
  border-radius: 18px;
  background: #fff;
}

.intro h2 {
  margin: 0 0 3px;
  font-size: 23px;
}

.intro p {
  margin: 0;
  color: #6b6458;
  font-size: 16px;
}

.demo-label {
  align-self: flex-start;
  margin: 0;
  padding: 4px 10px;
  border-radius: 999px;
  background: #efede5;
  color: #746e61;
  font-size: 14px;
  font-weight: 800;
}

.branch-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.branch-card {
  min-height: 94px;
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 13px 14px;
  border: 2px solid #d9d3c7;
  border-radius: 18px;
  background: #fff;
  color: #2b2620;
  text-align: left;
  box-shadow: 0 3px 12px rgba(69, 58, 25, 0.06);
}

.branch-card.selected {
  border: 3px solid #d4a300;
  background: #fff;
}

.select-mark {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border: 2px solid #b8b09e;
  border-radius: 50%;
}

.selected .select-mark {
  border-color: #d4a300;
  box-shadow: inset 0 0 0 6px #fff;
  background: #d4a300;
}

.branch-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.branch-copy b {
  font-size: 20px;
  line-height: 1.3;
  word-break: keep-all;
}

.branch-copy small {
  overflow: hidden;
  color: #777064;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.branch-wait {
  display: flex;
  flex: none;
  flex-direction: column;
  align-items: flex-end;
}

.branch-wait strong {
  color: #665219;
  font-size: 20px;
}

.branch-wait small {
  color: #7b7466;
  font-size: 14px;
}

.selection-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 54px;
  padding: 10px 14px;
  border-radius: 14px;
  background: #efede7;
  font-size: 17px;
}

.selection-summary b { text-align: right; }
.selection-summary.empty { justify-content: center; color: #777064; }

.issue-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: auto;
}

.counter-link {
  min-height: 52px;
  border: 0;
  background: transparent;
  color: #5f510f;
  font-size: 17px;
  font-weight: 800;
  text-decoration: underline;
  text-underline-offset: 4px;
}

.ticket-card {
  overflow: hidden;
  border: 3px solid #d4a300;
  border-radius: 24px;
  background: #fff;
  box-shadow: 0 12px 30px rgba(69, 58, 25, 0.14);
  text-align: center;
}

.ticket-label {
  padding: 10px;
  background: #fff;
  color: #2b2620;
  border-bottom: 2px solid #d4a300;
  font-size: 18px;
  font-weight: 900;
  letter-spacing: 0.04em;
}

.ticket-number {
  margin: 20px 0 0;
  font-size: 30px;
  font-weight: 900;
}

.ticket-number span {
  margin-right: 5px;
  color: #2c271b;
  font-size: 82px;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.ticket-status {
  margin: 6px 0 18px;
  color: #665219;
  font-size: 22px;
  font-weight: 900;
}

.wait-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  margin: 0 18px;
  overflow: hidden;
  border: 1px solid #ded9cf;
  border-radius: 16px;
  background: #fff;
}

.wait-grid > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 13px 8px;
}

.wait-grid > div + div { border-left: 1px solid #ded9cf; }
.wait-grid span { color: #716a5c; font-size: 15px; }
.wait-grid strong { font-size: 24px; }

.ticket-branch {
  display: block;
  margin-top: 18px;
  padding: 16px 18px;
  border-top: 1px dashed #c8b97f;
  text-align: left;
}

.ticket-branch div { display: flex; flex-direction: column; min-width: 0; }
.ticket-branch b { font-size: 20px; word-break: keep-all; }
.ticket-branch div span { color: #746d60; font-size: 15px; }

.arrival-note {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 15px 17px;
  border-radius: 16px;
  background: #efede7;
  color: #4f493f;
}

.arrival-note b { font-size: 19px; }
.arrival-note span { font-size: 16px; }

.ticket-actions,
.cancel-confirm > div {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ticket-actions { margin-top: auto; }

.cancel-confirm {
  margin-top: auto;
  padding: 16px;
  border: 3px solid var(--danger);
  border-radius: 18px;
  background: #fff;
}

.cancel-confirm p {
  margin: 0 0 12px;
  font-size: 22px;
  font-weight: 900;
  text-align: center;
}

@media (max-width: 360px) {
  .ticket-page { padding: 12px; }
  .branch-card { grid-template-columns: 26px minmax(0, 1fr); }
  .branch-wait { grid-column: 2; flex-direction: row; gap: 8px; align-items: center; }
  .ticket-number span { font-size: 68px; }
}
</style>
