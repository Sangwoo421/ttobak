<script setup>
// /mock, /senior 용 폰 프레임: 최대 430px 중앙 정렬, 데스크톱에서는 은은한 폰 테두리.
</script>

<template>
  <div class="phone-wrap">
    <div class="phone">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.phone-wrap {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: stretch;
  background: #e9e9e4;
}

.phone {
  width: 100%;
  max-width: 430px;
  min-height: 100vh;
  background: var(--bg);
  position: relative;
  display: flex;
  flex-direction: column;
}

@media (min-width: 480px) {
  .phone-wrap {
    padding: 20px 0;
    align-items: flex-start;
  }

  .phone {
    min-height: calc(100vh - 40px);
    border: 10px solid #222;
    border-radius: 36px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
    overflow: hidden;
  }
}
</style>
