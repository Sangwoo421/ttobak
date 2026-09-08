# 또박또박

어르신이 창구에 가기 전에, 앱이 말로 미리 정리해주는 서비스. 2026 KB IT's Your Life 해커톤 (팀 유종의 미)

> 어르신이 입출금 알림을 누르면 앱이 **말로 읽어주고**, 이어지는 질문을 **대화로 받고**, 앱이 못 푸는 것은 **창구 요약서**로 넘긴다.
> 트랙: 디지털 금융약자 지원

세 가지 약속: **못 알아들어도 하려던 일에 도달한다** · **모르면 지어내지 않고 창구로 넘긴다** · **AI 에게 돈을 움직일 권한을 주지 않는다**

## 팀원이라면 먼저

1. [docs/07-handoff.md](docs/07-handoff.md) — 지금 어디까지 됐고 내 파트에 뭐가 남았는지
2. [docs/prompts/](docs/prompts/) — 내 파일을 복사해 Claude Code 첫 메시지로 붙여넣기
3. 아래 빠른 시작으로 환경 부팅

## 빠른 시작 (팀원용, 10분)

```bash
# 0. 저장소 받기 + 키 준비
git clone <repo> && cd hack
cp .env.example .env          # OPENAI_API_KEY 채우기 (없으면 stub 모드로도 뜬다)

# 1. DB
docker compose -f infra/docker-compose.yml up -d mysql     # 시드 자동 적용

# 2. 백엔드 (:8080)
cd backend && ./gradlew bootRun          # Windows: .\gradlew.bat bootRun
curl localhost:8080/api/users/1/briefing

# 3. AI 서버 (:8000)
cd ai-server && python -m venv .venv && .venv/Scripts/activate   # mac: source .venv/bin/activate
pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000
curl -X POST localhost:8000/ai/session/start -H "content-type: application/json" -d "{\"user_id\":1}"

# 4. 프론트 (:5173)
cd frontend && npm install && npm run dev
# 브라우저: http://localhost:5173/mock/home → 푸시 배너 탭
```

전체를 컨테이너로: `docker compose -f infra/docker-compose.yml up --build`

## 문서

| 문서 | 내용 |
|---|---|
| **[docs/07-handoff.md](docs/07-handoff.md)** | **현재 상태와 파트별 남은 일 — 여기부터 읽는다** |
| **[docs/prompts/](docs/prompts/)** | **각자 AI 에 붙여넣을 프롬프트 5개** |
| [docs/00-plan.md](docs/00-plan.md) | 전체 계획 (심사 전략·기술 결정·시간표) |
| [docs/01-judging-strategy.md](docs/01-judging-strategy.md) | 심사기준별 점수 전략 |
| [docs/02-proposal-revisions.md](docs/02-proposal-revisions.md) | 기획서 수정·추가 문안 |
| [docs/03-demo-scenario.md](docs/03-demo-scenario.md) | 시연 대본 (개발의 북극성) |
| [docs/04-roles-and-tasks.md](docs/04-roles-and-tasks.md) | 5명 역할별 체크리스트 + Claude Code 프롬프트 |
| [docs/05-timeline.md](docs/05-timeline.md) | 2박3일 시간표·체크포인트 |
| [docs/06-presentation.md](docs/06-presentation.md) | PPT 구성·예상 Q&A |
| [docs/contracts/](docs/contracts/) | API·상태 머신·분류 규칙·말투 정책·시드 (단일 진실) |
| [CLAUDE.md](CLAUDE.md) | AI 코딩 공통 규칙 |

## 구조

```
frontend (Vue)  ──오디오/버튼──▶  ai-server (FastAPI)  ──REST──▶  backend (Spring Boot)  ── MySQL
     │                                 │ STT / TTS / LLM
     └──요약서 조회·직원 화면──────────────────────────────────▶  backend
```

- **backend**: 데이터, 브리핑 선별, 확인 가능 여부 규칙 엔진, 창구 요약서, 직원 API
- **ai-server**: 음성 대응 레이어(발화 종료 대기·어휘 힌트·후보 대조), 대화 상태 머신, 어르신 모드 말투, TTS
- **frontend**: 스타뱅킹 진입 목업, 어르신 모드 화면, 직원용 요약서 화면
- **tools/measure**: 레이어 적용 전/후 의도 도달률·오실행 측정
