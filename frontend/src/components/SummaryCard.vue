<script setup>
import { computed } from 'vue'
import { won, statusLabel } from '@/utils/format'

// 창구 요약서 카드. 어르신 화면(큰 글씨)과 직원 화면(체크박스) 공용.
const props = defineProps({
  summary: { type: Object, required: true }, // Summary (openapi-backend)
  size: { type: String, default: 'senior' }, // senior | staff
  checkable: { type: Boolean, default: false }, // 직원: REQUEST/QUESTION 체크박스
  showCode: { type: Boolean, default: true },
})
const emit = defineEmits(['toggle']) // (item, handled)

const requests = computed(() => props.summary.items.filter((i) => i.section === 'REQUEST').sort((a, b) => a.ordinal - b.ordinal))
const questions = computed(() => props.summary.items.filter((i) => i.section === 'QUESTION').sort((a, b) => a.ordinal - b.ordinal))
const preps = computed(() => props.summary.items.filter((i) => i.section === 'PREP').sort((a, b) => a.ordinal - b.ordinal))

const REQUEST_TYPE = { TRANSFER: '보내기(이체)' }
</script>

<template>
  <div class="summary-card" :class="size">
    <header v-if="showCode" class="head">
      <div class="code-label">창구 코드</div>
      <div class="code">{{ summary.code }}</div>
      <div class="meta">
        <span class="ticket">번호표 <b>{{ summary.ticket_no }}</b>번</span>
        <span class="branch">{{ summary.branch_name }}</span>
      </div>
      <div class="meta small">
        <span>{{ summary.user_name }} 님</span>
        <span class="status-badge" :class="summary.status">{{ statusLabel(summary.status) }}</span>
      </div>
    </header>

    <!-- 1. 창구에서 하려던 일 -->
    <section>
      <h2>창구에서 하려던 일</h2>
      <p v-if="!requests.length" class="muted">없음</p>
      <div v-for="item in requests" :key="item.id" class="item" :class="{ handled: item.handled }">
        <label v-if="checkable" class="check">
          <input type="checkbox" :checked="item.handled" @change="emit('toggle', item, $event.target.checked)" />
        </label>
        <div class="body">
          <div class="title">{{ REQUEST_TYPE[item.payload.type] || item.payload.type }}</div>
          <dl>
            <dt>받는 사람</dt>
            <dd>{{ item.payload.recipient_name }}</dd>
            <dt>관계</dt>
            <dd>{{ item.payload.recipient_relation || '-' }}</dd>
            <dt>은행</dt>
            <dd>{{ item.payload.recipient_bank || '-' }}</dd>
            <dt>계좌</dt>
            <dd>{{ item.payload.recipient_account_masked || '-' }}</dd>
            <dt>금액</dt>
            <dd class="amount">{{ won(item.payload.amount) }}</dd>
            <template v-if="item.payload.note">
              <dt>메모</dt>
              <dd>{{ item.payload.note }}</dd>
            </template>
          </dl>
        </div>
      </div>
    </section>

    <!-- 2. 창구에서 여쭤볼 것 -->
    <section>
      <h2>창구에서 여쭤볼 것</h2>
      <p v-if="!questions.length" class="muted">없음</p>
      <div v-for="item in questions" :key="item.id" class="item" :class="{ handled: item.handled }">
        <label v-if="checkable" class="check">
          <input type="checkbox" :checked="item.handled" @change="emit('toggle', item, $event.target.checked)" />
        </label>
        <div class="body">
          <div class="title">{{ item.payload.text }}</div>
          <div v-if="item.payload.transaction_id" class="muted sub">거래 #{{ item.payload.transaction_id }}</div>
        </div>
      </div>
    </section>

    <!-- 3. 준비물 -->
    <section>
      <h2>준비물</h2>
      <p v-if="!preps.length" class="muted">없음</p>
      <ul class="preps">
        <li v-for="item in preps" :key="item.id" :class="{ required: item.payload.required }">
          {{ item.payload.item }}<span v-if="item.payload.required" class="req">(꼭)</span>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.summary-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.head {
  background: var(--card);
  border-radius: var(--radius);
  padding: 18px;
  text-align: center;
  box-shadow: var(--shadow);
  border: 3px solid var(--kb-yellow);
}

.code-label {
  color: var(--muted);
  font-weight: 700;
}

.code {
  font-size: 64px;
  font-weight: 900;
  letter-spacing: 0.12em;
  line-height: 1.1;
  margin: 4px 0 8px;
  font-variant-numeric: tabular-nums;
}

.meta {
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
  font-weight: 700;
}

.meta.small {
  margin-top: 6px;
  font-size: 0.85em;
  color: var(--muted);
  align-items: center;
}

section {
  background: var(--card);
  border-radius: var(--radius);
  padding: 16px;
  box-shadow: var(--shadow);
}

section h2 {
  margin: 0 0 10px;
  font-size: 1.1em;
  font-weight: 900;
  border-left: 8px solid var(--kb-yellow);
  padding-left: 10px;
}

.item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-top: 1px solid var(--line);
}

.item:first-of-type {
  border-top: 0;
}

.item.handled .body {
  opacity: 0.5;
  text-decoration: line-through;
}

.check input {
  width: 28px;
  height: 28px;
  margin-top: 4px;
}

.body {
  flex: 1;
}

.title {
  font-weight: 800;
  margin-bottom: 6px;
}

dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 4px 14px;
  margin: 0;
}

dt {
  color: var(--muted);
  font-weight: 600;
}

dd {
  margin: 0;
  font-weight: 700;
}

dd.amount {
  font-size: 1.15em;
  font-weight: 900;
}

.sub {
  font-size: 0.8em;
}

.preps {
  margin: 0;
  padding-left: 22px;
}

.preps li.required {
  font-weight: 900;
}

.req {
  margin-left: 6px;
  color: var(--bad);
  font-size: 0.85em;
}

/* 직원 화면: 보통 크기 */
.summary-card.staff {
  font-size: 15px;
}

.summary-card.staff .code {
  font-size: 40px;
}

.summary-card.staff section h2 {
  font-size: 17px;
}

.summary-card.staff .head {
  text-align: left;
}

.summary-card.staff .meta {
  justify-content: flex-start;
}
</style>
