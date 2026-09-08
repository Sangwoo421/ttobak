<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { won } from '@/utils/format'
import { getTransactions } from '@/api/backend'
import { errorMessage } from '@/api/http'
import { useAudioPlayer } from '@/composables/useAudioPlayer'
import LevelBadge from '@/components/LevelBadge.vue'

// 어르신 모드 홈. 일반 모드와 같은 데이터를 쓰지만 바뀌는 것은 글씨 크기만이 아니다.
//  - 거래 한 줄이 통째로 버튼이고, 누르면 그 건을 음성으로 읽고 바로 대화가 이어진다
//  - 무엇을 물어야 할지 몰라도 되도록, 할 수 있는 일을 큰 버튼 세 개로만 보여준다
//  - 확인 가능 / 일부 확인 / 확인 안 됨을 배지로 미리 알려, 앱이 뭘 모르는지 숨기지 않는다
// (담당 조태석·이성우 경계에 걸쳐 있음. docs/07-handoff.md 참고)
const props = defineProps({ account: { type: Object, required: true } })
const emit = defineEmits(['exit'])

const router = useRouter()
const player = useAudioPlayer()

const items = ref([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    items.value = await getTransactions(1, 6)
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
})

function go(path, query) {
  player.unlock() // 사용자 제스처 안에서 오디오를 깨워 둬야 이후 자동재생이 막히지 않는다
  router.push({ path, query })
}

const openBriefing = () => go('/senior/briefing')
const openChat = () => go('/senior/chat', { start: 'true' })
const openCounter = () => go('/senior/chat', { start: 'true', counter: 'true' })
const readOne = (it) => go('/senior/chat', { tx: String(it.transaction.id) })

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
        <div class="s-mode">어르신 모드</div>
        <div class="s-name">{{ account.name }}</div>
      </div>
      <button type="button" class="s-off" @click="emit('exit')">모드 끄기</button>
    </header>

    <section class="s-balance">
      <div class="s-label">지금 남은 돈</div>
      <div class="s-amount">{{ won(account.balance) }}</div>
    </section>

    <section class="s-actions">
      <button type="button" class="s-act primary" @click="openBriefing">
        <span class="ico">🔊</span>
        <span class="txt"><b>들어오고 나간 돈 듣기</b><small>최근 것부터 읽어드려요</small></span>
      </button>
      <button type="button" class="s-act" @click="openChat">
        <span class="ico">🎤</span>
        <span class="txt"><b>말로 물어보기</b><small>궁금한 걸 그냥 말씀하세요</small></span>
      </button>
      <button type="button" class="s-act" @click="openCounter">
        <span class="ico">🏦</span>
        <span class="txt"><b>창구 갈 일 정리</b><small>은행에서 할 일을 미리 적어드려요</small></span>
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
          <b class="s-row-name">{{ it.transaction.counterparty_name }}</b>
          <span class="s-row-sub">
            {{ when(it.transaction) }}
            <LevelBadge :level="it.classification.level" />
          </span>
        </span>
        <span class="s-row-right">
          <span class="s-amt" :class="it.transaction.type">
            {{ it.transaction.type === 'IN' ? '+' : '-' }}{{ won(it.transaction.amount) }}
          </span>
          <span class="s-speaker" aria-hidden="true">🔊</span>
        </span>
      </button>
    </section>
  </div>
</template>

<style scoped>
.senior-home {
  background: #fffdf5;
  min-height: 100%;
  padding-bottom: 28px;
  display: flex;
  flex-direction: column;
}

/* 헤더와 잔액은 한 덩어리로 보이게 해서 "모드가 바뀌었다"가 첫눈에 읽히게 한다 */
.s-top {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 12px;
  padding: 20px 18px 10px;
  background: linear-gradient(180deg, #ffc61a 0%, #ffbc00 100%);
}
.s-mode {
  display: inline-block; font-size: 14px; font-weight: 800; color: #6b4e00;
  background: rgba(255, 255, 255, 0.6); border-radius: 999px; padding: 3px 10px;
}
.s-name { font-size: 25px; font-weight: 900; color: #1b1b1b; margin-top: 6px; letter-spacing: -0.4px; }
.s-off {
  flex: none; min-height: 46px; padding: 0 15px;
  border: 2px solid rgba(107, 78, 0, 0.55); border-radius: 999px;
  background: rgba(255, 255, 255, 0.85);
  font-size: 16px; font-weight: 800; color: #6b4e00; cursor: pointer;
}
.s-off:active { background: #fff; }

.s-balance {
  padding: 4px 18px 24px;
  background: linear-gradient(180deg, #ffbc00 0%, #ffb800 100%);
}
.s-label { font-size: 18px; font-weight: 800; color: #6b4e00; }
.s-amount {
  font-size: 42px; font-weight: 900; letter-spacing: -1.5px; margin-top: 2px;
  color: #1b1b1b; line-height: 1.1;
}

/* 카드가 잔액 위로 살짝 올라타 보이게 해서 화면에 깊이를 준다 */
.s-actions {
  display: grid; gap: 12px; padding: 0 16px;
  margin-top: -14px; position: relative; z-index: 1;
}
.s-act {
  display: flex; align-items: center; gap: 14px; width: 100%;
  min-height: 84px; padding: 14px 16px; text-align: left;
  border: 2px solid #e6dfc9; border-radius: 18px; background: #fff; cursor: pointer;
  box-shadow: 0 4px 14px rgba(90, 70, 0, 0.1);
  transition: transform 0.08s ease;
}
.s-act:active { transform: scale(0.985); }
.s-act.primary { border-color: #ffbc00; background: linear-gradient(180deg, #fffaeb 0%, #fff4d1 100%); }
.s-act .ico {
  font-size: 26px; flex: none; width: 52px; height: 52px; border-radius: 16px;
  background: #fff3cd; display: flex; align-items: center; justify-content: center;
}
.s-act.primary .ico { background: #ffd766; }
.s-act .txt { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.s-act b { font-size: 22px; font-weight: 900; color: #1b1b1b; letter-spacing: -0.3px; }
.s-act small { font-size: 15px; color: #6b6455; }

.s-list { padding: 22px 16px 0; }
.s-list h3 { font-size: 23px; font-weight: 900; margin: 0 0 3px; letter-spacing: -0.4px; }
.s-help { font-size: 15px; color: #6b6455; margin: 0 0 14px; }
.s-msg { font-size: 18px; color: #6b6455; padding: 8px 2px; }
.s-msg.err { color: #b3261e; }

.s-row {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  width: 100%; min-height: 82px; padding: 14px 16px; margin-bottom: 10px;
  border: 2px solid #ece5d2; border-radius: 18px; background: #fff;
  text-align: left; cursor: pointer;
  box-shadow: 0 2px 8px rgba(90, 70, 0, 0.06);
  transition: transform 0.08s ease, background 0.12s ease;
}
.s-row:active { background: #fff8e1; transform: scale(0.99); }
.s-row-main { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.s-row-name {
  font-size: 20px; font-weight: 900; color: #1b1b1b; letter-spacing: -0.3px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.s-row-sub { display: flex; align-items: center; gap: 8px; font-size: 15px; color: #7a7466; }
.s-row-right { display: flex; align-items: center; gap: 12px; flex: none; }
.s-amt { font-size: 19px; font-weight: 900; letter-spacing: -0.3px; }
.s-amt.IN { color: #1558d6; }
.s-amt.OUT { color: #1b1b1b; }
.s-speaker {
  font-size: 20px; width: 42px; height: 42px; border-radius: 50%;
  background: #fff3cd; display: flex; align-items: center; justify-content: center;
}
</style>
