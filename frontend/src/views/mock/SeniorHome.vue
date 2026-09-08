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
        <span class="s-row-main">
          <span class="s-row-top">
            <b>{{ it.classification.spoken_name || it.transaction.counterparty_name }}</b>
            <LevelBadge :level="it.classification.level" />
          </span>
          <span class="s-row-sub">{{ when(it.transaction) }}</span>
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
.senior-home { background: #fffdf5; min-height: 100%; padding-bottom: 24px; }

.s-top {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 18px 12px; background: #ffbc00;
}
.s-mode { font-size: 15px; font-weight: 800; color: #6b4e00; }
.s-name { font-size: 24px; font-weight: 800; color: #1b1b1b; margin-top: 2px; }
.s-off {
  min-height: 48px; padding: 0 16px; border: 2px solid #6b4e00; border-radius: 12px;
  background: #fff; font-size: 17px; font-weight: 700; color: #6b4e00; cursor: pointer;
}

.s-balance { padding: 20px 18px; background: #ffbc00; }
.s-label { font-size: 19px; font-weight: 700; color: #6b4e00; }
.s-amount { font-size: 40px; font-weight: 900; letter-spacing: -1px; margin-top: 4px; color: #1b1b1b; }

.s-actions { display: grid; gap: 12px; padding: 18px; }
.s-act {
  display: flex; align-items: center; gap: 14px; width: 100%;
  min-height: 84px; padding: 14px 16px; text-align: left;
  border: 3px solid #d8d2c0; border-radius: 16px; background: #fff; cursor: pointer;
}
.s-act.primary { border-color: #ffbc00; background: #fff8e1; }
.s-act .ico { font-size: 32px; flex: none; }
.s-act .txt { display: flex; flex-direction: column; gap: 3px; }
.s-act b { font-size: 23px; font-weight: 800; color: #1b1b1b; }
.s-act small { font-size: 16px; color: #5f5a4e; }

.s-list { padding: 6px 18px 0; }
.s-list h3 { font-size: 23px; font-weight: 800; margin: 10px 0 4px; }
.s-help { font-size: 16px; color: #5f5a4e; margin: 0 0 12px; }
.s-msg { font-size: 18px; color: #5f5a4e; }
.s-msg.err { color: #b3261e; }

.s-row {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  width: 100%; min-height: 80px; padding: 14px 16px; margin-bottom: 10px;
  border: 3px solid #e6e0cf; border-radius: 16px; background: #fff;
  text-align: left; cursor: pointer;
}
.s-row:active { background: #fff3cd; }
.s-row-main { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.s-row-top { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.s-row-top b { font-size: 21px; font-weight: 800; color: #1b1b1b; }
.s-row-sub { font-size: 16px; color: #5f5a4e; }
.s-row-right { display: flex; align-items: center; gap: 10px; flex: none; }
.s-amt { font-size: 20px; font-weight: 800; }
.s-amt.IN { color: #1558d6; }
.s-amt.OUT { color: #1b1b1b; }
.s-speaker { font-size: 26px; }
</style>
