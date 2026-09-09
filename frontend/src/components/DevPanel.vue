<script setup>
import { ref } from 'vue'
import { useConversation } from '@/composables/useConversation'
import { USE_MOCK } from '@/api/http'

// 숨겨진 개발 패널. 시연 보험 + 측정용.
//  (a) 녹음 클립 입력 모드: 마이크 대신 로컬 오디오 파일을 /ai/stt 로 보낸다
//  (b) 텍스트 턴: 타이핑한 문장을 /ai/turn 으로 보낸다
//  (c) debug 보기: 마지막 턴의 debug (intent, matched, score, decision, path)
//  + 침묵 대기(2000 어르신 / 700 baseline), VAD 임계값, 자동 마이크
const conv = useConversation()
const { session } = conv

const typed = ref('')
const fileInput = ref(null)

async function onFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  await conv.sendAudioBlob(file)
  e.target.value = ''
}

async function onSend() {
  const t = typed.value
  typed.value = ''
  await conv.sendTypedText(t)
}

function setSilence(v) {
  session.silenceOverride = v
}
</script>

<template>
  <div class="dev-panel">
    <div class="row head">
      <b>개발 패널</b>
      <span class="tag" :class="{ mock: USE_MOCK }">{{ USE_MOCK ? 'MOCK' : 'LIVE' }}</span>
      <span class="mono">{{ session.session_id || '-' }} · {{ session.state }} · {{ session.tone }}</span>
      <button class="x" @click="conv.devOpen.value = false">닫기</button>
    </div>

    <div class="row">
      <label class="lbl">녹음 클립</label>
      <input ref="fileInput" type="file" accept="audio/*,.webm,.ogg,.wav,.mp3,.m4a" :disabled="!conv.canInteract.value" @change="onFile" />
    </div>

    <div class="row">
      <label class="lbl">텍스트 턴</label>
      <input v-model="typed" type="text" placeholder="예: 첫 번째 거 그게 뭐야" :disabled="!conv.canInteract.value" @keyup.enter="onSend" />
      <button :disabled="!conv.canInteract.value || !typed" @click="onSend">보내기</button>
    </div>

    <div class="row">
      <label class="lbl">침묵 대기</label>
      <button :class="{ on: session.silenceOverride == null }" @click="setSilence(null)">서버값 {{ session.silenceMs }}</button>
      <button :class="{ on: session.silenceOverride === 2000 }" @click="setSilence(2000)">2000 (어르신)</button>
      <button :class="{ on: session.silenceOverride === 700 }" @click="setSilence(700)">700 (baseline)</button>
      <span class="mono">= {{ session.effectiveSilenceMs }}ms</span>
    </div>

    <div class="row">
      <label class="lbl">VAD 임계</label>
      <input v-model.number="conv.vadThreshold.value" type="number" step="0.005" min="0.005" max="0.3" class="num" />
      <span class="mono">RMS {{ conv.recorder.level.value.toFixed(3) }}</span>
      <label class="chk"><input v-model="conv.autoListen.value" type="checkbox" /> 자동 마이크(listen)</label>
      <label class="chk"><input v-model="conv.showDebug.value" type="checkbox" /> debug 보기</label>
    </div>

    <pre v-if="conv.showDebug.value" class="debug">{{ session.lastDebug ? JSON.stringify(session.lastDebug, null, 2) : '(아직 턴 없음)' }}</pre>
  </div>
</template>

<style scoped>
.dev-panel {
  background: #fff;
  color: #2b2620;
  font-size: 13px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-bottom: 3px solid #d4a300;
}

.row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.row.head {
  justify-content: flex-start;
}

.lbl {
  width: 64px;
  color: #6b6458;
  flex: none;
}

.tag {
  padding: 2px 8px;
  border-radius: 999px;
  background: #2e7d32;
  font-weight: 700;
}

.tag.mock {
  background: #b26a00;
}

.mono {
  font-family: ui-monospace, Consolas, monospace;
  color: #6b6458;
  font-size: 12px;
}

.x {
  margin-left: auto;
}

input[type='text'] {
  flex: 1;
  min-width: 120px;
  font-size: 14px;
  padding: 6px 8px;
  border-radius: 6px;
  border: 1px solid #bcb5aa;
  background: #fff;
  color: #2b2620;
}

input[type='file'] {
  color: #4f493f;
  font-size: 12px;
  max-width: 100%;
}

.num {
  width: 80px;
  font-size: 14px;
  padding: 4px 6px;
  border-radius: 6px;
  border: 1px solid #bcb5aa;
  background: #fff;
  color: #2b2620;
}

button {
  font-size: 13px;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #8f887d;
  background: #fff;
  color: #2b2620;
}

button.on {
  background: #fff;
  color: #2b2620;
  border: 2px solid #d4a300;
}

button:disabled {
  opacity: 0.4;
}

.chk {
  display: flex;
  align-items: center;
  gap: 4px;
}

.debug {
  margin: 0;
  background: #f4f2ed;
  color: #315d38;
  border: 1px solid #d9d3c7;
  padding: 8px;
  border-radius: 6px;
  max-height: 260px;
  overflow: auto;
  font-size: 12px;
  line-height: 1.35;
}
</style>
