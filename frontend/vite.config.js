import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// 개발 서버: /api → 백엔드(8080), /ai → AI 서버(8000) 프록시.
// @contracts → docs/contracts/examples (목 모드가 예시 JSON 을 그대로 읽는다 = 단일 진실).
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@contracts': fileURLToPath(new URL('../docs/contracts/examples', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    host: true,
    fs: { allow: ['..'] },
    proxy: {
      '/api': { target: 'http://localhost:8080', changeOrigin: true },
      '/ai': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
