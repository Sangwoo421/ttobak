# 각자 AI 에 붙여넣을 프롬프트

| 파일 | 담당 | 파트 |
|---|---|---|
| `01-ai-server.md` | 고현준 | AI 서버 (FastAPI 배선) |
| `02-backend-data.md` | 안상우 | 백엔드 — 브리핑·분류 규칙·수취인 |
| `03-backend-summary.md` | 강두형 | 백엔드 — 요약서·직원·인프라 |
| `04-frontend-senior.md` | 이성우 | 프론트 — 어르신 모드 |
| `05-frontend-staff.md` | 조태석 | 프론트 — 목업·직원 화면·측정 |

## 쓰는 법
1. 저장소를 clone 하고 자기 폴더에서 `claude` 를 실행한다.
2. 자기 파일 내용을 **통째로 복사해 첫 메시지로** 붙여넣는다. (공통 규칙 + 자기 작업 목록이 다 들어 있다)
3. 작업 1건이 끝날 때마다 커밋하고 push 한다.

## 충돌 안 나게 하는 규칙
- **자기 파일만 건드린다.** 남의 폴더·남의 클래스를 고쳐야 하면 그 사람에게 말한다.
- **`docs/contracts/` 는 아무도 혼자 못 바꾼다.** 바꿔야 하면 팀 채팅 → 고현준 확인 → 커밋 `[contracts] ...` → 전원 공지.
- 안상우·강두형은 같은 `backend/` 를 쓴다. 담당 패키지가 갈려 있으니(아래 표) 서로 그 밖은 건드리지 않는다.

| 안상우 | 강두형 |
|---|---|
| `controller/Briefing*`, `Classification*`, `Counterparty*`, `DialogLog*` | `controller/Summary*`, `Staff*` |
| `service/Briefing*`, `Classification*`, `Counterparty*`, `MuteRule*`, `DialogLog*` | `service/Summary*` |
| `rules/`, `mapper/{Counterparty,Transaction,Notification,MuteRule,DialogLog,User}*` | `provider/`, `mapper/Summary*`, `Dockerfile`, `infra/` |

- 이성우·조태석도 같은 `frontend/` 를 쓴다.

| 이성우 | 조태석 |
|---|---|
| `views/senior/`, `composables/`, `components/{Mic*,Tone*,SpeechBubble,BigButton,SeniorShell}` | `views/mock/`, `views/staff/`, `components/DevPanel`, `tools/measure/` |
| `stores/session.js` (주 담당) | `api/mock.js` |
