# 5명 역할과 작업 체크리스트

P0 = 시연 필수 / P1 = 점수 가산 / P2 = 여유. 작업 1건 = Claude Code 세션 1개. 각 항목 옆 프롬프트를 그대로 쓴다.
공통 규칙은 `CLAUDE.md`(로컬), 계약은 `docs/contracts/`. 완료 = **실행해서 확인한 결과를 보고**한 것.

---

## 고현준 — AI 서버 · 통합 리드 (`ai-server/`)

| P | Day | 작업 | 완료 기준 |
|---|---|---|---|
| P0 | 1 | 계약 최종 확인·공지 (openapi 2개, 상태 머신, 규칙표, 시드) | 팀 채팅에 "계약 v1 고정" 공지 |
| P0 | 1 | OpenAI 키 발급, `.env` 배포, `/ai/health` 에서 provider=openai 확인 | health 응답 |
| P0 | 1 | `session/start` 실제 백엔드 연동 + TTS 브리핑 재생 확인 | 브리핑 mp3 가 들림 |
| P0 | 1 | `/ai/stt` 어휘 힌트 전달, 실제 마이크 입력으로 3·4·6번 대사 인식 확인 | 3개 대사 debug 출력 |
| P0 | 2 | 자모 대조 임계값 튜닝(0.8/0.6/0.1), 서수·별칭 표면형 보강 | 테스트셋 20건 중 도달률 |
| P0 | 2 | 슬롯 채우기(수취인·금액)·CONFIRM 확인 톤·ADD_REQUEST 게이팅 | 대본 6~7 통과 |
| P0 | 2 | EXPLAIN 에서 LLM 설명(facts 만) + 실패 시 템플릿 폴백 | 4번 대사 응답 |
| P0 | 2 | `session/{id}/summary` → 백엔드 저장 → 안내 음성 | 대본 9 통과 |
| P1 | 2 | 동점 후보 LLM 선택, LLM 응답 사실 검증(숫자·고유명사) | debug.llm_rejected |
| P1 | 2 | dialog-logs 전송, TTS 캐시 워밍 스크립트(시연 대사) | audio_cache 에 대사 파일 |
| P0 | 3 | 시연 경로 안정화, 구조 슬라이드, 기술 Q&A | |

프롬프트 예:
> `ai-server/` 에서 작업. `docs/contracts/dialog-state-machine.md` 의 개체 해결 정책대로 `app/core/candidates.py` 의 임계값을 `.env` 값으로 읽게 하고, 서수 표면형에 "일번/이번/삼번/첫 거/두 번째 거"를 추가해. `pytest` 를 돌려 결과를 보여줘.

## 안상우 — 백엔드 A · 데이터·규칙 (`backend/`)

| P | Day | 작업 | 완료 기준 |
|---|---|---|---|
| P0 | 1 | mysql 시드 적용 확인, `GET /api/users/1/briefing` 이 `examples/briefing.json` 과 같은 형태 | curl 출력 |
| P0 | 1 | `heard`, `counterparties`, 뮤트 반영한 선별 | heard 후 2건 |
| P0 | 2 | 분류 규칙 엔진 R1~R5 검증(시드 6건 기대표), facts 문장 품질(시각 표현·생활어) | 6건 표 |
| P0 | 2 | `spoken_name` 존칭·축약표, 마스킹 유틸 | |
| P1 | 2 | `mute-rules`, `dialog-logs` 저장 + 조회 SQL(발표용 "같은 입력 같은 판정" 근거) | |
| P2 | 2 | 시연 데이터 다양화(입금·자동이체 추가, id 9000+) | |
| P0 | 3 | 데이터·규칙 슬라이드, Q&A(판정 재현성) | |

프롬프트 예:
> `backend/` 에서 작업. `docs/contracts/classification-rules.md` 표 순서대로 `rules/ClassificationRuleEngine` 을 검토하고, 시드 101~106 에 대해 기대 level/rule_id 가 나오는지 curl 로 6건 모두 확인해 표로 보여줘. facts 문장은 `examples/briefing.json` 과 같은 말투로.

## 강두형 — 백엔드 B · 요약서·인프라 (`backend/`, `infra/`)

| P | Day | 작업 | 완료 기준 |
|---|---|---|---|
| P0 | 1 | `docker compose up -d mysql` 전원 성공 지원, `.env` 가이드 | 5명 부팅 |
| P0 | 1 | `TransactionProvider`/`AuthProvider` 인터페이스 + Demo 구현 정리 | 서비스가 인터페이스만 의존 |
| P0 | 1 | `POST /api/summaries` (confirmed_by_user 검증, 준비물 규칙, 코드·번호표) | example 요청 → 201 |
| P0 | 2 | `by-code`, `status`, staff 목록·PATCH 상태 전이(OPEN→IN_PROGRESS→DONE) | 대본 10~11 |
| P1 | 2 | GitHub Actions 빌드 체크, 계좌 마스킹 일관성 | CI 녹색 |
| P0 | 2 | 시연 노트북 환경 고정(전체 compose `--profile full`), 핫스팟 백업 | 오프라인 부팅 |
| P0 | 2 밤 | 시연 영상 녹화(대본 1~11) | mp4 |
| P0 | 3 | 제출물 정리(GitHub, 보고서, PPT, 영상) | |

프롬프트 예:
> `backend/` 에서 작업. `PATCH /api/staff/summaries/{id}/items/{item_id}` 후 요약서 status 전이 규칙(openapi description)을 구현하고, example 요약서로 REQUEST→QUESTION 순서로 체크했을 때 IN_PROGRESS→DONE 이 되는지 curl 로 보여줘.

## 이성우 — 프론트 A · 어르신 모드 (`frontend/`)

| P | Day | 작업 | 완료 기준 |
|---|---|---|---|
| P0 | 1 | 라우팅·세션 스토어·API 연동, 브리핑 화면(카드 3장, TTS 재생, 재생 후 버튼) | 실제 AI 서버로 브리핑 |
| P0 | 1 | 녹음 composable: 침묵 VAD 2000ms(기본)/700ms(비교), 최소·최대 길이, 상태 표시 | 3번 대사 인식 |
| P0 | 2 | 대화 화면: 말풍선, 버튼(≤3), CLARIFY 선택지, `listen` 자동 마이크 | 대본 3~8 |
| P0 | 2 | 확인 톤 프레임(배경·테두리·버튼 2개), 토스트, END 처리 | 대본 6~7 |
| P0 | 2 | 요약서 화면 + status 폴링 + 완료 음성 | 대본 9·11 |
| P0 | 2 | 녹음 클립 입력 모드(파일 → /ai/stt) | 클립으로 대본 진행 |
| P1 | 2 | 접근성: 글자 22px+, 고대비, 버튼 72px+, 진동 피드백 | 정책 §6 체크 |
| P0 | 3 | 시연자, 무대 세팅 | |

프롬프트 예:
> `frontend/` 에서 작업. `src/composables/useRecorder.js` 의 VAD 가 말이 시작된 뒤 `silenceMs` 동안 조용하면 자동 종료하도록 확인하고, 개발자 패널에서 700/2000 을 토글할 수 있게 해. 브라우저에서 녹음 → `/ai/stt` 응답까지 되는지 확인해 결과를 보여줘.

## 조태석 — 프론트 B · 시연·측정·발표 (`frontend/`, `tools/measure/`, `docs/`)

| P | Day | 작업 | 완료 기준 |
|---|---|---|---|
| P0 | 1 | `/mock/home` 스타뱅킹 홈 목업 + 푸시 배너 → 브리핑 이동 | 대본 1 |
| P0 | 1 | 시연 대본 v1 확정(docs/03), 테스트셋 문장 20~30개 작성(`tools/measure/testset/manifest.csv`) | |
| P1 | 1 | 직원 화면 골격(`/staff`, 목록, 상세) | |
| P0 | 2 | 직원 화면 완성: 코드 조회, 체크 → PATCH, 상태 배지 | 대본 10 |
| P0 | 2 | 테스트셋 녹음 지휘(전원 6문장, 느리게·중간 쉬기·사투리) → wav 저장 | 파일 20+ |
| P0 | 2 | `run_measure.py` 실행 → `results/results.md` 표 + 그래프 | 표 1장 |
| P0 | 2 | PPT 초안(docs/06 구성), 리허설 1차 진행 | |
| P0 | 3 | PPT 완성, 리허설 2·3회, Q&A 문답, 발표 | |

프롬프트 예:
> `tools/measure/` 에서 작업. `run_measure.py` 가 manifest 의 각 wav 를 baseline/layered 두 모드로 AI 서버에 넣고 의도 도달률·평균 시도 횟수·오실행을 계산해 `results/results.md` 에 표로 쓰게 완성해. 샘플 3건으로 돌려 결과를 보여줘.

---

## 공통: Claude Code 프롬프트 템플릿

```
[어디서] `<폴더>/` 에서 작업한다.
[무엇을] `docs/contracts/<파일>` 의 <항목> 을 구현/수정한다.
[기준] 기대 결과는 `docs/contracts/examples/<파일>.json` / 시연 대본 <n>번.
[확인] 구현 후 <curl|pytest|npm run build|브라우저> 로 확인하고 결과를 보여줘.
[금지] 계약 파일을 바꾸지 말 것. 돈이 움직이는 코드를 넣지 말 것.
```

## 계약 변경 절차
1. 팀 채팅에 "계약 변경 제안: <파일> <내용> <이유>"
2. 고현준 확인 → `docs/contracts/` 수정 → 커밋 `[contracts] ...`
3. 영향받는 담당자가 각자 Claude Code 로 반영
