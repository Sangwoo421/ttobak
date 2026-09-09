import { createRouter, createWebHistory } from 'vue-router'

// 시연 경로: /mock/home → /senior/briefing → /senior/chat → /senior/summary/:id
// 직원:      /staff → /staff/summaries/:id (또는 /staff/summaries 목록)
const routes = [
  { path: '/', redirect: '/mock/home' },

  { path: '/mock/home', component: () => import('@/views/mock/MockHome.vue'), meta: { frame: 'phone' } },

  { path: '/senior/briefing', component: () => import('@/views/senior/SeniorBriefing.vue'), meta: { frame: 'phone' } },
  { path: '/senior/chat', component: () => import('@/views/senior/SeniorChat.vue'), meta: { frame: 'phone' } },
  { path: '/senior/summary/:id', component: () => import('@/views/senior/SeniorSummary.vue'), meta: { frame: 'phone' } },

  // 직원 화면은 폰 프레임을 씌우지 않는다. 창구 단말은 노트북이고, 시연에서 노치 달린
  // 430px 아이폰으로 보이면 "직원은 확인부터 시작합니다"라는 설명과 어긋난다.
  { path: '/staff', component: () => import('@/views/staff/StaffHome.vue') },
  { path: '/staff/summaries', component: () => import('@/views/staff/StaffSummaryList.vue') },
  { path: '/staff/summaries/:id', component: () => import('@/views/staff/StaffSummaryDetail.vue') },

  { path: '/:pathMatch(.*)*', redirect: '/mock/home' },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
