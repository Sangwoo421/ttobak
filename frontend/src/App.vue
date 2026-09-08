<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import PhoneFrame from '@/components/PhoneFrame.vue'

// /mock, /senior 는 폰 프레임(최대 430px) 안에, /staff 는 전체 폭.
const route = useRoute()
const isPhone = computed(() => route.meta.frame === 'phone')
</script>

<template>
  <PhoneFrame v-if="isPhone">
    <router-view />
  </PhoneFrame>
  <router-view v-else />
</template>
