# tools/measure

후보 대조 레이어(`app/core/candidates.py`)의 성능을 숫자로 측정한다.
`app/core/`·`docs/contracts/` 는 읽기만 하고, Gemini·네트워크는 부르지 않는다.

## 실행

```bash
cd ai-server
.venv/bin/python tools/measure/text_measure.py
```

난수 시드가 고정돼 있어 매번 같은 결과가 나온다.

## 산출물

| 파일 | 내용 |
|---|---|
| `results/text-results.md` | 강도별 표 · 전체 요약 · 임계값(0.70/0.80/0.90) 비교 · 표본 |
| `testset/text-cases.csv` | 생성된 깨진 입력 200건 (깨진입력, 정답후보id, 왜곡강도, 적용한변형) |

## 무엇을 재는가

`briefing.json` + `counterparties.json` → `build_candidates()` 의 정답 표현(`surface_forms`)에
한국어 STT 오류 패턴(연음화·받침탈락·유사자음·모음혼동·띄어쓰기·군더더기)을 약(1곳)/중(2곳)/강(3곳+)
으로 적용한 뒤, `score_candidates()` → `decide(0.80, 0.60, 0.10)` 결과를
맞음 / 위험(오실행) / 되물음 / 버튼 (+ `decide()` 의 LLM_TIEBREAK = 동점보류) 으로 분류한다.
