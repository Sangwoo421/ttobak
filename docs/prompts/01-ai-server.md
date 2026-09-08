# 고현준 — AI 서버 (FastAPI 배선)

> 아래 전체를 복사해서 `ai-server/` 에서 실행한 Claude Code 의 **첫 메시지**로 붙여넣는다.

---

너는 "또박또박" 해커톤 프로젝트의 AI 서버를 담당한다. 작업 폴더는 `ai-server/` 이고, **이 폴더 밖은 절대 수정하지 않는다** (`docs/`, `backend/`, `frontend/`, `infra/` 는 읽기만).

## 프로젝트
어르신이 입출금 알림을 누르면 앱이 음성으로 읽어주고, 이어지는 질문을 대화로 받고, 앱이 못 푸는 것은 창구 요약서로 넘기는 서비스. AI 서버는 **음성(STT/TTS)·대화 상태 머신·어르신 모드 말투**를 담당한다.

## 먼저 읽을 것 (이게 계약이다. 여기서 벗어나지 마라)
- `docs/contracts/openapi-ai.yaml` — 네가 구현할 모든 엔드포인트와 응답 스키마
- `docs/contracts/dialog-state-machine.md` — 상태·의도 정규식·신뢰도 임계값·전이·절대 규칙
- `docs/contracts/senior-mode-policy.md` — 문장 템플릿·생활어 치환표·톤별 TTS 파라미터·LLM 사용 범위
- `docs/contracts/openapi-backend.yaml` — 네가 호출할 백엔드 API
- `docs/contracts/examples/*.json` — `session-start.json`, `turn-*.json`, `session-summary.json` 이 **네가 돌려줘야 할 정확한 모양**이다. `briefing.json`, `counterparties.json`, `summary.json` 은 백엔드가 주는 것(= mock 모드에서 읽을 것)
- `.env.example` — 설정 키와 임계값

## 이미 있는 것 (다시 짜지 마라, 읽고 그대로 써라)
`app/core/` 에 핵심 로직이 전부 있다:
- `state_machine.py` — `handle_turn()`, `TurnContext`, `TurnResult`, 모든 전이
- `templates.py` — 브리핑·설명·확인·요약 등 문장 40여 개
- `candidates.py` — 자모 분해, 유사도, `build_candidates()`, `decide()`
- `intents.py` — 의도 정규식 분류
- `amount_parser.py`, `korean_number.py`, `relative_time.py`, `policy.py`, `session_store.py`
- `app/config.py` — pydantic-settings `Settings`, `get_settings()`

**첫 작업 전에 `app/core/state_machine.py` 와 `app/config.py` 를 읽고, 어떤 인터페이스를 기대하는지 파악해라.** 나머지 파일은 필요할 때 읽어라.

## 네가 만들 것 (없는 것 전부)

1. **`app/main.py`** — FastAPI 앱. CORS 는 `http://localhost:5173` 허용. 라우터 등록. `/ai/audio` 를 `ai-server/audio_cache/` 에 StaticFiles 로 마운트.
2. **`app/routers/`** — `health.py`, `session.py`, `stt.py`, `turn.py`, `tts.py`, `summary.py`, `debug.py`. 경로·요청·응답은 `openapi-ai.yaml` 그대로.
3. **`app/providers/`**
   - `base.py` — Protocol: `STTProvider.transcribe(audio_bytes, filename, hints)`, `TTSProvider.synthesize(text, tone) -> (bytes, ext)`, `LLMProvider.classify_intent()` / `.choose_candidate()` / `.explain()`
   - `openai_provider.py` — STT `audio.transcriptions.create(model=..., language="ko", prompt=", ".join(hints))`, TTS `audio.speech.create(..., instructions=<톤 지시>, speed=<톤 속도>)`, LLM `chat.completions` + `response_format={"type":"json_object"}`
   - `stub_provider.py` — **네트워크 없이 도는 폴백.** STT 는 multipart 의 `stub_text` 필드를 그대로 반환(없으면 고정 문자열), TTS 는 `wave` 표준 라이브러리로 0.5초 무음 wav 생성, LLM 은 intent UNKNOWN conf 0.3
   - `anthropic_llm.py` — 선택. Anthropic SDK 사용 (지금은 뒤로 미뤄도 됨)
   - `factory.py` — 설정에 따라 provider 선택. **모든 provider 호출은 try/except 로 감싸서 예외 시 stub 결과를 쓰고 `debug` 에 오류를 기록한다. 시연 중 API 실패로 앱이 죽으면 안 된다.**
4. **`app/clients/`** — `backend_client.py`(httpx 로 백엔드 호출), `mock_backend.py`(`docs/contracts/examples/*.json` 을 읽어 같은 인터페이스 제공). `BACKEND_MODE=mock` 이면 후자.
5. **`app/services/audio_cache.py`** — `sha1(text+tone+model)` → `audio_cache/<hash>.<ext>`, URL `/ai/audio/<파일명>` 반환, `cached` 플래그.
6. **`tests/`** — `test_candidates.py`, `test_amount_parser.py`, `test_korean_number.py`, `test_intents.py`, `test_demo_flow.py`
7. **`Dockerfile`** — `python:3.12-slim`, `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## 절대 규칙
- **돈이 움직이는 코드를 쓰지 않는다.** 이체 실행 API 를 만들지 않는다. "이체 요청"은 창구 요약서에 담기는 것뿐이다.
- **`ADD_REQUEST` 는 `CONFIRM` 상태에서 YES 를 받은 직후에만** 생성된다. 다른 경로 없음.
- **판정은 코드, 설명만 LLM.** LLM 은 백엔드가 준 `facts` 밖의 숫자·이름을 말하면 안 된다.
- **음성 원본을 저장하지 않는다.** 메모리에서 처리하고 임시 파일은 지운다.
- JSON 필드는 전부 snake_case.
- `docs/contracts/` 를 수정하지 않는다. 바꿔야 하면 팀에 먼저 말한다.

## 작업 순서 (한 번에 하나씩, 각각 끝나면 확인하고 커밋)
1. `main.py` + `routers/health.py` + `providers/stub_provider.py` + `factory.py` → `uvicorn` 띄우고 `/ai/health` 확인
2. `clients/mock_backend.py` + `routers/session.py` + `services/audio_cache.py` → `POST /ai/session/start {"user_id":1}` 이 `examples/session-start.json` 과 같은 모양인지 확인
3. `routers/turn.py` (state_machine 연결) → 대본 7턴 수동 확인
4. `routers/stt.py`, `tts.py`, `summary.py`, `debug.py`
5. `providers/openai_provider.py` → 실제 키로 브리핑 음성 재생
6. `clients/backend_client.py` → `BACKEND_MODE=http` 로 실제 백엔드 연동
7. `tests/` → `pytest` 전부 통과
8. `Dockerfile`

## 검증 (매 작업 후 실제로 실행하고 결과를 보여줄 것)
```powershell
cd ai-server
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:BACKEND_MODE='mock'
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
# 다른 창에서
Invoke-RestMethod http://localhost:8000/ai/health
Invoke-RestMethod -Method Post http://localhost:8000/ai/session/start -ContentType application/json -Body '{"user_id":1}'
```
`test_demo_flow.py` 는 `docs/contracts/dialog-state-machine.md` 마지막의 **시연 시나리오 7턴**을 그대로 재현하고, 각 턴의 state·matched·action 을 단언한다. 특히 "CONFIRM+YES 없이 ADD_REQUEST 가 나오지 않는다"를 반드시 테스트한다.

**"될 것 같다"는 완료가 아니다. 실행해서 나온 출력을 보여줘야 완료다.**
