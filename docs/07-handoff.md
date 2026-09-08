# 현재 상태와 인계 (2026-09-08 작성)

초기 뼈대는 AI 로 한 번에 생성했다. **완성본이 아니다.** 아래 표의 "남은 일"부터 각자 자기 파트를 이어서 짠다.
각자 `docs/prompts/` 의 자기 파일을 Claude Code 에 그대로 붙여넣고 시작하면 된다.

## 한눈에

| 파트 | 담당 | 상태 | 검증 |
|---|---|---|---|
| `backend/` | 안상우 · 강두형 | 코드 **완성** (Java 53, MyBatis XML 7) | `gradlew build` 성공. **실행·API 호출은 미검증** |
| `ai-server/` | 고현준 | 핵심 로직 **완성**, FastAPI 배선 **없음** | 미검증 |
| `frontend/` | 이성우 · 조태석 | 화면·컴포넌트 **완성** | `npm install` 완료. **build·동작 미검증** |
| `docs/` `docs/contracts/` | 전원 | 완성 | — |
| `infra/` `tools/measure/` `.github/` | 강두형 · 조태석 | 완성 | mysql 컨테이너 기동 확인 |

## 파트별 남은 일

### backend — 안상우 (데이터·규칙)
있는 것: `BriefingService`, `ClassificationRuleEngine`(R1~R5), `CounterpartyService`, `MuteRuleService`, `DialogLogService`, MyBatis 매퍼 7종.
남은 일:
1. **실행 검증** — `bootRun` 후 `/api/users/1/briefing` 이 `docs/contracts/examples/briefing.json` 과 같은 모양인지 확인
2. 시드 101~106 의 분류 결과가 `classification-rules.md` 기대표와 맞는지 6건 전수 확인
3. `facts` 문장 말투 다듬기 (예시 JSON 과 같은 어투)
4. 아래 "계약 해석 확인 필요" 6건 중 1·2·3·4번 판단

### backend — 강두형 (요약서·인프라)
있는 것: `SummaryService`(코드·번호표·준비물·상태 전이), `StaffController`, `TransactionProvider`/`AuthProvider` + Demo 구현, `Dockerfile`.
남은 일:
1. **실행 검증** — 요약서 생성 → `by-code` 조회 → 항목 체크 → `OPEN→IN_PROGRESS→DONE`
2. **포트 충돌 해결** — 이 PC 는 3306 을 다른 컨테이너가 쓰고 있어 mysql 을 3307 로 띄웠다. 팀 표준 포트를 정하고 `.env` 에 고정
3. 전체 `docker compose --profile full up --build` 로 3서비스 동시 기동
4. 계약 해석 5·6번 판단

### ai-server — 고현준
있는 것 (`app/core/`, `app/config.py`): `state_machine.py`(전이 전부), `templates.py`(문장 40여 개), `candidates.py`(자모 분해·유사도·게이팅), `intents.py`, `amount_parser.py`, `korean_number.py`, `relative_time.py`, `policy.py`, `session_store.py`.
**없는 것 (이게 남은 일 전부):**
1. `app/main.py` — FastAPI 앱, CORS, `/ai/audio` 정적 마운트
2. `app/routers/` — health, session, stt, turn, tts, summary, debug (7개)
3. `app/providers/` — `base.py`(Protocol), `openai_provider.py`, `anthropic_llm.py`, `stub_provider.py`, `factory.py`
4. `app/clients/` — `backend_client.py`(httpx), `mock_backend.py`(examples JSON 읽기)
5. `app/services/audio_cache.py` — sha1 해시 파일 캐시
6. `tests/` — 5개 테스트
7. `Dockerfile`

### frontend — 이성우 (어르신 모드)
있는 것: `SeniorBriefing.vue`, `SeniorChat.vue`, `SeniorSummary.vue`, `useRecorder.js`(VAD), `useAudioPlayer.js`, `useConversation.js`, `ToneFrame.vue`, `MicButton/MicStatus`, `BigButton`, `SpeechBubble`.
남은 일:
1. **`npm run build` 성공 확인** (미검증)
2. 브라우저에서 실제 마이크 녹음 → VAD 자동 종료 → `/ai/stt` 왕복
3. 확인 톤 프레임 시각 전환, 접근성(글자 22px+ / 버튼 72px+ / 고대비)

### frontend — 조태석 (목업·직원·측정·발표)
있는 것: `MockHome.vue`, `StaffHome/StaffSummaryList/StaffSummaryDetail.vue`, `DevPanel.vue`, `tools/measure/run_measure.py`, `testset/manifest.csv`(14행).
남은 일:
1. 직원 화면 실제 백엔드 연동 확인 (코드 조회 → 체크 → 상태 배지)
2. 테스트셋 녹음 지휘 (전원 6문장씩) → `tools/measure/testset/*.wav`
3. `run_measure.py` 실행 → `results/results.md` 표
4. PPT (`docs/06-presentation.md` 구성대로)

## 계약 해석 — 확인 필요 6건

백엔드 생성 시 애매한 부분을 아래처럼 정했다. 담당자가 확인하고 바꿀 것은 바꾼다.

| # | 정한 것 | 확인 |
|---|---|---|
| 1 | 계좌 마스킹 = 마지막 그룹을 `****` + 끝 2자리 (`3333-01-1234567` → `3333-01-****67`) | 안상우 |
| 2 | 시각 표현에서 11~17시를 "낮"으로 씀. 예시 JSON 은 "어제 오후" | 안상우 (예시에 맞추려면 "오후") |
| 3 | R4(수수료)의 `spoken_name` 은 `수수료` (`'수수료'이라는 곳` 아님) | 안상우 |
| 4 | PERSON `spoken_name` 은 일괄 `{존칭} {name} 님` → 손자도 "손자 박민수 님" | 안상우 |
| 5 | `SummaryCreateRequest.session_id` 는 저장 컬럼이 없어 무시 | 강두형 |
| 6 | 요약서 상태: REQUEST+QUESTION 전부 처리 → DONE / 아무거나 하나 처리 → IN_PROGRESS | 강두형 |

## 알려진 환경 이슈
- **MySQL 포트**: 이 PC 에서 3306 이 이미 사용 중이라 3307 로 기동했다. 각자 `MYSQL_PORT` 를 `.env` 에 맞춰 넣을 것.
- **API 키 없음**: `.env` 의 `OPENAI_API_KEY` 가 비면 AI 서버는 stub 모드로 동작하게 설계돼 있다(고현준이 `stub_provider.py` 를 만들면). 키 발급 전까지 이걸로 개발한다.
- **`CLAUDE.md` 는 저장소에 없다** (팀 결정). 각자 AI 지침은 `docs/prompts/` 의 자기 파일에 들어 있다.
