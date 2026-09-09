# 안상우 — 백엔드 (브리핑·분류 규칙·수취인)

> 아래 전체를 복사해서 `backend/` 에서 실행한 Claude Code 의 **첫 메시지**로 붙여넣는다.

---

너는 "또박또박" 해커톤 프로젝트의 백엔드 중 **데이터·판정 규칙** 파트를 담당한다. 작업 폴더는 `backend/` 이고, 그 안에서도 **아래 담당 파일만** 수정한다. 다른 파일(`Summary*`, `Staff*`, `provider/`, `Dockerfile`)은 강두형 담당이므로 건드리지 않는다.

담당: `controller/{Briefing,Classification,Counterparty,DialogLog}Controller.java`, `service/{Briefing,Classification,Counterparty,MuteRule,DialogLog}Service.java`, `rules/ClassificationRuleEngine.java`, `mapper/{Counterparty,Transaction,Notification,MuteRule,DialogLog,User}Mapper.java` + 같은 이름의 `resources/mapper/*.xml`, `docs/contracts/seed-data.sql`(시연 데이터 추가 시)

## 프로젝트
어르신이 입출금 알림을 누르면 앱이 음성으로 읽어주고, 못 푸는 건 창구 요약서로 넘기는 서비스. 백엔드는 **데이터와 판정(규칙 엔진)** 을 담당한다. 대화·음성은 AI 서버(고현준)가 한다.

## 먼저 읽을 것 (계약이다)
- `docs/contracts/openapi-backend.yaml` — 엔드포인트와 응답 스키마
- `docs/contracts/classification-rules.md` — **R1~R5 규칙표, 존칭·축약표, 시드 6건 기대 결과**
- `docs/contracts/seed-data.sql` — 스키마와 시연 데이터
- `docs/contracts/examples/briefing.json`, `counterparties.json`, `classification-103.json` — **네 API 가 돌려줘야 할 정확한 모양**
- `docs/07-handoff.md` — 현재 상태와 "계약 해석 확인 필요" 6건

## 이미 있는 것
코드는 이미 다 작성돼 있고 `gradlew build` 는 통과한다. **하지만 한 번도 실행해서 확인한 적이 없다.** 네 일은 새로 짜는 게 아니라 **검증하고 고치는 것**이다.

## 작업 순서

### 1. 실행 검증 (최우선)
```powershell
docker compose -f infra/docker-compose.yml up -d mysql
cd backend
.\gradlew.bat bootRun --no-daemon
# 다른 창에서
Invoke-RestMethod http://localhost:8080/api/users/1/briefing | ConvertTo-Json -Depth 8
```
> MySQL 이 3306 에서 안 뜨면 다른 컨테이너가 쓰는 중이다. `$env:MYSQL_PORT='3307'` 로 띄우고 백엔드에도 같은 값을 준다.

응답이 `docs/contracts/examples/briefing.json` 과 **필드 이름·구조·값이 같은지** 대조한다. 다르면 고친다.

### 2. 분류 규칙 전수 확인
거래 101~106 각각 `GET /api/transactions/{id}/classification` 을 호출해 아래 표와 맞는지 확인하고, 결과를 표로 보여준다.

| id | 상대 | 기대 rule_id | 기대 level |
|---|---|---|---|
| 101 | 김철수(아들) | R1_REGISTERED_PERSON | CONFIRMED |
| 102 | 한국전력공사 | R2_REGISTERED_INSTITUTION | PARTIAL |
| 103 | 국민라이프 | R5_UNKNOWN | UNKNOWN |
| 104 | 국민연금공단 | R2_REGISTERED_INSTITUTION | PARTIAL |
| 105 | 수수료 | R4_FEE | UNKNOWN |
| 106 | 김영희(딸) | R1_REGISTERED_PERSON | CONFIRMED |

### 3. 나머지 엔드포인트 확인
- `POST /api/notifications/1001/heard` → 이후 briefing 이 2건으로 줄어드는지
- `GET /api/users/1/counterparties` → `aliases` 가 배열로 나오는지
- `POST /api/mute-rules` → 뮤트한 상대가 briefing 에서 빠지는지
- `POST /api/dialog-logs` → 저장되는지

### 4. facts 문장 다듬기
`facts` 는 AI 서버가 그대로 읽거나 LLM 에 넘기는 **완결된 짧은 한국어 문장**이어야 한다. `examples/briefing.json` 의 어투와 맞춘다.

### 5. 계약 해석 4건 판단 (`docs/07-handoff.md` 참고)
1. 계좌 마스킹 형식 — 지금은 `3333-01-****67`
2. 시각 표현 — 지금은 11~17시를 "낮". 예시 JSON 은 "어제 오후". 어느 쪽으로 통일할지
3. R4 수수료의 `spoken_name` — 지금은 `수수료`
4. PERSON 존칭 — 지금은 손자도 "손자 박민수 님"

바꾸기로 하면 고치고, 그대로 두기로 하면 `docs/07-handoff.md` 의 표를 "확정"으로 업데이트한다.

## 규칙
- **규칙 엔진은 DB 값과 정규식만 본다.** LLM 호출, 외부 API 호출을 넣지 마라. 같은 입력이면 같은 결과가 나와야 한다(사후 검증 가능해야 함).
- **돈이 움직이는 API 를 만들지 않는다.** 잔액 변경, 이체 실행 코드가 이 저장소에 있으면 안 된다.
- JSON 필드는 전부 snake_case (Jackson 전역 설정돼 있음).
- **시드 데이터를 지우지 마라.** 테스트용이 필요하면 id 9000 이상을 쓴다.
- `docs/contracts/` 의 스키마를 혼자 바꾸지 마라. 바꿔야 하면 팀에 먼저 말한다.
- 강두형 담당 파일(`Summary*`, `Staff*`, `provider/`)을 수정하지 마라.

**한 번에 한 가지씩 하고, 매번 실제로 실행해서 나온 출력을 보여줘라. "될 것 같다"는 완료가 아니다.**
