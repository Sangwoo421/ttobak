"""시연 직전 데이터 초기화 — docker compose down/up 없이 3초.

무엇을 되돌리나 (docs/contracts/seed-data.sql 기준):
  · 알림 101·102·103 을 다시 '미청취'로 (heard_at = NULL)  → 브리핑이 세 건을 읽는다
  · 시연 중 만들어진 창구 요약서·항목·대기표·대화 로그 삭제 (시드 id 는 남긴다)
시드 자체는 건드리지 않는다. 필요하면 --dry-run 으로 실행할 SQL 만 본다.

사용:  python tools/reset_demo.py            (컨테이너 이름 기본 ttobak-mysql)
       python tools/reset_demo.py --container ttobak-mysql --dry-run
"""
from __future__ import annotations

import argparse
import subprocess
import sys

SEED_MAX_SUMMARY_ID = 1     # counter_summaries 시드 마지막 id
DEMO_USER_ID = 1            # 시연 사용자(김영자). 시드 대기표(9001~)는 user 2 소유라 남는다

SQL = f"""
UPDATE notifications SET heard_at = NULL WHERE transaction_id IN (101, 102, 103);
DELETE FROM summary_items   WHERE summary_id > {SEED_MAX_SUMMARY_ID};
DELETE FROM branch_tickets  WHERE user_id = {DEMO_USER_ID};
DELETE FROM counter_summaries WHERE id > {SEED_MAX_SUMMARY_ID};
DELETE FROM dialog_logs;
SELECT id, transaction_id, heard_at FROM notifications WHERE transaction_id IN (101, 102, 103);
SELECT COUNT(*) AS summaries_left FROM counter_summaries;
""".strip()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows 콘솔(cp949)에서 한글 깨짐 방지
    ap = argparse.ArgumentParser()
    ap.add_argument("--container", default="ttobak-mysql")
    ap.add_argument("--user", default="ttobak")
    ap.add_argument("--password", default="ttobak")
    ap.add_argument("--database", default="ttobak")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.dry_run:
        print(SQL)
        return 0
    cmd = ["docker", "exec", "-i", a.container, "mysql", f"-u{a.user}", f"-p{a.password}", a.database]
    r = subprocess.run(cmd, input=SQL, text=True, capture_output=True)
    out = "\n".join(l for l in (r.stdout + r.stderr).splitlines() if "Warning" not in l)
    print(out)
    if r.returncode != 0:
        print("초기화 실패. mysql 컨테이너가 떠 있는지 확인: docker ps", file=sys.stderr)
        return r.returncode
    print("시연 데이터 초기화 완료. 알림 3건 미청취, 시연 중 만든 요약서·대기표 삭제.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
