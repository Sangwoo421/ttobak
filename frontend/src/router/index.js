import { createRouter, createWebHistory } from 'vue-router'

// 시연 경로: /mock/home → /senior/briefing → /senior/chat → /senior/summary/:id
// 직원:      /staff → /staff/summaries/:id (또는 /staff/summaries 목록)
const routes = [
  { path: '/', redirect: '/mock/home' },

  { path: '/mock/home', component: () => import('@/views/mock/MockHome.vue'), meta: { frame: 'phone' } },
  { path: '/senior/home', component: () => import('@/views/mock/SeniorHome.vue'), meta: { frame: 'phone' } },

  { path: '/senior/briefing', component: () => import('@/views/senior/SeniorBriefing.vue'), meta: { frame: 'phone' } },
  { path: '/senior/chat', component: () => import('@/views/senior/SeniorChat.vue'), meta: { frame: 'phone' } },
  { path: '/senior/summary/:id', component: () => import('@/views/senior/SeniorSummary.vue'), meta: { frame: 'phone' } },

  { path: '/staff', component: () => import('@/views/staff/StaffHome.vue') },
  { path: '/staff/summaries', component: () => import('@/views/staff/StaffSummaryList.vue'), meta: { frame: 'phone' } },
  { path: '/staff/summaries/:id', component: () => import('@/views/staff/StaffSummaryDetail.vue'), meta: { frame: 'phone' } },

  { path: '/:pathMatch(.*)*', redirect: '/mock/home' },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
