# 시연 런북 — 발표 직전 30분에 이 순서대로

2026-09-09 밤 실측으로 확인한 것만 적었다. 여기 없는 절차는 만들지 않았다.

## 0. 알아야 할 위험 세 가지 (전원)

| 위험 | 증상 | 대책 |
|---|---|---|
| **Gemini TTS 무료 등급은 하루 10회** (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, 429 실측) | 안 캐시된 문장이 무음 → "고장"으로 보임 | ① 시연 대사는 `ai-server/audio_cache/` 에 미리 캐시 ② 초과하면 서버가 Windows 내장 한국어 음성(Heami)으로 자동 대체 — 목소리는 기계적이지만 소리는 난다 ③ **가능하면 Gemini 프로젝트에 결제 등록**(유료 등급이면 상한이 사라진다) |
| **Gemini STT 는 분당 제한** | 연속으로 빨리 말하면 빈 문자열 → "잘 못 들었어요" | 시연 중엔 문제 없음(턴 사이 간격 충분). 리허설을 연달아 여러 번 돌리지 말 것. 막히면 개발자 패널 "녹음 클립 입력"(stub_text)로 |
| **시드 소진** | 브리핑이 "새로 들어오고 나간 돈이 없어요" | `python tools/reset_demo.py` (3초). compose 재시작 불필요 |

LLM(gemini-3.5-flash)은 thinking 을 껐다. "으음 그 저기" 같은 CLARIFY 턴이 9.9초 → 1.4~5초.

## 1. 발표 전 30분 체크리스트

```
# 1) 서비스 떠 있나
curl localhost:8080/api/health ; curl localhost:8000/ai/health   # tts/stt/llm 이 gemini 인지
docker ps                                                          # ttobak-mysql (healthy)

# 2) 데이터 초기화 (알림 3건 미청취, 시연 중 만든 요약서·대기표 삭제)
python tools/reset_demo.py

# 3) API 로 대본 1~11 완주 (프론트 없이, 30초)
ai-server/.venv/Scripts/python tools/smoke_demo.py     # 마지막 줄 "대본 1~11 API 완주 OK"

# 4) 다시 초기화 (스모크가 알림을 '들은 것'으로 바꾼다)
python tools/reset_demo.py
```

그 다음 폰 화면에서:
- [ ] `/mock/home` → 어르신(간편) 모드 홈에 거래 3줄이 보인다
- [ ] 푸시 배너 탭 → 브리핑 **소리가 난다** (안 나면 TTS 캐시/할당량 확인 → 아래 2)
- [ ] 마이크 한 번 말해보기 → 말풍선에 글이 뜬다 (안 뜨면 STT 분당 제한 → 20초 쉬고 다시)
- [ ] 노트북 `/staff` 에 코드 입력 → 요약서 뜬다
- [ ] 백업 영상 바탕화면에 있다

## 2. TTS 캐시 워밍 (Gemini 할당량 10회를 시연 대사에 쓴다)

캐시 여부는 `POST /ai/tts` 응답의 `cached` 로 안다. **하루 10회뿐이므로** 캐시 안 된 문장만 골라 한 번씩 호출하고, 호출 사이 15초 이상 띄운다. 우선순위:

1. 브리핑 문장 (session/start 가 만드는 것 — 스모크 1회로 캐시됨)
2. 3·4·5·6·7·8 단계 응답 (스모크 1회로 캐시됨)
3. 요약서 안내 "창구 갈 준비가 됐어요 … 번호표 N번이에요" — **번호표 번호가 바뀌면 새 문장**이라 캐시가 안 맞는다. 대기표를 먼저 받아 번호를 고정하고 그 번호로 한 번 돌려 둔다.
4. "창구에서 처리됐어요. 수고하셨어요." / "네, 다음에 또 불러 주세요."

## 3. 서버 재시작 (코드를 바꿨을 때)

AI 서버는 `--reload` 없이 떠 있다. 바꾼 코드는 재시작해야 반영된다.

```
# PowerShell
Get-CimInstance Win32_Process | ? { $_.Name -match 'python' -and $_.CommandLine -match '--port 8000' } | % { Stop-Process -Id $_.ProcessId -Force }
cd ai-server; Start-Process .\.venv\Scripts\python.exe -ArgumentList '-m','uvicorn','app.main:app','--port','8000' -WindowStyle Hidden
```

## 4. 죽었을 때

| 상황 | 한마디 | 행동 |
|---|---|---|
| 소리가 안 남 | "음성 대신 자막으로 이어가겠습니다" | 말풍선은 그대로 보인다. 계속 진행 |
| 마이크가 못 알아들음 2회 | "현장 소음 대비 녹음 클립을 쓰겠습니다" | 개발자 패널(제목 1.5초 길게 누르기) → 녹음 클립 입력 |
| 화면이 멈춤 | "영상으로 이어가겠습니다" | 백업 영상 |

## 5. 측정 (PPT 7번 슬라이드)

```
cd tools/measure
# AI 서버를 목 백엔드로 하나 더 띄운다 (실서버 8000 은 그대로)
cd ../../ai-server; BACKEND_MODE=mock .venv/Scripts/python -m uvicorn app.main:app --port 8001
cd ../tools/measure
../../ai-server/.venv/Scripts/python run_measure.py --ai http://localhost:8001 --pause-s 7 --label "팀원 녹음"
```

- `testset/*.wav` 는 지금 **Windows 한국어 TTS 로 합성한 예비본**이다(`--label` 로 결과표에 그렇게 적힌다). 팀원 녹음이 들어오면 같은 파일명으로 덮어쓰고 다시 돌린다. 발표에서는 출처를 그대로 말한다.
- `--pause-s 7` 은 STT 분당 제한 때문이다. 14건 × 2경로 ≈ 5분.
