#!/bin/bash
# 시연 데이터 원상복구. 리허설 돌릴 때마다 실행.
# 사용: ./tools/reset-demo.sh          (root 비번 물어봄)

# TTS 캐시도 함께 비운다 — 리허설마다 모든 문장을 새 합성으로 다시 굽는다.
"$(dirname "$0")/clear-audio-cache.sh"

mysql -u root -p ttobak <<'SQL'
DELETE FROM summary_items   WHERE summary_id >= 2;
DELETE FROM counter_summaries WHERE id >= 2;
UPDATE notifications SET heard_at = NULL, read_at = NULL WHERE id IN (1001, 1002, 1003);
DELETE FROM mute_rules;
DELETE FROM dialog_logs;
SELECT '── 복구 완료 ──' AS '';
SELECT id, counterparty_name, heard_at FROM notifications n JOIN transactions t ON t.id = n.transaction_id WHERE n.id IN (1001,1002,1003);
SQL
