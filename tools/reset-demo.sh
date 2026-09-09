#!/bin/bash
# 시연 데이터 원상복구. 리허설 돌릴 때마다 실행.
#
# 사용:
#   ./tools/reset-demo.sh                DB 만 리셋 (기본)
#   ./tools/reset-demo.sh --with-audio   DB 리셋 + TTS 캐시까지 삭제
#
# ⚠️ 발표 직전에는 --with-audio 를 쓰지 마라.
#    캐시가 비면 첫 재생부터 실시간 합성이 걸리고, 무료 티어 429 로 문장이 무음이 될 수 있다.
#    모델·목소리를 바꾼 직후 한 번만 --with-audio 로 다시 굽고,
#    리허설은 캐시를 남긴 채(옵션 없이) 돌려라.

set -euo pipefail

with_audio=0
for arg in "$@"; do
  case "$arg" in
    --with-audio) with_audio=1 ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "알 수 없는 옵션: $arg (사용법은 --help)" >&2; exit 2 ;;
  esac
done

if [ "$with_audio" -eq 1 ]; then
  "$(dirname "$0")/clear-audio-cache.sh"
else
  echo "── TTS 캐시는 그대로 둔다 (지우려면 --with-audio) ──"
fi

# 호스트에 mysql 클라이언트가 없는 PC 가 있어서 컨테이너 안에서 돌린다.
# (-p 대화형 프롬프트는 비TTY 에서 죽는다. 시연용 로컬 계정이라 비밀번호를 인라인으로 둔다.)
MYSQL_CONTAINER="${MYSQL_CONTAINER:-ttobak-mysql}"

if docker exec "$MYSQL_CONTAINER" true 2>/dev/null; then
  RUN_SQL() { docker exec -i "$MYSQL_CONTAINER" mysql -uttobak -pttobak --default-character-set=utf8mb4 ttobak 2>/dev/null; }
elif command -v mysql >/dev/null 2>&1; then
  RUN_SQL() { mysql -uttobak -pttobak --default-character-set=utf8mb4 ttobak; }
else
  echo "!! MySQL 에 닿을 수 없다. 컨테이너가 떠 있는지 확인:  docker start $MYSQL_CONTAINER"
  exit 1
fi

RUN_SQL <<'SQL'
DELETE FROM summary_items   WHERE summary_id >= 2;
DELETE FROM counter_summaries WHERE id >= 2;
-- 리허설에서 뽑은 대기표. 남아 있으면 다음 발급이 409(이미 활성 대기표 있음)로 막힌다.
DELETE FROM branch_tickets WHERE id >= 9000;
UPDATE notifications SET heard_at = NULL, read_at = NULL WHERE id IN (1001, 1002, 1003);
DELETE FROM mute_rules;
DELETE FROM dialog_logs;
SELECT '── 복구 완료 ──' AS '';
SELECT n.id, t.counterparty_name, n.heard_at FROM notifications n JOIN transactions t ON t.id = n.transaction_id WHERE n.id IN (1001,1002,1003);
SELECT COUNT(*) AS '남은 대기표' FROM branch_tickets WHERE id >= 9000;
SQL
