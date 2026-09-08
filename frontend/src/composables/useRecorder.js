// 마이크 녹음 + 간단한 VAD(RMS 기반).
//   record(opts) → Promise<{ blob, durationMs, speechDetected, mimeType } | null>
//   - 말소리(RMS > threshold)가 한 번이라도 감지된 뒤, silenceMs 동안 조용하면 자동 종료
//   - 최소 minMs(0.8s), 최대 maxMs(15s)
//   - stop() 으로 수동 종료, cancel() 은 결과 없이(null) 종료
// 모듈 싱글턴이라 화면을 옮겨도 녹음이 이어진다 (브리핑 → 대화 화면).
import { ref, readonly } from 'vue'

export const RECORDER_DEFAULTS = {
  silenceMs: 2000, // 어르신 모드 기본. 700 은 비교용 baseline
  maxMs: 15000,
  minMs: 800,
  threshold: 0.02, // RMS (0~1). 시끄러운 곳이면 0.04~0.06 으로 올린다 (개발 패널)
  tickMs: 50,
}

const status = ref('idle') // idle | listening | processing
const level = ref(0) // 현재 RMS (미터 표시용)
const elapsedMs = ref(0)
const error = ref(null)
const supported = typeof navigator !== 'undefined' && !!navigator.mediaDevices?.getUserMedia && typeof window !== 'undefined' && !!window.MediaRecorder

let stream = null
let ctx = null
let analyser = null
let recorder = null
let chunks = []
let timer = null
let finish = null // record() 의 resolve
let cancelled = false
let startedAt = 0
let lastSpeechAt = 0
let speechDetected = false

function pickMimeType() {
  const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
  return candidates.find((m) => window.MediaRecorder?.isTypeSupported?.(m)) || ''
}

function readRms(buf, byteBuf) {
  if (analyser.getFloatTimeDomainData) {
    analyser.getFloatTimeDomainData(buf)
  } else {
    // 구형 Safari: 바이트 → -1..1
    analyser.getByteTimeDomainData(byteBuf)
    for (let i = 0; i < byteBuf.length; i++) buf[i] = (byteBuf[i] - 128) / 128
  }
  let sum = 0
  for (let i = 0; i < buf.length; i++) sum += buf[i] * buf[i]
  return Math.sqrt(sum / buf.length)
}

function cleanup() {
  if (timer) clearInterval(timer)
  timer = null
  try {
    stream?.getTracks().forEach((t) => t.stop())
  } catch {
    /* ignore */
  }
  try {
    ctx?.close()
  } catch {
    /* ignore */
  }
  stream = null
  ctx = null
  analyser = null
  recorder = null
  level.value = 0
}

function stop() {
  if (status.value !== 'listening') return
  status.value = 'processing'
  if (timer) clearInterval(timer)
  timer = null
  try {
    if (recorder && recorder.state !== 'inactive') recorder.stop()
    else settle()
  } catch {
    settle()
  }
}

function cancel() {
  cancelled = true
  stop()
}

function settle() {
  const durationMs = Math.round(performance.now() - startedAt)
  const mimeType = recorder?.mimeType || 'audio/webm'
  const blob = chunks.length ? new Blob(chunks, { type: mimeType }) : null
  const result = cancelled || !blob ? null : { blob, durationMs, speechDetected, mimeType }
  cleanup()
  chunks = []
  status.value = 'idle'
  elapsedMs.value = 0
  const f = finish
  finish = null
  f?.(result)
}

async function record(opts = {}) {
  if (!supported) throw new Error('이 브라우저는 마이크 녹음을 지원하지 않아요 (HTTPS 또는 localhost 필요)')
  if (status.value !== 'idle') throw new Error('이미 녹음 중이에요')
  const o = { ...RECORDER_DEFAULTS, ...opts }
  error.value = null
  cancelled = false
  speechDetected = false
  chunks = []

  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } })
  } catch (e) {
    error.value = e
    throw new Error('마이크를 쓸 수 없어요. 브라우저 권한을 확인해 주세요.')
  }

  const AC = window.AudioContext || window.webkitAudioContext
  ctx = new AC()
  if (ctx.state === 'suspended') await ctx.resume().catch(() => {})
  analyser = ctx.createAnalyser()
  analyser.fftSize = 2048
  ctx.createMediaStreamSource(stream).connect(analyser)
  const buf = new Float32Array(analyser.fftSize)
  const byteBuf = new Uint8Array(analyser.fftSize)

  const mimeType = pickMimeType()
  recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
  recorder.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) chunks.push(e.data)
  }
  recorder.onstop = settle
  recorder.onerror = (e) => {
    error.value = e.error || e
    settle()
  }

  const done = new Promise((resolve) => {
    finish = resolve
  })

  startedAt = performance.now()
  lastSpeechAt = 0
  recorder.start(250)
  status.value = 'listening'

  timer = setInterval(() => {
    if (!analyser) return
    const rms = readRms(buf, byteBuf)
    level.value = rms
    const now = performance.now()
    const elapsed = now - startedAt
    elapsedMs.value = elapsed
    if (rms > o.threshold) {
      speechDetected = true
      lastSpeechAt = now
    }
    if (elapsed >= o.maxMs) return stop()
    if (speechDetected && elapsed >= o.minMs && now - lastSpeechAt >= o.silenceMs) return stop()
  }, o.tickMs)

  return done
}

export function useRecorder() {
  return {
    status: readonly(status),
    level: readonly(level),
    elapsedMs: readonly(elapsedMs),
    error: readonly(error),
    supported,
    record,
    stop,
    cancel,
  }
}
