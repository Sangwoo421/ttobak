<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { won } from '@/utils/format'
import { getTransactions, getBriefing } from '@/api/backend'
import { unheardBadge, unheardCountFromBriefing } from '@/utils/notifications'
import { tts } from '@/api/ai'
import { seniorErrorMessage } from '@/api/http'
import { useAudioPlayer } from '@/composables/useAudioPlayer'
import LevelBadge from '@/components/LevelBadge.vue'
import { useSessionStore } from '@/stores/session'
import { useAuthStore } from '@/stores/auth'

// 어르신 모드 홈. 일반 모드와 같은 데이터를 쓰지만 바뀌는 것은 글씨 크기만이 아니다.
//  - 거래 한 줄이 통째로 버튼이고, 누르면 그 건을 음성으로 읽고 바로 대화가 이어진다
//  - 무엇을 물어야 할지 몰라도 되도록, 할 수 있는 일을 큰 버튼으로만 보여준다
//  - 확인 가능 / 일부 확인 / 확인 안 됨을 알약으로 미리 알려, 앱이 뭘 모르는지 숨기지 않는다
// 시각 규칙(design/Main.dc.html · A안 마감본): 장식 없이 여백·글자 크기·흰 카드로 층을 만든다.
// 색은 노랑 하나, 나머지는 검정과 회색 단계. 카드는 1px 테두리 + 아주 옅은 그림자 두 겹.
// (담당 조태석·이성우 경계에 걸쳐 있음. docs/07-handoff.md 참고)
const props = defineProps({ account: { type: Object, required: true } })
const emit = defineEmits(['exit'])

const router = useRouter()
const player = useAudioPlayer()
const session = useSessionStore()
const auth = useAuthStore()

const items = ref([])
const loading = ref(true)
const error = ref('')
const notice = ref('')
const reading = ref(false)
const unheard = ref(0)

const userName = computed(() => auth.userName || '고객')
// 이름 첫 글자는 성이라 구분이 안 된다. "김영자" → "영" 처럼 이름의 첫 글자를 쓴다.
const initial = computed(() => {
  const n = userName.value.trim()
  return n.length >= 2 ? n[1] : n[0] || ''
})
// 뱃지와 부제는 미청취 알림 개수(countUnheard)만 본다. 홈 목록(items)의 길이가 아니다.
const briefingBadge = computed(() => unheardBadge(unheard.value))

onMounted(() => {
  loadTransactions()
  loadUnheard()
})

// 홈 목록: 청취 여부와 무관한 최근 거래. 화면 본문이라 실패하면 에러를 띄운다.
async function loadTransactions() {
  try {
    items.value = await getTransactions(1, 6)
  } catch (e) {
    error.value = seniorErrorMessage(e)
  } finally {
    loading.value = false
  }
}

// 뱃지용 미청취 개수. 못 받으면 0 으로 둬서 뱃지를 숨긴다 (틀린 숫자보다 안 보이는 게 낫다).
async function loadUnheard() {
  try {
    unheard.value = unheardCountFromBriefing(await getBriefing(1))
  } catch {
    unheard.value = 0
  }
}

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
    notice.value = '아직 정리한 창구 요약서가 없어요. 말로 물어보기에서 창구 갈 일을 먼저 정리해 주세요.'
    return
  }
  go(`/senior/summary/${session.latest_summary_id}`)
}

/** 잔액 읽어주기: 이 앱의 핵심 동작(들어서 아는 것)을 첫 화면에서 바로. 서버 턴 없이 TTS 만 쓴다. */
async function readBalance() {
  if (reading.value) return
  reading.value = true
  notice.value = ''
  try {
    player.unlock()
    const { audio_url } = await tts(`${props.account.name} 지금 잔액은 ${won(props.account.balance)}이에요.`, 'friendly')
    await player.play(audio_url)
  } catch (e) {
    notice.value = seniorErrorMessage(e)
  } finally {
    reading.value = false
  }
}

function when(tx) {
  const d = new Date(tx.occurred_at)
  if (Number.isNaN(d.getTime())) return ''
  const today = new Date()
  const days = Math.round((new Date(today.toDateString()) - new Date(d.toDateString())) / 86400000)
  const part = d.getHours() < 12 ? '오전' : '오후'
  if (days === 0) return `오늘 ${part}`
  if (days === 1) return `어제 ${part}`
  if (days === 2) return '그저께'
  return `${days}일 전`
}
</script>

<template>
  <div class="senior-home">
    <header class="s-top">
      <span class="s-avatar" aria-hidden="true">{{ initial }}</span>
      <div class="s-who">
        <p class="s-name">{{ userName }} 님</p>
        <span class="s-mode"><i class="dot" />간편 모드 켜짐</span>
      </div>
      <button type="button" class="s-off" @click="emit('exit')">모드 끄기</button>
    </header>

    <section class="s-balance-wrap">
      <div class="s-balance">
        <div class="s-balance-head">
          <div>
            <p class="s-account-name">{{ account.name }}</p>
            <p class="s-account-number num">{{ account.number }}</p>
          </div>
          <span class="s-fresh">방금 확인</span>
        </div>
        <p class="s-balance-label">지금 잔액</p>
        <div class="s-amount">
          <span class="num">{{ Number(account.balance).toLocaleString('ko-KR') }}</span>
          <span class="unit">원</span>
        </div>
        <button type="button" class="s-read" :disabled="reading" @click="readBalance">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 5 6 9H2v6h4l5 4V5z" /><path d="M15.5 8.5a5 5 0 0 1 0 7" /></svg>
          {{ reading ? '읽어드리는 중' : '잔액 읽어주기' }}
        </button>
      </div>
    </section>

    <p v-if="notice" class="s-notice" role="status">{{ notice }}</p>

    <section class="s-section">
      <p class="s-label">무엇을 도와드릴까요</p>
      <div class="s-actions">
        <button type="button" class="s-act" @click="openBriefing">
          <span class="s-icon accent">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 5 6 9H2v6h4l5 4V5z" /><path d="M15.5 8.5a5 5 0 0 1 0 7" /><path d="M18.5 5.5a9 9 0 0 1 0 13" /></svg>
          </span>
          <span class="txt"><b>들어오고 나간 돈 듣기</b><small>{{ briefingBadge.subtitle }}</small></span>
          <span v-if="briefingBadge.showBadge" class="s-count num">{{ briefingBadge.count }}</span>
        </button>

        <button type="button" class="s-act" @click="openChat">
          <span class="s-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a3 3 0 0 1 3 3v5a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3z" /><path d="M19 11a7 7 0 0 1-14 0" /><path d="M12 18v3" /></svg>
          </span>
          <span class="txt"><b>말로 물어보기</b><small>궁금한 걸 그냥 말씀하세요</small></span>
          <svg class="s-chev" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7" /></svg>
        </button>

        <button type="button" class="s-act" @click="openSummary">
          <span class="s-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="3" width="16" height="18" rx="3" /><path d="M8 8h8" /><path d="M8 12h8" /><path d="M8 16h5" /></svg>
          </span>
          <span class="txt"><b>창구 요약서 보기</b><small>정리해 둔 창구 업무를 다시 확인해요</small></span>
          <svg class="s-chev" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7" /></svg>
        </button>

        <button type="button" class="s-act" @click="openCounter">
          <span class="s-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 21h18" /><path d="M5 21V10l7-5 7 5v11" /><path d="M10 21v-6h4v6" /></svg>
          </span>
          <span class="txt"><b>지점·대기표 선택</b><small>갈 은행을 고르고 번호표를 받아요</small></span>
          <svg class="s-chev" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7" /></svg>
        </button>
      </div>
    </section>

    <section class="s-section s-list">
      <div class="s-label-row">
        <p class="s-label">들어오고 나간 돈</p>
        <p class="s-help">누르면 읽어드려요</p>
      </div>

      <p v-if="loading" class="s-msg">불러오는 중이에요…</p>
      <p v-else-if="error" class="s-msg err">{{ error }}</p>

      <div v-else class="s-card">
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
            <b class="s-row-name">{{ it.transaction.counterparty_name }}</b>
            <span class="s-row-sub">
              <LevelBadge :level="it.classification.level" size="sm" />
              {{ when(it.transaction) }}
            </span>
          </span>
          <b class="s-amt num" :class="it.transaction.type">
            {{ it.transaction.type === 'IN' ? '+' : '−' }}{{ won(it.transaction.amount) }}
          </b>
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.senior-home {
  --ink: #17161a;
  --ink-2: #4a463f;
  --muted: #85817a;
  --label: #9a968c;
  --faint: #b3afa6;
  --paper: #f3f2ee;
  --line: #e9e6df;
  --hair: #f0eeea;
  --card-shadow: 0 1px 2px rgba(23, 22, 26, 0.04), 0 8px 24px rgba(23, 22, 26, 0.05);
  background: var(--paper);
  min-height: 100%;
  padding-bottom: 28px;
  display: flex;
  flex-direction: column;
  color: var(--ink);
}

.num { font-variant-numeric: tabular-nums; }
svg { display: block; }

/* ------------------------------------------------------------ 헤더 */
.s-top {
  display: flex; align-items: center; gap: 14px;
  padding: 16px 18px 12px;
  background: #fff;
}
.s-avatar {
  flex: none; width: 46px; height: 46px; border-radius: 50%;
  background: var(--kb-yellow); color: var(--ink);
  font-size: 20px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
}
.s-who { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.s-name { margin: 0; font-size: 23px; font-weight: 800; letter-spacing: -0.6px; line-height: 1.1; }
.s-mode { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; color: var(--muted); }
.s-mode .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--ok); }
.s-off {
  flex: none; min-height: 42px; padding: 0 14px;
  border: 1px solid #e6e3dc; border-radius: 12px; background: #fff;
  font-size: 14px; font-weight: 700; color: #6b675e;
}
.s-off:active { background: var(--paper); }

/* ------------------------------------------------------------ 잔액 */
.s-balance-wrap { background: #fff; padding: 2px 18px 20px; }
.s-balance {
  background: var(--kb-yellow);
  border-radius: 20px;
  padding: 18px 18px 16px;
  box-shadow: 0 1px 2px rgba(120, 85, 0, 0.1), 0 12px 30px rgba(255, 188, 0, 0.28);
}
.s-balance-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.s-account-name { margin: 0 0 2px; font-size: 14px; font-weight: 700; color: var(--ink); }
.s-account-number { margin: 0; font-size: 13px; font-weight: 600; color: #7a5c00; }
.s-fresh {
  flex: none; font-size: 12px; font-weight: 700; color: #7a5c00;
  background: rgba(255, 255, 255, 0.55); padding: 5px 10px; border-radius: 999px;
}
.s-balance-label { margin: 0 0 4px; font-size: 14px; font-weight: 600; color: #7a5c00; }
.s-amount { display: flex; align-items: baseline; gap: 5px; }
.s-amount .num { font-size: 38px; font-weight: 800; letter-spacing: -1.6px; line-height: 1; }
.s-amount .unit { font-size: 20px; font-weight: 700; }
.s-read {
  margin-top: 14px; min-height: 44px; padding: 0 16px 0 13px;
  display: inline-flex; align-items: center; gap: 8px;
  border: none; border-radius: 999px; background: var(--ink); color: #fff;
  font-size: 15px; font-weight: 700;
}
.s-read svg { width: 18px; height: 18px; fill: none; stroke: #fff; stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round; }
.s-read:disabled { opacity: 0.6; }
.s-read:focus-visible, .s-off:focus-visible, .s-act:focus-visible, .s-row:focus-visible {
  outline: 4px solid #1a56b0; outline-offset: 2px;
}

.s-notice {
  margin: 16px 18px 0;
  padding: 14px 16px;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: #fff;
  color: var(--ink-2);
  font-size: 18px;
  font-weight: 700;
  line-height: 1.45;
  word-break: keep-all;
  box-shadow: var(--card-shadow);
}

/* ------------------------------------------------------------ 구획 */
.s-section { padding: 22px 18px 0; }
.s-label { margin: 0 0 10px; font-size: 13px; font-weight: 700; color: var(--label); letter-spacing: 0.4px; }
.s-label-row { display: flex; align-items: baseline; justify-content: space-between; }
.s-help { margin: 0 0 12px; font-size: 13px; font-weight: 600; color: var(--faint); }

.s-actions { display: flex; flex-direction: column; gap: 8px; }
.s-act {
  display: flex; align-items: center; gap: 14px;
  width: 100%; min-height: 78px; padding: 13px 14px; text-align: left;
  border: 1px solid var(--line); border-radius: 20px; background: #fff;
  box-shadow: var(--card-shadow);
  color: var(--ink);
  transition: transform 0.08s ease;
}
.s-act:active { transform: scale(0.985); }
.s-icon {
  flex: none; width: 46px; height: 46px; border-radius: 14px; background: var(--paper);
  display: flex; align-items: center; justify-content: center;
}
.s-icon svg { width: 24px; height: 24px; fill: none; stroke: #3d3a34; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.s-icon.accent { background: var(--kb-yellow); }
.s-icon.accent svg { stroke: var(--ink); }
.s-act .txt { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.s-act b { font-size: 20px; font-weight: 800; letter-spacing: -0.6px; line-height: 1.25; word-break: keep-all; }
.s-act small { font-size: 14px; font-weight: 500; color: var(--muted); line-height: 1.35; word-break: keep-all; }
.s-count {
  flex: none; min-width: 26px; height: 26px; padding: 0 8px; border-radius: 999px;
  background: var(--ink); color: #fff; font-size: 14px; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
}
.s-chev { flex: none; width: 22px; height: 22px; fill: none; stroke: #c5c1b8; stroke-width: 2.4; stroke-linecap: round; stroke-linejoin: round; }

/* ------------------------------------------------------------ 내역: 카드 한 장에 여러 줄 */
.s-list { padding-bottom: 4px; }
.s-msg { font-size: 18px; color: var(--muted); padding: 8px 2px; }
.s-msg.err { color: var(--bad); }

.s-card {
  background: #fff; border: 1px solid var(--line); border-radius: 20px;
  padding: 0 18px; box-shadow: var(--card-shadow);
  display: flex; flex-direction: column;
}
.s-row {
  display: flex; align-items: center; gap: 14px;
  width: 100%; min-height: 76px; padding: 14px 0;
  border: none; border-bottom: 1px solid var(--hair); background: transparent;
  text-align: left; color: var(--ink);
  transition: background 0.12s ease;
}
.s-row:last-child { border-bottom: 0; }
.s-row:active { background: #faf9f6; }
.s-row-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 7px; }
.s-row-name {
  font-size: 20px; font-weight: 800; letter-spacing: -0.4px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.s-row-sub { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; color: var(--muted); }
.s-amt { flex: none; font-size: 19px; font-weight: 800; letter-spacing: -0.4px; }
.s-amt.IN { color: #1558d6; }
.s-amt.OUT { color: var(--ink); }
</style>
