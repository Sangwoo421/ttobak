<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { errorMessage } from '@/api/http'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const pin = ref('')
const error = ref('')
const submitting = ref(false)
const dots = computed(() => Array.from({ length: 6 }, (_, index) => index < pin.value.length))
let submitTimer = null

function destination() {
  const redirect = String(route.query.redirect || '')
  return redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : '/mock/home'
}

function press(value) {
  if (submitting.value || pin.value.length >= 6) return
  error.value = ''
  pin.value += value
  if (pin.value.length === 6) {
    clearTimeout(submitTimer)
    submitTimer = setTimeout(submit, 140)
  }
}

function erase() {
  if (submitting.value) return
  error.value = ''
  pin.value = pin.value.slice(0, -1)
}

async function submit() {
  if (pin.value.length !== 6 || submitting.value) return
  submitting.value = true
  try {
    await auth.login(pin.value)
    await router.replace(destination())
  } catch (e) {
    error.value = errorMessage(e).replace(/^서버 오류 401:\s*/, '')
    pin.value = ''
  } finally {
    submitting.value = false
  }
}

function onKeydown(event) {
  if (/^[0-9]$/.test(event.key)) press(event.key)
  else if (event.key === 'Backspace') erase()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  clearTimeout(submitTimer)
})
</script>

<template>
  <main class="login-page">
    <header class="brand">
      <span>KB스타뱅킹</span>
    </header>

    <section class="login-card" aria-labelledby="login-title">
      <h1 id="login-title">간편비밀번호를<br />입력해 주세요</h1>

      <div class="pin-dots" :aria-label="`비밀번호 ${pin.length}자리 입력됨`" aria-live="polite">
        <span v-for="(filled, index) in dots" :key="index" :class="{ filled }" />
      </div>

      <p v-if="error" class="login-error" role="alert">{{ error }}</p>
      <p v-else-if="submitting" class="login-status" role="status">확인하고 있어요…</p>
      <p v-else class="login-status" aria-hidden="true">&nbsp;</p>
    </section>

    <div class="keypad" aria-label="숫자 키패드">
      <button v-for="n in [1, 2, 3, 4, 5, 6, 7, 8, 9]" :key="n" type="button" class="key" :disabled="submitting" @click="press(String(n))">{{ n }}</button>
      <span class="key-spacer" aria-hidden="true" />
      <button type="button" class="key" :disabled="submitting" @click="press('0')">0</button>
      <button type="button" class="key erase" aria-label="한 자리 지우기" :disabled="submitting || !pin.length" @click="erase">지우기</button>
    </div>

    <p class="security-note">비밀번호는 화면이나 기기에 저장하지 않아요</p>
  </main>
</template>

<style scoped>
.login-page {
  min-height: 100%;
  display: flex;
  flex: 1;
  flex-direction: column;
  padding: 24px 24px 18px;
  background:
    radial-gradient(circle at 50% -10%, #fff7cf 0, transparent 38%),
    #fffdf7;
  color: #242018;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 19px;
  font-weight: 900;
}

.login-card {
  margin-top: 72px;
  text-align: center;
}

h1 {
  margin: 0;
  font-size: 30px;
  line-height: 1.3;
  letter-spacing: -0.6px;
}

.pin-dots {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin: 24px 0 14px;
}

.pin-dots span {
  width: 16px;
  height: 16px;
  border: 2px solid #b9b19d;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.12s ease, background 0.12s ease;
}

.pin-dots span.filled {
  border-color: #5e4900;
  background: #5e4900;
  transform: scale(1.08);
}

.login-error,
.login-status {
  min-height: 24px;
  margin: 0;
  font-size: 15px;
  font-weight: 700;
}

.login-error { color: #b3261e; }
.login-status { color: #6a5200; }

.keypad {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px 18px;
  margin-top: auto;
}

.key {
  min-height: 66px;
  border: 0;
  border-radius: 20px;
  background: transparent;
  color: #252117;
  font-size: 28px;
  font-weight: 800;
  transition: background 0.08s ease, transform 0.08s ease;
}

.key:active {
  background: #fff0af;
  transform: scale(0.95);
}

.key:focus-visible {
  outline: 4px solid #1a56b0;
  outline-offset: 1px;
}

.key:disabled { opacity: 0.35; }
.key.erase { font-size: 18px; }

.security-note {
  margin: 10px 0 0;
  color: #8a8374;
  font-size: 13px;
  text-align: center;
}

@media (max-height: 780px) {
  .login-page { padding-top: 16px; }
  .login-card { margin-top: 46px; }
  h1 { font-size: 26px; }
  .pin-dots { margin: 14px 0 8px; }
  .key { min-height: 54px; }
}
</style>
