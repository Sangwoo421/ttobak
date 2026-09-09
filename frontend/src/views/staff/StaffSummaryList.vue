<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listStaffSummaries } from '@/api/backend'
import { errorMessage } from '@/api/http'
import { dateTime, statusLabel } from '@/utils/format'

// 직원용 요약서 목록: GET /api/staff/summaries[?status=]
const router = useRouter()
const rows = ref([])
const filter = ref('')
const error = ref('')
const loading = ref(false)
const filters = [
  { value: '', label: '전체' },
  { value: 'OPEN', label: '접수됨' },
  { value: 'IN_PROGRESS', label: '처리 중' },
  { value: 'DONE', label: '처리 완료' },
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    rows.value = await listStaffSummaries(filter.value || undefined)
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(filter, load)
</script>

<template>
  <div class="staff staff-mobile">
    <header class="app-bar">
      <router-link to="/staff" class="icon-button" aria-label="창구 홈으로 돌아가기">‹</router-link>
      <div class="app-title">
        <span class="eyebrow">또박또박 직원</span>
        <h1>요약서 목록</h1>
      </div>
      <button type="button" class="icon-button refresh" aria-label="새로고침" :disabled="loading" @click="load">↻</button>
    </header>

    <nav class="filters" aria-label="처리 상태 필터">
      <button
        v-for="item in filters"
        :key="item.value"
        type="button"
        :class="{ active: filter === item.value }"
        @click="filter = item.value"
      >
        {{ item.label }}
      </button>
    </nav>

    <p v-if="error" class="error-box">{{ error }}</p>
    <p class="result-count">{{ loading ? '불러오는 중…' : `요약서 ${rows.length}건` }}</p>

    <div v-if="!loading && !rows.length" class="empty-state">
      <strong>표시할 요약서가 없습니다</strong>
      <span>다른 처리 상태를 선택해 보세요.</span>
    </div>

    <section v-else class="summary-list" aria-label="요약서 목록">
      <button v-for="r in rows" :key="r.id" type="button" class="summary-item" @click="router.push(`/staff/summaries/${r.id}`)">
        <span class="item-top">
          <span class="ticket">번호표 <b>{{ r.ticket_no }}</b>번</span>
          <span class="status-badge" :class="r.status">{{ statusLabel(r.status) }}</span>
        </span>
        <span class="customer-line">
          <strong>{{ r.user_name }} 고객님</strong>
          <span class="chevron" aria-hidden="true">›</span>
        </span>
        <span class="item-meta">
          <span>{{ dateTime(r.created_at) }}</span>
          <span>처리 항목 {{ r.item_count }}건</span>
        </span>
      </button>
    </section>
  </div>
</template>

<style scoped>
/* 창구 단말은 노트북이다. 폰 프레임을 뗀 뒤 요소가 화면 끝까지 늘어져 은행 업무 화면으로
   보이지 않아, 읽기 좋은 폭으로 잡고 가운데 둔다. 좁은 화면에서는 그대로 꽉 찬다. */
.staff-mobile {
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  min-height: 100%;
  flex: 1;
  padding: 0 16px 36px;
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
  min-height: 72px;
  margin: 0 -16px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.96);
  border-bottom: 1px solid #edf0f4;
  backdrop-filter: blur(10px);
}

.app-title {
  flex: 1;
  min-width: 0;
}

.app-title h1 {
  margin: 0;
  font-size: 22px;
  line-height: 1.2;
}

.eyebrow {
  display: block;
  margin-bottom: 2px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
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

.filters {
  display: flex;
  gap: 8px;
  margin: 16px 0 14px;
  overflow-x: auto;
  scrollbar-width: none;
}

.filters button {
  min-height: 40px;
  flex: none;
  padding: 8px 14px;
  border: 1px solid #cbd5df;
  border-radius: 999px;
  background: var(--card);
  color: #5f6f82;
  font-size: 14px;
  font-weight: 700;
}

.filters button.active {
  border: 2px solid #d4a300;
  background: #fff;
  color: #2b2620;
}

.result-count {
  margin: 0 2px 10px;
  color: var(--muted);
  font-size: 13px;
  font-weight: 700;
}

.summary-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.summary-item {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px;
  border: 2px solid #d4a300;
  border-radius: 15px;
  background: #fff;
  color: #2b2620;
  text-align: left;
  box-shadow: 0 10px 24px rgba(69, 58, 25, 0.1);
}

.summary-item:active {
  transform: scale(0.99);
}

.summary-item:focus-visible {
  outline: 3px solid rgba(212, 163, 0, 0.45);
  outline-offset: 3px;
}

.item-top,
.customer-line,
.item-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.ticket {
  color: #6b6458;
  font-size: 14px;
}

.ticket b {
  color: #2b2620;
  font-size: 18px;
}

.customer-line strong {
  font-size: 20px;
  color: #2b2620;
}

.chevron {
  color: #8a6a00;
  font-size: 30px;
  line-height: 1;
}

.item-meta {
  padding-top: 2px;
  color: #7a7469;
  font-size: 12px;
}

.summary-item .status-badge {
  border: 0;
}

.summary-item .status-badge.OPEN {
  background: #fff3d7;
  color: #895b08;
}

.summary-item .status-badge.IN_PROGRESS {
  background: #e7efff;
  color: #315f9b;
}

.summary-item .status-badge.DONE {
  background: #e7fff4;
  color: #14734f;
}

.empty-state {
  min-height: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--muted);
  text-align: center;
}

.empty-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  margin-bottom: 6px;
  border-radius: 50%;
  background: var(--ok-bg);
  color: var(--ok);
  font-size: 24px;
  font-weight: 900;
}

.empty-state strong {
  color: var(--text);
  font-size: 17px;
}

.empty-state span {
  font-size: 13px;
}

</style>
