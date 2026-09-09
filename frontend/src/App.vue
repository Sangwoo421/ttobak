<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import PhoneFrame from '@/components/PhoneFrame.vue'

// 시연 화면은 모두 폰 프레임(최대 430px) 안에 표시한다.
const route = useRoute()
const isPhone = computed(() => route.meta.frame === 'phone')
</script>

<template>
  <PhoneFrame v-if="isPhone">
    <router-view />
  </PhoneFrame>
  <router-view v-else />
</template>
