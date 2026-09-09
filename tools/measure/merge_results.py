"""여러 번 나눠 돌린 details.csv 를 합쳐 results.md 표를 다시 만든다.

무료 등급 STT 하루 한도(키당 25회) 때문에 한 번에 다 못 돌릴 때 쓴다.
같은 (file, mode) 가 여러 파일에 있으면 **뒤에 준 파일이 이긴다** — 빈 STT 로 깨진 건을 보충 실행으로 덮어쓴다.

사용: python merge_results.py results/details.csv results_fix/details.csv --out results_final/ --label "..."
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def recount(r: dict) -> int:
    """run_measure.judge 와 같은 규칙. NA(대조 불필요 의도)는 의도가 맞으면 1회."""
    d = r.get("decision") or ""
    intent_ok = r.get("intent") == r.get("expected_intent")
    if r.get("expected_intent") == "UNKNOWN":
        return 3
    if d in ("ACCEPT", "LLM_TIEBREAK"):
        return 1
    if d == "NA":
        return 1 if intent_ok else 3
    if d == "ASK_AGAIN":
        return 2
    return 3


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("details", nargs="+")
    ap.add_argument("--out", default="results_final/")
    ap.add_argument("--label", default="팀원 녹음")
    args = ap.parse_args()

    rows: dict[tuple[str, str], dict] = {}
    for path in args.details:
        for r in csv.DictReader(open(path, encoding="utf-8")):
            rows[(r["file"], r["mode"])] = r
    files = sorted({f for f, _ in rows})
    # 두 경로 모두 STT 결과가 있는 건만 센다 (한쪽만 빈 문자열이면 레이어 비교가 아니라 API 실패다)
    valid = [f for f in files if all(rows.get((f, m), {}).get("text") for m in ("baseline", "layered"))]
    dropped = [f for f in files if f not in valid]

    stats = {m: {"reached": 0, "attempts": 0, "wrong": 0} for m in ("baseline", "layered")}
    for f in valid:
        for m in ("baseline", "layered"):
            r = rows[(f, m)]
            stats[m]["reached"] += r["reached"] == "True"
            r["attempts"] = str(recount(r))
            stats[m]["attempts"] += int(r["attempts"])
            stats[m]["wrong"] += r["wrong_exec"] == "True"
    n = len(valid)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    with (out / "details.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(next(iter(rows.values())).keys()))
        w.writeheader()
        for f in files:
            for m in ("baseline", "layered"):
                if (f, m) in rows:
                    w.writerow(rows[(f, m)])
    md = ["# 레이어 적용 전/후 측정 결과", "",
          f"테스트셋: 자체 구성 {n}건 ({args.label}). 같은 STT 엔진, 같은 파일.",
          (f"제외 {len(dropped)}건 (STT 호출 실패로 한쪽 텍스트가 비어 비교 불가): {', '.join(dropped)}" if dropped else ""), "",
          "| 경로 | 의도 도달률 | 평균 시도 횟수 | 오실행 건수 |", "|---|---|---|---|"]
    for m, label in (("baseline", "레이어 미적용"), ("layered", "레이어 적용")):
        s = stats[m]
        md.append(f"| {label} | {s['reached']}/{n} ({s['reached'] / n * 100:.0f}%) | {s['attempts'] / n:.2f} | {s['wrong']} |")
    md += ["", "건별:", "", "| 파일 | 기대 | 미적용 → | 적용 → |", "|---|---|---|---|"]
    for f in valid:
        b, l = rows[(f, "baseline")], rows[(f, "layered")]
        fmt = lambda r: f"{r['decision'] or '-'} ({r['attempts']}회){' ✗' if r['reached'] != 'True' else ''}"
        md.append(f"| {f} | {b['expected_intent']} | {fmt(b)} | {fmt(l)} |")
    (out / "results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
