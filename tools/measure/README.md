# 측정 도구 — 음성 대응 레이어 적용 전/후 비교

같은 오디오를 두 경로에 넣고 **의도 도달률 · 평균 시도 횟수 · 오실행 건수**를 비교한다. STT 엔진이 같으므로 차이는 레이어에서만 난다.

| 경로 | 발화 종료 대기 | 어휘 힌트 | 대조 방식 |
|---|---|---|---|
| baseline | 700ms 침묵에서 절단(오프라인 VAD 로 모사) | 없음 | 단순 문자열 포함 |
| layered | 전체 오디오(2000ms 대기 모사) | 세션 수취인·거래 상대명 | 자모 편집거리 + 신뢰도 게이팅 |

## 준비
1. `testset/manifest.csv` 의 각 행에 해당하는 wav 를 `testset/` 에 녹음해 넣는다. 16kHz mono wav 권장(브라우저 녹음이면 webm 도 됨, 이 경우 baseline 절단은 생략).
   - 느리게, 문장 중간에 1~2초 쉬고, 사투리 흉내도 섞는다. 한 사람이 6문장씩.
2. AI 서버를 실제 백엔드 또는 mock 으로 띄운다 (`BACKEND_MODE=mock` 이면 시드와 동일한 후보가 나온다).
3. `pip install httpx` (ai-server 의 venv 를 그대로 써도 된다).

## 실행
```
python run_measure.py --ai http://localhost:8000 --manifest testset/manifest.csv --out results/
```
결과: `results/results.md` (PPT 표), `results/details.csv` (건별 debug).

## 지표 정의
- **의도 도달**: `expected_intent` 가 UNKNOWN 이면 CLARIFY 로 간 것이 도달. 그 외에는 debug.intent 일치 **그리고** (expected_entity 가 있으면) matched_candidate 일치.
- **시도 횟수**: decision ACCEPT=1, ASK_AGAIN=2, BUTTON/CLARIFY=3, 오인식 채택=3(실패).
- **오실행**: 잘못된 개체가 ACCEPT 로 채택된 건수(확정 단계로 들어감). 구조상 0 이 목표.
