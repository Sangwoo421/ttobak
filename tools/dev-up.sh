#!/bin/bash
# 서버 3개를 한 번에 띄운다.   사용: ./tools/dev-up.sh
# 로그: tools/.logs/*.log      끄기: ./tools/dev-down.sh
set -u
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
LOGS="$ROOT/tools/.logs"
mkdir -p "$LOGS"

kill_port() {
  local pids
  pids=$(lsof -ti:"$1" 2>/dev/null) || true
  if [ -n "$pids" ]; then
    echo "   :$1 쓰던 프로세스 정리"
    echo "$pids" | xargs kill -9 2>/dev/null
    sleep 1
  fi
}

echo "── 기존 프로세스 정리"
kill_port 8080; kill_port 8000; kill_port 5173

echo "── 백엔드 (8080)"
( cd "$ROOT/backend" && ./gradlew bootRun ) > "$LOGS/backend.log" 2>&1 &

echo "── AI 서버 (8000)"
( cd "$ROOT/ai-server" && source .venv/bin/activate && BACKEND_MODE=http python -m uvicorn app.main:app --port 8000 ) > "$LOGS/ai.log" 2>&1 &

echo "── 프론트 (5173)"
( cd "$ROOT/frontend" && npm run dev ) > "$LOGS/front.log" 2>&1 &

echo ""
echo "── 뜰 때까지 대기 (최대 90초)"
for i in $(seq 1 90); do
  b=$(curl -s -o /dev/null -w "%{http_code}" localhost:8080/api/health 2>/dev/null)
  a=$(curl -s -o /dev/null -w "%{http_code}" localhost:8000/ai/health 2>/dev/null)
  f=$(curl -s -o /dev/null -w "%{http_code}" localhost:5173 2>/dev/null)
  if [ "$b" = "200" ] && [ "$a" = "200" ] && [ "$f" = "200" ]; then
    echo ""; echo "✅ 셋 다 떴다"; echo ""
    curl -s localhost:8000/ai/health; echo; echo
    echo "   http://localhost:5173/mock/home"
    echo "   로그 보기: tail -f tools/.logs/ai.log"
    echo "   끄기:     ./tools/dev-down.sh"
    exit 0
  fi
  printf "\r   backend %s / ai %s / front %s   (%s초)" "$b" "$a" "$f" "$i"
  sleep 1
done
echo ""; echo "❌ 90초 안에 다 못 떴다. 로그 봐라:"
echo "   tail -30 tools/.logs/backend.log"
echo "   tail -30 tools/.logs/ai.log"
echo "   tail -30 tools/.logs/front.log"
exit 1
