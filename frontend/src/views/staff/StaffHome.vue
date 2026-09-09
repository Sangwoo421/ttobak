<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { getSummaryByCode } from '@/api/backend'
import { errorMessage } from '@/api/http'

// 시연 5단계: 직원이 6자리 코드를 입력 → GET /api/summaries/by-code/{code} → 상세로.
const router = useRouter()
const code = ref('')
const error = ref('')
const loading = ref(false)

async function lookup() {
  const c = code.value.trim()
  if (!/^[0-9]{6}$/.test(c)) {
    error.value = '숫자 6자리를 입력하세요'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const s = await getSummaryByCode(c)
    router.push(`/staff/summaries/${s.id}`)
  } catch (e) {
    error.value = e?.response?.status === 404 ? '해당 코드의 요약서가 없습니다' : errorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="staff home">
    <h1>또박또박 창구 화면</h1>
    <p class="muted">어르신 화면에 보이는 6자리 코드를 입력하세요.</p>

    <form class="code-form" @submit.prevent="lookup">
      <input v-model="code" type="text" inputmode="numeric" maxlength="6" placeholder="482913" autofocus class="code-input" />
      <button type="submit" class="btn primary" :disabled="loading">{{ loading ? '조회 중…' : '조회' }}</button>
    </form>
    <p v-if="error" class="error-box">{{ error }}</p>

    <p class="links">
      <router-link to="/staff/summaries">요약서 목록 보기 →</router-link>
      <router-link to="/mock/home" class="muted">어르신 화면(목업)</router-link>
    </p>
  </div>
</template>

<style scoped>
/* 창구 단말은 노트북이다. 폰 프레임을 뗀 뒤 요소가 화면 끝까지 늘어져 은행 업무 화면으로
   보이지 않아, 읽기 좋은 폭으로 잡고 가운데 둔다. 좁은 화면에서는 그대로 꽉 찬다. */
.home {
  width: 100%;
  max-width: 900px;
  margin: 0 auto;
  min-height: 100%;
  padding: 44px 20px 36px;
}

.code-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 20px 0 10px;
}

.code-input {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  font-size: 32px !important;
  letter-spacing: 0.22em;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.code-form .btn {
  width: 100%;
  min-height: 48px;
}

.links {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 30px;
}
</style>
