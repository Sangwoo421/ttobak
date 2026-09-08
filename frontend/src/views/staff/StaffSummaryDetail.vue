<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import SummaryCard from '@/components/SummaryCard.vue'
import { getSummary, patchSummaryItem } from '@/api/backend'
import { errorMessage } from '@/api/http'
import { dateTime, statusLabel } from '@/utils/format'

// 시연 6단계: 항목별 체크 → PATCH /api/staff/summaries/{id}/items/{item_id} {handled} → 돌려받은 Summary 로 다시 그림.
// 모든 REQUEST/QUESTION 이 처리되면 서버가 status=DONE 으로 바꾸고, 어르신 화면이 폴링으로 알아챈다.
const route = useRoute()
const summary = ref(null)
const error = ref('')
const saving = ref(false)

async function load() {
  error.value = ''
  try {
    summary.value = await getSummary(route.params.id)
  } catch (e) {
    error.value = errorMessage(e)
  }
}

async function onToggle(item, handled) {
  saving.value = true
  error.value = ''
  try {
    summary.value = await patchSummaryItem(summary.value.id, item.id, handled)
  } catch (e) {
    error.value = errorMessage(e)
    await load() // 체크박스 상태를 서버 기준으로 되돌린다
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="staff staff-mobile">
    <header class="app-bar">
      <router-link to="/staff/summaries" class="icon-button" aria-label="요약서 목록으로 돌아가기">‹</router-link>
      <h1>요약서 상세</h1>
      <button type="button" class="icon-button refresh" aria-label="새로고침" :disabled="saving" @click="load">↻</button>
    </header>

    <p v-if="error" class="error-box">{{ error }}</p>

    <template v-if="summary">
      <section class="customer-card">
        <div class="customer-top">
          <span class="ticket">번호표 <b>{{ summary.ticket_no }}</b>번</span>
          <span class="status-badge" :class="summary.status">{{ statusLabel(summary.status) }}</span>
        </div>
        <p class="card-guide">고객님의 방문 업무를 확인해 주세요.</p>
        <h2>{{ summary.user_name }} 고객님</h2>
        <div class="code-box">
          <span>창구 확인 코드</span>
          <strong class="mono">{{ summary.code }}</strong>
        </div>
        <dl class="summary-meta">
          <div>
            <dt>접수 시각</dt>
            <dd>{{ dateTime(summary.created_at) }}</dd>
          </div>
          <div>
            <dt>방문 지점</dt>
            <dd>{{ summary.branch_name }}</dd>
          </div>
        </dl>
      </section>

      <details class="help">
        <summary>처리 방법 안내</summary>
        <ol>
          <li>"하려던 일"과 "여쭤볼 것"을 처리한 뒤 체크합니다.</li>
          <li>모두 체크되면 상태가 <b>처리 완료</b>로 바뀌고, 어르신 화면에 음성으로 안내됩니다.</li>
          <li>이체 실행은 이 시스템이 하지 않습니다. 창구 절차대로 진행하세요.</li>
        </ol>
      </details>

      <SummaryCard :summary="summary" size="staff" :show-code="false" checkable @toggle="onToggle" />
    </template>
  </div>
</template>

<style scoped>
.staff-mobile {
  width: 100%;
  max-width: none;
  min-height: 100%;
  flex: 1;
  padding: 0 0 36px;
  background: #fff;
  overflow-x: hidden;
}

.app-bar {
  position: sticky;
  top: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 64px;
  margin: 0 0 16px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.96);
  border-bottom: 1px solid #edf0f4;
  backdrop-filter: blur(10px);
}

.app-bar h1 {
  margin: 0;
  flex: 1;
  font-size: 20px;
  text-align: center;
}

.icon-button {
  width: 44px;
  height: 44px;
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--muted);
  font-size: 32px;
  line-height: 1;
  text-decoration: none;
}

.icon-button:active {
  background: var(--line);
}

.icon-button.refresh {
  color: var(--text);
  font-size: 26px;
}

.icon-button:disabled {
  opacity: 0.45;
}

.customer-card {
  margin: 0 16px 18px;
  padding: 20px;
  border: 0;
  border-radius: 15px;
  background: linear-gradient(150deg, #26364f 0%, #324963 52%, #405a78 100%);
  box-shadow: 0 12px 28px rgba(25, 43, 65, 0.22);
  color: #fff;
}

.customer-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.ticket {
  color: rgba(255, 255, 255, 0.78);
  font-size: 14px;
}

.ticket b {
  color: #fff;
  font-size: 20px;
}

.customer-card .status-badge {
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
}

.customer-card .status-badge.DONE {
  border-color: transparent;
  background: #e7fff4;
  color: #14734f;
}

.card-guide {
  margin: 23px 0 6px;
  color: #b8d8df;
  font-size: 13px;
  font-weight: 700;
}

.customer-card h2 {
  margin: 0 0 18px;
  font-size: 24px;
  letter-spacing: -0.03em;
}

.code-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.22);
  border-bottom: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 0;
  background: transparent;
  color: rgba(255, 255, 255, 0.82);
  font-size: 13px;
  font-weight: 700;
}

.code-box .mono {
  color: #8fe3d3;
  font-family: ui-monospace, Consolas, monospace;
  font-size: 28px;
  letter-spacing: 0.12em;
  text-shadow: 0 2px 10px rgba(10, 24, 40, 0.24);
}

.summary-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 14px 0 0;
}

.summary-meta div {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 10px;
}

.summary-meta dt {
  color: rgba(255, 255, 255, 0.68);
  font-size: 13px;
  font-weight: 600;
}

.summary-meta dd {
  margin: 0;
  overflow-wrap: anywhere;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
}

.help {
  margin: 0 16px 18px;
  padding: 14px 16px;
  border: 1px solid #63aee0;
  border-radius: 10px;
  background: #fff;
  color: var(--muted);
  font-size: 13px;
}

.help summary {
  min-height: 28px;
  color: var(--text);
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
}

.help ol {
  margin: 12px 0 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

</style>
