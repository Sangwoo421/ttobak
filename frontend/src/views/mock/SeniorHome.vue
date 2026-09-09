<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { won } from '@/utils/format'
import { getTransactions } from '@/api/backend'
import { seniorErrorMessage } from '@/api/http'
import { useAudioPlayer } from '@/composables/useAudioPlayer'
import LevelBadge from '@/components/LevelBadge.vue'
import { useSessionStore } from '@/stores/session'

// 어르신 모드 홈. 일반 모드와 같은 데이터를 쓰지만 바뀌는 것은 글씨 크기만이 아니다.
//  - 거래 한 줄이 통째로 버튼이고, 누르면 그 건을 음성으로 읽고 바로 대화가 이어진다
//  - 무엇을 물어야 할지 몰라도 되도록, 할 수 있는 일을 큰 버튼 세 개로만 보여준다
//  - 확인 가능 / 일부 확인 / 확인 안 됨을 배지로 미리 알려, 앱이 뭘 모르는지 숨기지 않는다
// (담당 조태석·이성우 경계에 걸쳐 있음. docs/07-handoff.md 참고)
const props = defineProps({ account: { type: Object, required: true } })
const emit = defineEmits(['exit'])

const router = useRouter()
const player = useAudioPlayer()
const session = useSessionStore()

const items = ref([])
const loading = ref(true)
const error = ref('')
const transferNotice = ref('')

onMounted(async () => {
  try {
    items.value = await getTransactions(1, 6)
  } catch (e) {
    error.value = seniorErrorMessage(e)
  } finally {
    loading.value = false
  }
})

function go(path, query) {
  player.unlock() // 사용자 제스처 안에서 오디오를 깨워 둬야 이후 자동재생이 막히지 않는다
  router.push({ path, query })
}

const openBriefing = () => go('/senior/briefing')
// 「말로 물어보기」: 대화 화면으로 이동만 한다. 녹음은 사용자가 마이크를 눌러야 시작된다 (SeniorChat 이 처리).
const openChat = () => go('/senior/chat', { start: 'true' })
const openCounter = () => go('/branch-ticket')
const readOne = (it) => go('/senior/chat', { tx: String(it.transaction.id) })

function openSummary() {
  if (!session.latest_summary_id) {
    transferNotice.value = '아직 정리한 창구 요약서가 없어요. 말로 물어보기에서 창구 갈 일을 먼저 정리해 주세요.'
    return
  }
  go(`/senior/summary/${session.latest_summary_id}`)
}

function when(tx) {
  const d = new Date(tx.occurred_at)
  if (Number.isNaN(d.getTime())) return ''
  const today = new Date()
  const days = Math.round((new Date(today.toDateString()) - new Date(d.toDateString())) / 86400000)
  if (days === 0) return '오늘'
  if (days === 1) return '어제'
  if (days === 2) return '그저께'
  return `${days}일 전`
}
</script>

<template>
  <div class="senior-home">
    <header class="s-top">
      <div>
        <div class="s-mode">간편 모드</div>
        <div class="s-name">내 계좌</div>
      </div>
      <button type="button" class="s-off" @click="emit('exit')">모드 끄기</button>
    </header>

    <section class="s-balance">
      <div class="s-account-name">{{ account.name }}</div>
      <div class="s-account-number">{{ account.number }}</div>
      <div class="s-amount">{{ won(account.balance) }}</div>
    </section>

    <p v-if="transferNotice" class="s-notice" role="status">{{ transferNotice }}</p>

    <section class="s-actions">
      <button type="button" class="s-act primary" @click="openBriefing">
        <span class="s-act-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5 6 9H2v6h4l5 4V5z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/></svg>
        </span>
        <span class="txt"><b>들어오고 나간 돈 듣기</b><small>최근 것부터 읽어드려요</small></span>
      </button>
      <button type="button" class="s-act" @click="openChat">
        <span class="s-act-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3z"/><path d="M17 11a5 5 0 0 1-10 0"/><path d="M12 19v2"/></svg>
        </span>
        <span class="txt"><b>말로 물어보기</b><small>궁금한 걸 그냥 말씀하세요</small></span>
      </button>
      <button type="button" class="s-act summary" @click="openSummary">
        <span class="s-act-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 21V9l8-6 8 6v12"/><path d="M9 21v-6h6v6"/></svg>
        </span>
        <span class="txt"><b>창구 요약서 보기</b><small>정리해 둔 업무를 확인해요</small></span>
      </button>
      <button type="button" class="s-act" @click="openCounter">
        <span class="s-act-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>
        </span>
        <span class="txt"><b>지점·대기표 선택</b><small>번호표를 미리 받아요</small></span>
      </button>
    </section>

    <section class="s-list">
      <h3>들어오고 나간 돈</h3>
      <p class="s-help">궁금한 줄을 누르면 읽어드려요</p>

      <p v-if="loading" class="s-msg">불러오는 중이에요…</p>
      <p v-else-if="error" class="s-msg err">{{ error }}</p>

      <button
        v-for="it in items"
        :key="it.transaction.id"
        type="button"
        class="s-row"
        @click="readOne(it)"
      >
        <!-- 목록에는 통장에 찍히는 이름을 쓴다. spoken_name("'대한정보통신'이라는 곳")은 읽어줄 때의 말이라
             한 줄에 넣으면 줄바꿈이 지저분해진다. -->
        <span class="s-row-main">
          <span class="s-row-avatar" aria-hidden="true">{{ it.transaction.counterparty_name.charAt(0) }}</span>
          <span class="s-row-text">
            <b class="s-row-name">{{ it.transaction.counterparty_name }}</b>
            <span class="s-row-sub">
              {{ when(it.transaction) }}
              <LevelBadge :level="it.classification.level" />
            </span>
          </span>
        </span>
        <span class="s-row-right">
          <span class="s-amt" :class="it.transaction.type">
            {{ it.transaction.type === 'IN' ? '+' : '-' }}{{ won(it.transaction.amount) }}
          </span>
        </span>
      </button>
    </section>
  </div>
</template>

<style scoped>
.senior-home {
  --warn-bg: #efede7;
  --warn: #665c4c;
  background: #f5f5f3;
  min-height: 100%;
  padding-bottom: 28px;
  display: flex;
  flex-direction: column;
}

/* 헤더와 잔액은 한 덩어리로 보이게 해서 "모드가 바뀌었다"가 첫눈에 읽히게 한다 */
.s-top {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 12px;
  padding: 20px 18px 10px;
  background: #fff;
  border-bottom: 3px solid #ffbc00;
}
.s-mode {
  display: inline-block; font-size: 14px; font-weight: 800; color: #5d4a12;
  background: #fff; border: 2px solid #e1b52e; border-radius: 999px; padding: 3px 10px;
}
.s-name { font-size: 25px; font-weight: 900; color: #2b2620; margin-top: 6px; letter-spacing: -0.4px; }
.s-off {
  flex: none; min-height: 46px; padding: 0 15px;
  border: 2px solid #c8c0b1; border-radius: 999px;
  background: #fff;
  font-size: 16px; font-weight: 800; color: #4f493f; cursor: pointer;
}
.s-off:active { background: #efede7; }

.s-balance {
  margin: 16px 16px 4px;
  padding: 20px;
  background: var(--kb-yellow);
  border: 2px solid #d6a100;
  border-radius: 20px;
  box-shadow: 0 8px 22px rgba(97, 75, 0, 0.16);
}
.s-account-name {
  color: #332c20;
  font-size: 20px;
  font-weight: 900;
}
.s-account-number {
  margin-top: 2px;
  color: #64531d;
  font-size: 16px;
  font-weight: 700;
}
.s-amount {
  font-size: 42px; font-weight: 900; letter-spacing: -1.5px; margin-top: 18px;
  color: #2b2620; line-height: 1.1;
}
.s-notice {
  margin: 12px 16px 0;
  padding: 14px 16px;
  border: 2px solid #c8c0b1;
  border-radius: 14px;
  background: #fff;
  color: #4f493f;
  font-size: 18px;
  font-weight: 800;
  line-height: 1.45;
  word-break: keep-all;
}

/* 메뉴는 잔액 영역과 겹치지 않게 분리해 각 영역의 경계를 또렷하게 보여준다. */
.s-actions {
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding: 0 16px;
  margin-top: 16px; position: relative; z-index: 1;
}
.s-act {
  display: flex; flex-direction: column; align-items: flex-start; gap: 10px; width: 100%;
  min-height: 150px; padding: 16px; text-align: left;
  border: 2px solid #d9d3c7; border-radius: 18px; background: #fff; cursor: pointer;
  box-shadow: 0 4px 14px rgba(69, 58, 25, 0.08);
  transition: transform 0.08s ease;
}
.s-act:active { transform: scale(0.985); }
.s-act.primary { border-color: #d9b238; background: #fff; }
.s-act.summary { border-color: #d9b238; }
.s-act-icon {
  width: 44px; height: 44px; flex: none; border-radius: 12px;
  background: var(--kb-yellow-soft, #fff4cc); color: #8a6d00;
  display: flex; align-items: center; justify-content: center;
}
.s-act-icon svg { width: 22px; height: 22px; }
.s-act .txt { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.s-act b { font-size: 19px; font-weight: 900; color: #1b1b1b; letter-spacing: -0.3px; line-height: 1.25; }
.s-act small { font-size: 13px; color: #6b6455; line-height: 1.35; word-break: keep-all; }

.s-list { padding: 22px 16px 0; }
.s-list h3 { font-size: 23px; font-weight: 900; margin: 0 0 3px; letter-spacing: -0.4px; }
.s-help { font-size: 15px; color: #6b6455; margin: 0 0 14px; }
.s-msg { font-size: 18px; color: #6b6455; padding: 8px 2px; }
.s-msg.err { color: #b3261e; }

.s-row {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  width: 100%; min-height: 82px; padding: 14px 16px; margin-bottom: 10px;
  border: 2px solid #ded9cf; border-radius: 18px; background: #fff;
  text-align: left; cursor: pointer;
  box-shadow: 0 2px 8px rgba(69, 58, 25, 0.06);
  transition: transform 0.08s ease, background 0.12s ease;
}
.s-row:active { background: #f4f2ed; transform: scale(0.99); }
.s-row-main { display: flex; align-items: center; gap: 12px; min-width: 0; }
.s-row-avatar {
  width: 40px; height: 40px; flex: none; border-radius: 50%;
  background: #f1eee6; color: #8a6d00; font-size: 16px; font-weight: 900;
  display: flex; align-items: center; justify-content: center;
}
.s-row-text { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.s-row-name {
  font-size: 20px; font-weight: 900; color: #1b1b1b; letter-spacing: -0.3px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.s-row-sub { display: flex; align-items: center; gap: 8px; font-size: 15px; color: #7a7466; }
.s-row-right { display: flex; align-items: center; gap: 12px; flex: none; }
.s-amt { font-size: 19px; font-weight: 900; letter-spacing: -0.3px; }
.s-amt.IN { color: #1558d6; }
.s-amt.OUT { color: #1b1b1b; }
</style>
