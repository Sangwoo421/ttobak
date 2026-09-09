<script setup>
import { computed } from 'vue'
import { won, statusLabel } from '@/utils/format'

// 창구 요약서 카드. 어르신 화면(큰 글씨)과 직원 화면(체크박스) 공용.
const props = defineProps({
  summary: { type: Object, required: true }, // Summary (openapi-backend)
  size: { type: String, default: 'senior' }, // senior | staff
  checkable: { type: Boolean, default: false }, // 직원: REQUEST/QUESTION 체크박스
  showHeader: { type: Boolean, default: true },
})
const emit = defineEmits(['toggle']) // (item, handled)

const requests = computed(() => props.summary.items.filter((i) => i.section === 'REQUEST').sort((a, b) => a.ordinal - b.ordinal))
const questions = computed(() => props.summary.items.filter((i) => i.section === 'QUESTION').sort((a, b) => a.ordinal - b.ordinal))
const preps = computed(() => props.summary.items.filter((i) => i.section === 'PREP').sort((a, b) => a.ordinal - b.ordinal))
const REQUEST_TYPE = { TRANSFER: '보내기(이체)' }
</script>

<template>
  <div class="summary-card" :class="size">
    <header v-if="showHeader" class="head">
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
    <section class="request-section">
      <h2>창구에서 하려던 일</h2>
      <p v-if="!requests.length" class="muted">없음</p>
      <div v-for="item in requests" :key="item.id" class="item" :class="{ handled: item.handled }">
        <label v-if="checkable" class="check">
          <input type="checkbox" :checked="item.handled" @change="emit('toggle', item, $event.target.checked)" />
        </label>

        <!-- 어르신: 무엇을 / 누구에게 / 얼마 — 세 줄이면 충분하다. 표는 직원 화면에만. -->
        <div v-if="size === 'senior'" class="body senior-request">
          <div class="chip-row">
            <span class="type-chip">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></svg>
              {{ REQUEST_TYPE[item.payload.type] || item.payload.type }}
            </span>
            <span class="chip-note">{{ item.handled ? '처리됐어요' : '직원 확인 후 진행' }}</span>
          </div>
          <p class="to">
            <template v-if="item.payload.recipient_relation">{{ item.payload.recipient_relation }} </template>{{ item.payload.recipient_name }} 님에게
          </p>
          <p class="amount-row">
            <span class="amount-num num">{{ Number(item.payload.amount || 0).toLocaleString('ko-KR') }}</span><span class="amount-unit">원</span>
          </p>
          <p class="acct num">
            {{ item.payload.recipient_bank || '-' }}<template v-if="item.payload.recipient_account_masked"> · {{ item.payload.recipient_account_masked }}</template>
          </p>
          <p v-if="item.payload.note" class="note">{{ item.payload.note }}</p>
        </div>

        <div v-else class="body">
          <div class="title-row">
            <div class="title">{{ REQUEST_TYPE[item.payload.type] || item.payload.type }}</div>
            <span v-if="checkable" class="item-state">{{ item.handled ? '처리 완료' : '확인 필요' }}</span>
          </div>
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
    <section class="question-section">
      <h2>창구에서 여쭤볼 것</h2>
      <p v-if="!questions.length" class="muted">없음</p>
      <div v-for="item in questions" :key="item.id" class="item" :class="{ handled: item.handled }">
        <label v-if="checkable" class="check">
          <input type="checkbox" :checked="item.handled" @change="emit('toggle', item, $event.target.checked)" />
        </label>
        <div class="body">
          <div v-if="size === 'senior'" class="chip-row">
            <span class="ask-chip">{{ item.handled ? '답 들었어요' : '확인 안 됨' }}</span>
            <span v-if="item.payload.transaction_id" class="chip-note">앱에서 확인되지 않은 거래</span>
          </div>
          <div class="title-row">
            <div class="title">{{ item.payload.text }}</div>
            <span v-if="checkable" class="item-state">{{ item.handled ? '처리 완료' : '확인 필요' }}</span>
          </div>
          <div v-if="size !== 'senior' && item.payload.transaction_id" class="muted sub">거래 #{{ item.payload.transaction_id }}</div>
        </div>
      </div>
    </section>

    <!-- 3. 준비물 -->
    <section class="prep-section">
      <h2>{{ size === 'senior' ? '가져가실 것' : '준비물' }}</h2>
      <p v-if="!preps.length" class="muted">없음</p>
      <ul class="preps">
        <li v-for="item in preps" :key="item.id" :class="{ required: item.payload.required }">
          <span v-if="size === 'senior'" class="prep-mark" :class="{ on: item.payload.required }" aria-hidden="true">
            <svg v-if="item.payload.required" viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5" /></svg>
          </span>
          <span class="prep-name">{{ item.payload.item }}</span>
          <span v-if="item.payload.required" class="req">{{ size === 'senior' ? '꼭 필요해요' : '(필수)' }}</span>
          <span v-else-if="size === 'senior'" class="opt">있으면 좋아요</span>
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
  background: linear-gradient(145deg, #fffdf7 0%, #fff7d9 100%);
  border-radius: 22px;
  padding: 20px 18px;
  text-align: center;
  box-shadow: 0 8px 24px rgba(100, 76, 9, 0.1);
  border: 2px solid #e7bd3b;
}

.summary-card.senior .head {
  background: #fff;
  border-color: #d9b238;
  box-shadow: 0 8px 24px rgba(69, 58, 25, 0.1);
}

.meta {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
  font-weight: 700;
}

.summary-card.senior .ticket,
.summary-card.senior .branch {
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  padding: 5px 11px;
  border-radius: 999px;
}

.summary-card.senior .ticket {
  background: var(--kb-yellow);
  border: 2px solid #d4a300;
  color: #2b2620;
}

.summary-card.senior .branch {
  background: #fff;
  border: 1px solid #d9d3c7;
  color: #34495e;
}

.meta.small {
  margin-top: 10px;
  font-size: 0.85em;
  color: var(--muted);
  align-items: center;
}

.summary-card.senior .status-badge {
  padding: 5px 11px;
  font-size: 15px;
}

section {
  background: var(--card);
  border: 1px solid #d5dde6;
  border-radius: 20px;
  padding: 18px;
  box-shadow: 0 5px 18px rgba(36, 54, 77, 0.07);
}

section h2 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 14px;
  font-size: 1.05em;
  font-weight: 900;
  border: 0;
  padding: 0;
  color: #2b2620;
}

.summary-card.senior section h2::before {
  width: 34px;
  height: 34px;
  flex: none;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--kb-yellow);
  border: 2px solid #d4a300;
  color: #2b2620;
  font-size: 18px;
  font-weight: 900;
}

.summary-card.senior .request-section h2::before {
  content: '1';
}

.summary-card.senior .question-section h2::before {
  content: '2';
}

.summary-card.senior .prep-section h2::before {
  content: '3';
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
  min-width: 0;
}

.title {
  font-weight: 800;
  line-height: 1.45;
  margin-bottom: 6px;
}

.title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.item-state {
  flex: none;
  padding: 4px 7px;
  border-radius: 999px;
  background: #fff1df;
  color: #b36500;
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
}

dl {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  gap: 8px 12px;
  margin: 0;
}

dt {
  color: var(--muted);
  font-weight: 600;
}

dd {
  margin: 0;
  font-weight: 700;
  overflow-wrap: anywhere;
}

dd.amount {
  font-size: 1.15em;
  font-weight: 900;
  color: #665219;
}

.sub {
  font-size: 0.8em;
}

.preps {
  margin: 0;
  padding: 0;
  list-style: none;
}

.summary-card.senior .preps li {
  display: flex;
  align-items: center;
  min-height: 48px;
  padding: 8px 0;
  border-top: 1px solid #e1e7ed;
}

.summary-card.senior .preps li:first-child {
  border-top: 0;
}

.summary-card.senior .preps li::before {
  width: 10px;
  height: 10px;
  flex: none;
  display: grid;
  place-items: center;
  margin-right: 10px;
  border-radius: 50%;
  background: var(--ok);
  content: '';
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
  width: auto;
  max-width: none;
  margin: 0 16px;
  padding: 0;
  gap: 0;
  font-size: 15px;
}

.summary-card.staff section h2 {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 12px;
  padding: 0;
  border: 0;
  font-size: 16px;
  letter-spacing: -0.02em;
}

.summary-card.staff section {
  padding: 20px 0;
  border: 0;
  border-top: 1px solid #d9dde3;
  border-radius: 0;
  background: #fff;
  box-shadow: none;
}

.summary-card.staff section h2::before {
  width: 4px;
  height: 18px;
  border-radius: 999px;
  background: #758bf3;
  content: '';
}

.summary-card.staff .question-section h2::before {
  background: #3e9ee6;
}

.summary-card.staff .prep-section h2::before {
  background: #38aa87;
}

.summary-card.staff .item {
  gap: 8px;
  padding: 14px 0 4px;
  border-top: 0;
}

.summary-card.staff .item + .item {
  margin-top: 14px;
  border-top: 1px solid #edf0f3;
}

.summary-card.staff .check {
  width: 44px;
  height: 44px;
  flex: none;
  display: grid;
  place-items: center;
  margin-top: -4px;
}

.summary-card.staff .check input {
  width: 24px;
  height: 24px;
  margin: 0;
  accent-color: #2f6fed;
}

.summary-card.staff dl {
  grid-template-columns: 82px minmax(0, 1fr);
  gap: 8px 10px;
  margin-top: 8px;
  padding-left: 2px;
}

.summary-card.staff dt {
  color: #a2a7af;
  font-size: 13px;
}

.summary-card.staff dd {
  text-align: right;
}

.summary-card.staff dd.amount {
  color: #ec6267;
}

.summary-card.staff .item.handled .body {
  opacity: 1;
  text-decoration: none;
}

.summary-card.staff .item.handled .title {
  color: #727982;
}

.summary-card.staff .item.handled .item-state {
  background: #e9f8f1;
  color: #218261;
}

.summary-card.staff .preps {
  padding: 0;
  list-style: none;
}

.summary-card.staff .preps li {
  display: flex;
  align-items: center;
  min-height: 42px;
  border-top: 1px solid #edf0f3;
}

.summary-card.staff .preps li::before {
  width: 8px;
  height: 8px;
  margin-right: 10px;
  border-radius: 50%;
  background: #228566;
  content: '';
}

.summary-card.staff .req {
  margin-left: auto;
  padding: 4px 7px;
  border-radius: 999px;
  background: #fff0ef;
  color: #d75555;
  font-size: 11px;
}

.summary-card.staff .head {
  text-align: left;
}

.summary-card.staff .meta {
  justify-content: flex-start;
}

@media (max-width: 380px) {
  .summary-card.staff dl {
    grid-template-columns: 70px minmax(0, 1fr);
  }
}

/* ============================================================ 어르신 화면 (A안 마감본)
   구획은 작은 회색 라벨 + 흰 카드. 번호·선·그림자 장식은 없다. 상태는 알약 하나.
   아래 규칙이 위의 senior 규칙보다 뒤에 있어 이긴다. */
.summary-card.senior {
  gap: 22px;
}

.summary-card.senior .num { font-variant-numeric: tabular-nums; }

.summary-card.senior section {
  padding: 20px 22px 22px;
  border: 1px solid var(--card-line, #e9e6df);
  border-radius: 20px;
  background: #fff;
  box-shadow: var(--soft, 0 1px 2px rgba(23, 22, 26, 0.04), 0 8px 24px rgba(23, 22, 26, 0.05));
}

.summary-card.senior section h2 {
  margin: 0 0 14px;
  padding: 0;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.4px;
  color: var(--ink-4, #9a968c);
}

.summary-card.senior section h2::before { content: none; }

.summary-card.senior .item {
  padding: 0;
  border-top: 0;
}

.summary-card.senior .item + .item {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--hairline, #f0eeea);
}

.summary-card.senior .item.handled .body {
  opacity: 0.55;
  text-decoration: none;
}

.summary-card.senior .muted {
  margin: 0;
  font-size: 18px;
  color: var(--ink-3, #85817a);
}

.summary-card.senior .chip-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.summary-card.senior .type-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px 6px 10px;
  border-radius: 999px;
  background: var(--kb-yellow, #ffbc00);
  color: var(--ink, #17161a);
  font-size: 14px;
  font-weight: 800;
}

.summary-card.senior .type-chip svg {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.summary-card.senior .ask-chip {
  padding: 5px 11px;
  border-radius: 999px;
  background: var(--bad-bg, #fdecec);
  color: var(--bad, #c5221f);
  font-size: 14px;
  font-weight: 700;
}

.summary-card.senior .item.handled .ask-chip {
  background: var(--ok-bg);
  color: var(--ok);
}

.summary-card.senior .chip-note {
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-5, #b3afa6);
  text-align: right;
  word-break: keep-all;
}

.summary-card.senior .to {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.5px;
  color: var(--ink, #17161a);
  word-break: keep-all;
}

.summary-card.senior .amount-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin: 0 0 12px;
  color: var(--ink, #17161a);
}

.summary-card.senior .amount-num {
  font-size: 36px;
  font-weight: 800;
  letter-spacing: -1.4px;
  line-height: 1.1;
}

.summary-card.senior .amount-unit {
  font-size: 22px;
  font-weight: 700;
}

.summary-card.senior .acct {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--ink-3, #85817a);
}

.summary-card.senior .note {
  margin: 8px 0 0;
  font-size: 16px;
  color: var(--ink-2, #4a463f);
}

.summary-card.senior .question-section .title {
  margin: 0;
  font-size: 21px;
  font-weight: 800;
  line-height: 1.5;
  letter-spacing: -0.4px;
  color: var(--ink, #17161a);
  word-break: keep-all;
}

.summary-card.senior .prep-section {
  padding: 4px 22px;
}

.summary-card.senior .prep-section h2 {
  margin: 16px 0 6px;
}

.summary-card.senior .preps li {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 60px;
  padding: 14px 0;
  border-top: 1px solid var(--hairline, #f0eeea);
  font-size: 21px;
  font-weight: 700;
  letter-spacing: -0.4px;
  color: var(--ink-2, #4a463f);
}

.summary-card.senior .preps li.required {
  font-weight: 800;
  color: var(--ink, #17161a);
}

.summary-card.senior .preps li::before { content: none; }

.summary-card.senior .prep-mark {
  flex: none;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid #d9d5cc;
  display: flex;
  align-items: center;
  justify-content: center;
}

.summary-card.senior .prep-mark.on {
  border-color: var(--ok);
  background: var(--ok);
}

.summary-card.senior .prep-mark svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: #fff;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.summary-card.senior .prep-name { flex: 1; }

.summary-card.senior .req {
  margin-left: auto;
  font-size: 14px;
  font-weight: 800;
  color: var(--bad, #c5221f);
}

.summary-card.senior .opt {
  margin-left: auto;
  font-size: 14px;
  font-weight: 600;
  color: var(--ink-5, #b3afa6);
}

</style>
