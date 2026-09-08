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
  <div class="staff">
    <div class="bar">
      <router-link to="/staff/summaries" class="back">← 목록</router-link>
      <h1 v-if="summary">
        번호표 {{ summary.ticket_no }}번 · {{ summary.user_name }} 님
        <span class="status-badge" :class="summary.status">{{ statusLabel(summary.status) }}</span>
      </h1>
      <h1 v-else>요약서</h1>
      <span v-if="saving" class="muted">저장 중…</span>
      <button class="btn" @click="load">새로고침</button>
    </div>

    <p v-if="summary" class="muted meta">접수 {{ dateTime(summary.created_at) }} · {{ summary.branch_name }} · 코드 <b class="mono">{{ summary.code }}</b></p>
    <p v-if="error" class="error-box">{{ error }}</p>

    <div v-if="summary" class="grid">
      <SummaryCard :summary="summary" size="staff" checkable @toggle="onToggle" />
      <aside class="help">
        <h3>처리 방법</h3>
        <ol>
          <li>"하려던 일"과 "여쭤볼 것"을 처리한 뒤 체크합니다.</li>
          <li>모두 체크되면 상태가 <b>처리 완료</b>로 바뀌고, 어르신 화면에 음성으로 안내됩니다.</li>
          <li>이체 실행은 이 시스템이 하지 않습니다. 창구 절차대로 진행하세요.</li>
        </ol>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.bar {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 6px;
}

.bar h1 {
  margin: 0;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
}

.back {
  color: var(--muted);
  text-decoration: none;
}

.meta {
  margin: 0 0 16px;
}

.mono {
  font-family: ui-monospace, Consolas, monospace;
  letter-spacing: 0.1em;
}

.grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(220px, 1fr);
  gap: 20px;
  align-items: start;
}

.help {
  background: #fffbe8;
  border: 1px solid #f1e3a0;
  border-radius: 12px;
  padding: 14px 18px;
  font-size: 14px;
}

.help h3 {
  margin: 0 0 8px;
}

.help ol {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

@media (max-width: 760px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
