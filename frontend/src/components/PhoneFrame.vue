<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

// /mock, /senior 용 폰 프레임.
//
// 핵심은 "프레임이 늘어나지 않는다"는 것이다. 예전에는 .phone 에 min-height 만 있고 상한이 없어서
// 내용이 길어지면 폰 테두리가 같이 길어졌다. 실제 폰은 화면 크기가 고정이고 안에서 스크롤된다.
// 그래서 프레임 높이를 뷰포트에 고정하고, 스크롤은 .phone-screen 안에서만 일어나게 한다.
//
// 시연에서 이 프레임은 그냥 장식이 아니다. 심사위원이 보는 것은 "폰에서 도는 앱"이어야 한다.
// 상태바와 홈 인디케이터가 있으면 스크린샷 한 장으로도 앱처럼 읽힌다.

const now = ref(new Date())
let timer = null

onMounted(() => {
  timer = setInterval(() => { now.value = new Date() }, 30000)
})
onBeforeUnmount(() => clearInterval(timer))

const clock = computed(() => {
  const h = now.value.getHours()
  const m = String(now.value.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
})
</script>

<template>
  <div class="phone-wrap">
    <div class="phone">
      <!-- 상태바: 실제 폰처럼 보이게 하는 최소 장치 -->
      <div class="status-bar" aria-hidden="true">
        <span class="clock">{{ clock }}</span>
        <span class="notch" />
        <span class="icons">
          <span class="signal"><i /><i /><i /><i /></span>
          <span class="wifi">◗</span>
          <span class="battery"><b /></span>
        </span>
      </div>

      <!-- 스크롤은 여기서만 일어난다. 프레임은 절대 늘어나지 않는다. -->
      <div class="phone-screen">
        <slot />
      </div>

      <div class="home-indicator" aria-hidden="true" />
    </div>
  </div>
</template>

<style scoped>
.phone-wrap {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  justify-content: center;
  align-items: stretch;
  background: #edece7;
}

.phone {
  width: 100%;
  max-width: 430px;
  height: 100vh;
  height: 100dvh;
  background: var(--bg);
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 프레임 밖으로 새지 않는다 */
}

/* 내용이 아무리 길어도 프레임은 그대로, 안쪽만 스크롤된다 */
.phone-screen {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  display: flex;
  flex-direction: column;
}

.phone-screen > :deep(*) {
  flex: 1 0 auto;
}

/* ---------------------------------------------------------------- 상태바 */
.status-bar {
  flex: none;
  height: 44px;
  padding: 0 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg);
  color: #1b1b1b;
  font-size: 14px;
  font-weight: 700;
  position: relative;
  z-index: 2;
}

.clock { letter-spacing: 0.2px; }

.notch {
  position: absolute;
  left: 50%;
  top: 6px;
  transform: translateX(-50%);
  width: 96px;
  height: 26px;
  border-radius: 999px;
  background: #1b1b1b;
}

.icons { display: flex; align-items: center; gap: 6px; }

.signal { display: inline-flex; align-items: flex-end; gap: 2px; height: 11px; }
.signal i { width: 3px; background: #1b1b1b; border-radius: 1px; }
.signal i:nth-child(1) { height: 4px; }
.signal i:nth-child(2) { height: 6px; }
.signal i:nth-child(3) { height: 8px; }
.signal i:nth-child(4) { height: 11px; }

.wifi { font-size: 13px; transform: rotate(-45deg); }

.battery {
  width: 24px;
  height: 12px;
  border: 1.5px solid #1b1b1b;
  border-radius: 3px;
  padding: 1.5px;
  display: inline-flex;
}
.battery b { flex: 1; background: #1b1b1b; border-radius: 1px; }

.home-indicator {
  flex: none;
  height: 18px;
  background: var(--bg);
  position: relative;
  z-index: 2;
}
.home-indicator::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 6px;
  transform: translateX(-50%);
  width: 132px;
  height: 5px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.28);
}

/* ---------------------------------------------------------------- 데스크톱: 기기처럼 */
@media (min-width: 480px) {
  .phone-wrap {
    padding: 24px 0;
    align-items: center;
    background:
      radial-gradient(1200px 600px at 50% -10%, #ffffff 0%, #edece7 60%),
      #edece7;
  }

  .phone {
    height: min(880px, calc(100dvh - 48px));
    border: 12px solid #17171a;
    border-radius: 44px;
    box-shadow:
      0 0 0 2px #3a3a3f,
      0 30px 70px rgba(0, 0, 0, 0.32),
      0 8px 20px rgba(0, 0, 0, 0.18);
  }
}
</style>
