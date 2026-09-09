<template>
  <div class="staff home">
    <h1>또박또박 창구 화면</h1>
    <p class="muted">접수된 창구 요약서를 목록에서 선택하세요.</p>
    <router-link class="list-link" to="/staff/summaries">요약서 목록 보기</router-link>
    <router-link class="senior-link" to="/mock/home">어르신 화면</router-link>
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

.list-link {
  min-height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 24px;
  border: 3px solid #d4a300;
  border-radius: 12px;
  background: #fff;
  color: #2b2620;
  font-size: 18px;
  font-weight: 800;
  text-decoration: none;
}

.senior-link {
  display: block;
  margin-top: 20px;
  color: var(--muted);
  text-align: center;
}
</style>
