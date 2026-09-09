"""레이어 적용 전/후 비교 측정.

사용: python run_measure.py --ai http://localhost:8000 --manifest testset/manifest.csv --out results/
의존: httpx (pip install httpx). wav 절단은 표준 라이브러리 wave 만 사용.
"""
from __future__ import annotations

import argparse
import csv
import io
import struct
import time
import wave
from pathlib import Path

import httpx

USER_ID = 1


# ---------------------------------------------------------------- baseline 모사: 첫 긴 침묵에서 절단

def truncate_at_silence(wav_bytes: bytes, silence_ms: int, threshold: float = 0.02) -> bytes:
    """말이 시작된 뒤 silence_ms 이상 조용해지는 첫 지점에서 오디오를 자른다(일반 STT 의 발화 종료 판정 모사)."""
    with wave.open(io.BytesIO(wav_bytes)) as w:
        n_ch, sampw, rate, n_frames = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n_frames)
    if sampw != 2:
        return wav_bytes  # 16-bit 만 지원, 그 외는 그대로
    frame_ms = 20
    hop = int(rate * frame_ms / 1000) * n_ch
    samples = struct.unpack("<%dh" % (len(raw) // 2), raw)
    peak = 32768.0
    speech_started, silent_run, cut_at = False, 0, None
    for i in range(0, len(samples), hop):
        chunk = samples[i:i + hop]
        if not chunk:
            break
        rms = (sum(s * s for s in chunk) / len(chunk)) ** 0.5 / peak
        if rms > threshold:
            speech_started, silent_run = True, 0
        elif speech_started:
            silent_run += frame_ms
            if silent_run >= silence_ms:
                cut_at = i
                break
    if cut_at is None:
        return wav_bytes
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(n_ch); w.setsampwidth(sampw); w.setframerate(rate)
        w.writeframes(struct.pack("<%dh" % cut_at, *samples[:cut_at]))
    return out.getvalue()


# ---------------------------------------------------------------- 한 건 실행

def run_one(client: httpx.Client, ai: str, mode: str, audio: bytes, filename: str, silence_ms: int,
            pause_s: float = 0.0, retries: int = 2) -> dict:
    start = client.post(f"{ai}/ai/session/start", json={"user_id": USER_ID, "mode": mode}).json()
    sid = start["session_id"]
    if mode == "baseline" and filename.lower().endswith(".wav"):
        audio = truncate_at_silence(audio, silence_ms)
    # STT 미리보기 모델은 분당 호출 제한(429)이 있고 서버는 그때 빈 문자열을 돌려준다.
    # 빈 문자열이면 잠시 쉬고 다시 시도한다 — 안 그러면 제한이 "인식 실패"로 집계된다.
    text = ""
    for attempt in range(retries + 1):
        stt = client.post(f"{ai}/ai/stt", data={"session_id": sid}, files={"audio": (filename, audio)}).json()
        text = stt.get("text", "")
        if text or attempt == retries:
            break
        time.sleep(max(pause_s, 15.0))
    if pause_s:
        time.sleep(pause_s)
    turn = client.post(f"{ai}/ai/turn", json={"session_id": sid, "text": text}).json()
    d = turn.get("debug", {})
    return {
        "text": text,
        "intent": d.get("intent"),
        "matched": d.get("matched_candidate"),
        "score": d.get("match_score"),
        "decision": d.get("decision"),
        "state": turn.get("state"),
    }


def judge(row: dict, r: dict) -> tuple[bool, int, bool]:
    """(도달 여부, 시도 횟수, 오실행 여부)"""
    exp_intent, exp_entity = row["expected_intent"], (row.get("expected_entity") or "").strip()
    decision = r.get("decision") or "NA"
    attempts = {"ACCEPT": 1, "LLM_TIEBREAK": 1, "ASK_AGAIN": 2, "BUTTON": 3}.get(decision, 3)
    if exp_intent == "UNKNOWN":
        reached = r.get("state") == "CLARIFY" or decision == "BUTTON"
        return reached, attempts, False
    intent_ok = r.get("intent") == exp_intent
    entity_ok = (not exp_entity) or (r.get("matched") == exp_entity)
    wrong_exec = bool(exp_entity) and decision in ("ACCEPT", "LLM_TIEBREAK") and r.get("matched") not in (None, exp_entity)
    reached = (intent_ok and entity_ok) or decision in ("ASK_AGAIN", "BUTTON")  # 되묻기·버튼으로 갔으면 도달 경로 확보
    if decision in ("ASK_AGAIN", "BUTTON") and not (intent_ok and entity_ok):
        attempts = 3 if decision == "BUTTON" else 2
    return reached, attempts, wrong_exec


# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ai", default="http://localhost:8000")
    ap.add_argument("--manifest", default="testset/manifest.csv")
    ap.add_argument("--out", default="results/")
    ap.add_argument("--baseline-silence-ms", type=int, default=700)
    ap.add_argument("--pause-s", type=float, default=6.0, help="호출 사이 대기(초). STT 분당 제한 회피")
    ap.add_argument("--label", default="팀원 녹음", help="결과표에 적을 테스트셋 출처 (예: Windows TTS 합성)")
    args = ap.parse_args()

    manifest = Path(args.manifest)
    testdir = manifest.parent
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rows = [r for r in csv.DictReader(manifest.open(encoding="utf-8")) if (testdir / r["file"]).exists()]
    if not rows:
        print("testset 에 오디오 파일이 없습니다. manifest 의 file 열과 같은 이름으로 녹음 파일을 넣으세요.")
        return

    stats = {m: {"reached": 0, "attempts": 0, "wrong": 0} for m in ("baseline", "layered")}
    details = []
    with httpx.Client(timeout=60) as client:
        for row in rows:
            audio = (testdir / row["file"]).read_bytes()
            for mode in ("baseline", "layered"):
                r = run_one(client, args.ai, mode, audio, row["file"], args.baseline_silence_ms, args.pause_s)
                reached, attempts, wrong = judge(row, r)
                s = stats[mode]
                s["reached"] += int(reached); s["attempts"] += attempts; s["wrong"] += int(wrong)
                details.append({"file": row["file"], "mode": mode, **r, "expected_intent": row["expected_intent"],
                                "expected_entity": row.get("expected_entity", ""), "reached": reached,
                                "attempts": attempts, "wrong_exec": wrong})
                print(f"[{mode:8}] {row['file']:28} intent={r['intent']!s:18} matched={r['matched']!s:8} "
                      f"decision={r['decision']!s:12} reached={reached} attempts={attempts}")

    n = len(rows)
    with (out / "details.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(details[0].keys())); w.writeheader(); w.writerows(details)
    md = ["# 레이어 적용 전/후 측정 결과", "", f"테스트셋: 자체 구성 {n}건 ({args.label}). 같은 STT 엔진, 같은 파일.", "",
          "| 경로 | 의도 도달률 | 평균 시도 횟수 | 오실행 건수 |", "|---|---|---|---|"]
    for mode, label in (("baseline", "레이어 미적용"), ("layered", "레이어 적용")):
        s = stats[mode]
        md.append(f"| {label} | {s['reached']}/{n} ({s['reached']/n*100:.0f}%) | {s['attempts']/n:.2f} | {s['wrong']} |")
    (out / "results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
