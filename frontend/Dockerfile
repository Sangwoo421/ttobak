# 1) 빌드
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install
COPY . .
# 빌드 컨텍스트는 frontend/ 뿐이라 ../docs 가 없다 → 목 모드 JSON 은 빈 목록으로 빌드된다 (실서버 연동에는 영향 없음).
RUN npm run build

# 2) 서빙: nginx 가 정적 파일 + /api, /ai 프록시
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
