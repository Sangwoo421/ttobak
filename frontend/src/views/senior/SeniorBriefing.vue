<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import SeniorShell from '@/components/SeniorShell.vue'
import ToneFrame from '@/components/ToneFrame.vue'
import BigButton from '@/components/BigButton.vue'
import MicButton from '@/components/MicButton.vue'
import MicStatus from '@/components/MicStatus.vue'
import LevelBadge from '@/components/LevelBadge.vue'
import { useConversation } from '@/composables/useConversation'
import { ordinalLabel } from '@/utils/format'
import { errorMessage } from '@/api/http'

// 시연 2단계: POST /ai/session/start → 브리핑 글 크게 + 음성 재생 → 끝나면 버튼 3개 + 마이크.
// 버튼/마이크를 누르면 대화 화면(/senior/chat)으로 넘어가고, 턴은 useConversation 싱글턴이 이어서 처리한다.
const router = useRouter()
const conv = useConversation()
const { session, player, recorder } = conv

const loading = ref(true)
const error = ref('')
const ready = computed(() => !loading.value && !error.value && !player.playing.value)

async function load() {
  loading.value = true
  error.value = ''
  try {
    await conv.begin({ user_id: 1, onStarted: () => (loading.value = false) })
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)

function onButton(id) {
  conv.pressButton(id)
  router.push('/senior/chat')
}

function onMic() {
  conv.startListening()
  router.push('/senior/chat')
}

function onStop() {
  if (!session.hasSession) return router.push('/mock/home')
  conv.pressButton('STOP')
  router.push('/senior/chat')
}
</script>

<template>
  <SeniorShell title="들어오고 나간 돈" @stop="onStop">
    <ToneFrame :tone="session.tone">
      <div class="page">
        <div v-if="error" class="error-box">
          <p>{{ error }}</p>
          <BigButton kind="secondary" @click="load">다시 해 볼게요</BigButton>
        </div>

        <p v-else-if="loading" class="loading">알림을 읽어올게요…</p>

        <template v-else>
          <p class="briefing-text">{{ session.briefing?.text }}</p>

          <div class="items">
            <div v-for="it in session.briefing?.items || []" :key="it.ordinal" class="item-card">
              <div class="ord">{{ ordinalLabel(it.ordinal) }}</div>
              <div class="label">{{ it.short_label }}</div>
              <LevelBadge :level="it.level" />
            </div>
          </div>

          <p v-if="session.briefing?.remaining_count > 0" class="muted small">읽지 않은 알림이 {{ session.briefing.remaining_count }}건 더 있어요</p>

          <button v-if="ready" type="button" class="replay" @click="conv.replayLast()">🔊 다시 듣기</button>
        </template>

        <div class="bottom">
          <MicStatus v-if="!error" :status="conv.micStatus.value" :level="recorder.level.value" />
          <template v-if="ready">
            <MicButton :status="conv.micStatus.value" @click="onMic" />
            <BigButton v-for="b in session.mainButtons" :key="b.id" :kind="b.kind || 'secondary'" @click="onButton(b.id)">{{ b.label }}</BigButton>
          </template>
        </div>
      </div>
    </ToneFrame>
  </SeniorShell>
</template>

<style scoped>
.page {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 12px;
}

.loading {
  text-align: center;
  padding: 40px 0;
  color: var(--muted);
}

.briefing-text {
  font-size: var(--senior-font-lg);
  font-weight: 700;
  line-height: 1.5;
  word-break: keep-all;
  background: var(--card);
  border-radius: var(--radius);
  padding: 16px 18px;
  box-shadow: var(--shadow);
}

.items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.item-card {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 12px;
  background: var(--card);
  border-radius: var(--radius);
  padding: 16px;
  box-shadow: var(--shadow);
  border-left: 8px solid var(--kb-yellow);
}

.ord {
  font-size: 20px;
  font-weight: 900;
  color: var(--kb-brown);
}

.label {
  font-size: var(--senior-font);
  font-weight: 800;
  word-break: keep-all;
}

.small {
  font-size: 18px;
}

.replay {
  align-self: flex-start;
  background: none;
  border: 0;
  color: var(--muted);
  font-size: 20px;
  font-weight: 700;
  padding: 4px 0;
}

.bottom {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 8px;
}
</style>
