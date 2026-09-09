"""시연 대본(docs/03) 1~11 단계를 서버(백엔드 8080 · AI 8000)에 대고 API 로 그대로 돌려 본다. 프론트 없이.

사용:  python tools/reset_demo.py && ai-server/.venv/Scripts/python tools/smoke_demo.py
       (알림 3건이 미청취 상태여야 브리핑이 세 건을 읽는다 → 먼저 reset_demo.py)
한 단계라도 FAIL 이면 거기서 멈춘다. 마지막 줄 "대본 1~11 API 완주 OK" 가 나와야 리허설을 시작한다.
2026-09-09 23:00 전 구간 통과. 8단계(웅얼거림)는 LLM 호출이라 1~5초 걸린다.
"""
import sys, time
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AI = "http://localhost:8000"
BE = "http://localhost:8080"
c = httpx.Client(timeout=90)
tok = None

def be(method, path, **kw):
    h = {"Authorization": f"Bearer {tok}"} if tok else {}
    r = c.request(method, BE + path, headers=h, **kw)
    return r

def step(no, label, ok, extra=""):
    print(f"[{'OK ' if ok else 'FAIL'}] {no:>2} {label} {extra}")
    if not ok:
        sys.exit(1)

# 로그인 (프론트가 쓰는 간편 로그인)
r = be("POST", "/api/auth/simple-login", json={"user_id": 1, "pin": "123456"})
if r.status_code == 200:
    tok = r.json().get("access_token")
step(0, "간편 로그인", r.status_code in (200, 404), f"status={r.status_code}")

# 1~2 브리핑
r = c.post(f"{AI}/ai/session/start", json={"user_id": 1, "mode": "layered"}).json()
sid = r["session_id"]
step(2, "session/start 브리핑", len(r["briefing"]["items"]) == 3 and bool(r["briefing"]["audio_url"]), r["briefing"]["text"][:40])

def turn(body, expect_state=None, label=""):
    t0 = time.time()
    resp = c.post(f"{AI}/ai/turn", json={"session_id": sid, **body}).json()
    dt = time.time() - t0
    d = resp.get("debug", {})
    ok = expect_state is None or resp.get("state") == expect_state
    print(f"      {label!r} -> state={resp.get('state')} tone={resp.get('tone')} intent={d.get('intent')} "
          f"matched={d.get('matched_candidate')} decision={d.get('decision')} llm={d.get('llm_used')} {dt:.1f}s")
    print(f"      🔊 {resp.get('assistant_text')}")
    return resp, ok

resp, ok = turn({"text": "첫 번째 거 그게 뭐야"}, label="3")
step(3, "첫 번째 거 설명", ok and "김철수" in resp["assistant_text"])

resp, ok = turn({"text": "세 번째 그 정보통신인가 그건 뭐야"}, "OFFER_ADD_QUESTION", "4")
step(4, "확인 불가 → 창구 목록 제안", ok and any(b["id"] == "YES" for b in resp["ui"]["buttons"]))

resp, ok = turn({"button_id": "YES"}, label="5")
step(5, "적어두기 (ADD_QUESTION)", any(a["type"] == "ADD_QUESTION" for a in resp.get("actions", [])))

resp, ok = turn({"text": "아들이 뭐 보내라는데 이십만 원인가"}, "CONFIRM", "6")
step(6, "이체 요청 → 확인 톤", ok and resp["tone"] == "confirm" and ("이십만" in resp["assistant_text"] or "200,000" in resp["assistant_text"]))

resp, ok = turn({"text": "맞아"}, label="7")
step(7, "맞아 → ADD_REQUEST", any(a["type"] == "ADD_REQUEST" for a in resp.get("actions", [])) or resp["state"] != "CONFIRM",
     f"actions={[a['type'] for a in resp.get('actions', [])]}")

resp, ok = turn({"text": "으음 그 저기"}, "CLARIFY", "8")
choices = resp["ui"].get("choices", [])
step(8, "웅얼 → CLARIFY 선택지", ok and len(choices) >= 2, f"choices={[x['id'] for x in choices]}")

go = next((x for x in choices if "GO_COUNTER" in x["id"]), None)
resp, ok = turn({"choice_id": go["id"]} if go else {"button_id": "GO_COUNTER"}, label="9")
open_sum = next((a for a in resp.get("actions", []) if a["type"] == "OPEN_SUMMARY"), None)
step(9, "창구 갈 일 정리 → OPEN_SUMMARY", open_sum is not None, f"payload={open_sum and open_sum.get('payload')}")
summary_id = open_sum["payload"]["summary_id"]
code = open_sum["payload"].get("code")

r = be("GET", f"/api/summaries/{summary_id}")
step(9, "GET /api/summaries/{id}", r.status_code == 200, f"status={r.status_code}")
s = r.json()
secs = {i["section"] for i in s["items"]}
print(f"      code={s['code']} ticket={s['ticket_no']} branch={s['branch_name']} sections={sorted(secs)}")
step(9, "요약서에 REQUEST+QUESTION+PREP", {"REQUEST", "QUESTION", "PREP"} <= secs)

r = be("GET", f"/api/summaries/by-code/{s['code']}")
step(10, "직원 코드 조회", r.status_code == 200 and r.json()["id"] == summary_id)

for it in [i for i in s["items"] if i["section"] != "PREP"]:
    r = be("PATCH", f"/api/staff/summaries/{summary_id}/items/{it['id']}", json={"handled": True})
    step(10, f"직원 체크 item {it['id']} ({it['section']})", r.status_code == 200, f"status={r.status_code}")

r = be("GET", f"/api/summaries/{summary_id}/status").json()
step(11, "status DONE → 폰에 완료 음성", r["status"] == "DONE", f"{r['handled_count']}/{r['total_count']}")
print("\n대본 1~11 API 완주 OK")
