<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listStaffSummaries } from '@/api/backend'
import { errorMessage } from '@/api/http'
import { dateTime, statusLabel } from '@/utils/format'

// 직원용 요약서 목록: GET /api/staff/summaries[?status=]
const router = useRouter()
const rows = ref([])
const filter = ref('')
const error = ref('')
const loading = ref(false)

async function load() {
  loading.value = true
  error.value = ''
  try {
    rows.value = await listStaffSummaries(filter.value || undefined)
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(filter, load)
</script>

<template>
  <div class="staff">
    <div class="bar">
      <h1>요약서 목록</h1>
      <select v-model="filter">
        <option value="">전체</option>
        <option value="OPEN">접수됨</option>
        <option value="IN_PROGRESS">처리 중</option>
        <option value="DONE">처리 완료</option>
      </select>
      <button class="btn" @click="load">새로고침</button>
      <router-link to="/staff" class="back">← 코드 입력</router-link>
    </div>

    <p v-if="error" class="error-box">{{ error }}</p>

    <table>
      <thead>
        <tr>
          <th>번호표</th>
          <th>고객</th>
          <th>코드</th>
          <th>상태</th>
          <th>접수 시각</th>
          <th>항목</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!loading && !rows.length">
          <td colspan="6" class="muted">요약서가 없습니다</td>
        </tr>
        <tr v-for="r in rows" :key="r.id" class="row" @click="router.push(`/staff/summaries/${r.id}`)">
          <td><b>{{ r.ticket_no }}</b></td>
          <td>{{ r.user_name }}</td>
          <td class="mono">{{ r.code }}</td>
          <td><span class="status-badge" :class="r.status">{{ statusLabel(r.status) }}</span></td>
          <td>{{ dateTime(r.created_at) }}</td>
          <td>{{ r.item_count }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.bar h1 {
  margin: 0;
  flex: 1;
}

select {
  font-size: 15px;
  padding: 8px;
  border-radius: 8px;
}

.back {
  color: var(--muted);
  text-decoration: none;
}

.row {
  cursor: pointer;
}

.row:hover {
  background: #fffbe8;
}

.mono {
  font-family: ui-monospace, Consolas, monospace;
  letter-spacing: 0.1em;
}
</style>
