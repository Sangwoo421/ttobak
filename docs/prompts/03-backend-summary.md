# 강두형 — 백엔드 (창구 요약서·직원 화면 API·인프라)

> 아래 전체를 복사해서 `backend/` 에서 실행한 Claude Code 의 **첫 메시지**로 붙여넣는다.

---

너는 "또박또박" 해커톤 프로젝트의 백엔드 중 **창구 요약서·직원 API·인프라** 파트를 담당한다. 작업 폴더는 `backend/` 와 `infra/` 이고, 백엔드 안에서도 **아래 담당 파일만** 수정한다. 나머지(`Briefing*`, `Classification*`, `Counterparty*`, `rules/`)는 안상우 담당이므로 건드리지 않는다.

담당: `controller/{Summary,Staff}Controller.java`, `service/SummaryService.java`, `mapper/SummaryMapper.java` + `resources/mapper/SummaryMapper.xml`, `provider/`(TransactionProvider, AuthProvider, Demo 구현), `Dockerfile`, `infra/docker-compose.yml`, `.github/workflows/ci.yml`

## 프로젝트
어르신이 앱에서 대화로 정리한 "창구에서 하려던 일 / 여쭤볼 것 / 준비물"을 **요약서**로 만들어 창구 직원 화면에 넘긴다. 이게 이 서비스의 핵심 차별점이다. AI 가 답을 못 하는 지점이 실패가 아니라 창구로 이어지는 정상 경로다.

## 먼저 읽을 것 (계약이다)
- `docs/contracts/openapi-backend.yaml` — 특히 `/api/summaries*`, `/api/staff/*` 절
- `docs/contracts/examples/summary-create-request.json`, `summary.json` — **요청과 응답의 정확한 모양**
- `docs/contracts/seed-data.sql` — `counter_summaries`, `summary_items` 테이블
- `docs/03-demo-scenario.md` 9~11번 — 요약서가 시연에서 어떻게 쓰이는지
- `docs/07-handoff.md` — 현재 상태와 확인 필요 항목

## 이미 있는 것
코드는 이미 다 작성돼 있고 `gradlew build` 는 통과한다. **하지만 한 번도 실행해서 확인한 적이 없다.** 네 일은 새로 짜는 게 아니라 **검증하고 고치는 것**이다.

## 작업 순서

### 1. 포트 정리 + DB 기동 (최우선, 팀 전체가 막힌다)
이 PC 는 3306 을 다른 프로젝트 컨테이너가 쓰고 있어서 mysql 을 3307 로 띄웠다. 팀 표준 포트를 정하고 `.env.example` 과 `docs/07-handoff.md` 에 반영해라.
```powershell
docker compose -f infra/docker-compose.yml up -d mysql
docker inspect --format '{{.State.Health.Status}}' ttobak-mysql
```

### 2. 요약서 전체 흐름 실행 검증
```powershell
cd backend
.\gradlew.bat bootRun --no-daemon
# 다른 창에서
$body = Get-Content docs/contracts/examples/summary-create-request.json -Raw
$s = Invoke-RestMethod -Method Post http://localhost:8080/api/summaries -ContentType 'application/json; charset=utf-8' -Body $body
$s | ConvertTo-Json -Depth 6
```
확인할 것:
- `code` 가 6자리 숫자, `ticket_no` 가 8 (시드에 7번이 있으므로)
- items 4개: REQUEST 1, QUESTION 1, PREP 2 (`신분증` required=true, `통장 또는 카드` required=false)
- `recipient_account_masked` 가 수취인 정보로 채워졌는지
- `confirmed_by_user: false` 로 보내면 **400** 이 나는지 (이게 안전장치다. 반드시 확인)

### 3. 조회·처리 흐름
- `GET /api/summaries/by-code/{code}` → 직원 화면 진입
- `GET /api/staff/summaries` → 목록 (item_count 는 PREP 제외)
- `PATCH /api/staff/summaries/{id}/items/{itemId}` `{"handled":true}` → REQUEST 체크 후 `IN_PROGRESS`, QUESTION 까지 체크하면 `DONE`
- `GET /api/summaries/{id}/status` → 어르신 앱이 폴링하는 것. `handled_count`/`total_count` 는 PREP 제외

### 4. 외부 경계 인터페이스 정리
`provider/TransactionProvider`, `AuthProvider` 는 **실제 뱅킹 앱에 편입될 때 교체할 경계면**이다. 발표에서 "이 인터페이스만 갈아끼우면 된다"고 말할 부분이니, 서비스가 인터페이스에만 의존하고 Demo 구현은 갈아끼울 수 있게 돼 있는지 확인한다.

### 5. 전체 컨테이너 기동
```powershell
docker compose -f infra/docker-compose.yml --profile full up --build
```
3서비스가 다 뜨고 프론트에서 백엔드까지 닿는지 확인. 안 되면 고친다. **현장 네트워크가 불안할 수 있으니 로컬에서 전부 도는 게 중요하다.**

### 6. 계약 해석 2건 판단 (`docs/07-handoff.md`)
- `SummaryCreateRequest.session_id` 를 저장할지 (지금은 무시. 저장하려면 컬럼 추가 필요)
- 요약서 상태 전이 규칙 (지금은 아무 항목이나 처리되면 IN_PROGRESS)

### 7. 시연 환경 고정 (Day 2 밤)
- 시연용 노트북에서 `down -v && up -d mysql` 로 시드 초기화 → 알림 3건 미청취 상태 확인
- 시연 영상 녹화 (`docs/03-demo-scenario.md` 1~11번)

## 규칙
- **돈이 움직이는 API 를 만들지 않는다.** 이체 실행·잔액 변경 코드가 이 저장소에 있으면 안 된다. 요약서는 "창구에서 할 일 목록"일 뿐이다.
- **`confirmed_by_user` 검증을 절대 빼지 마라.** 사용자가 확인 톤에서 "맞아요"를 누르지 않은 요청은 저장되면 안 된다.
- 계좌번호는 항상 마스킹해서 내보낸다.
- JSON 필드는 전부 snake_case.
- `docs/contracts/` 를 혼자 바꾸지 마라.
- 안상우 담당 파일(`Briefing*`, `Classification*`, `Counterparty*`, `rules/`)을 수정하지 마라.

**한 번에 한 가지씩 하고, 매번 실제로 실행해서 나온 출력을 보여줘라. "될 것 같다"는 완료가 아니다.**
