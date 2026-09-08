# 조태석 — 진입 목업·직원 화면·측정·발표

> 아래 전체를 복사해서 `frontend/` 에서 실행한 Claude Code 의 **첫 메시지**로 붙여넣는다.
> (측정 도구 작업할 때는 `tools/measure/` 에서 따로 실행해도 된다)

---

너는 "또박또박" 해커톤 프로젝트의 **진입 목업·직원 화면·성과 측정**을 담당한다. 작업 폴더는 `frontend/` 와 `tools/measure/`, `docs/` 이고, 프론트 안에서는 **아래 담당 파일만** 수정한다. `views/senior/`, `composables/`, 음성 관련 컴포넌트는 이성우 담당이므로 건드리지 않는다.

담당: `views/mock/MockHome.vue`, `views/staff/`(StaffHome, StaffSummaryList, StaffSummaryDetail), `components/DevPanel.vue`, `api/mock.js`, `tools/measure/`, `docs/06-presentation.md`

## 프로젝트
어르신이 입출금 알림을 누르면 앱이 음성으로 읽어주고, 못 푸는 건 **창구 요약서**로 넘겨 직원 화면에 띄운다. 네가 만드는 건 이 흐름의 **시작(알림 목업)과 끝(직원 화면)**, 그리고 **그게 효과 있다는 증거(측정)** 다.

## 먼저 읽을 것
- `docs/03-demo-scenario.md` — **시연 대본 12단계. 네가 시연 진행을 책임진다.**
- `docs/06-presentation.md` — 발표 구성과 예상 Q&A
- `docs/01-judging-strategy.md` — 심사기준(기대효과 30점이 최대 배점)
- `docs/contracts/openapi-backend.yaml` — 직원 화면이 호출할 API (`/api/staff/*`, `/api/summaries/by-code/*`)
- `docs/contracts/examples/summary.json` — 요약서 모양
- `tools/measure/README.md` — 측정 방법
- `docs/07-handoff.md` — 현재 상태

## 이미 있는 것
화면들이 이미 작성돼 있지만 **동작 확인은 안 됐다.** 측정 스크립트(`run_measure.py`)도 뼈대만 있고 실제 오디오가 없다.

## 작업 순서

### 1. 빌드 + 목업 홈 확인
```powershell
cd frontend
npm install
$env:VITE_USE_MOCK='true'
npm run dev
```
`http://localhost:5173/mock/home` — KB스타뱅킹처럼 보이는가? 상단 푸시 배너("입금 300,000원 김철수")를 누르면 어르신 모드로 넘어가는가?
> 시연 1번 장면이다. **"새 앱이 아니라 기존 앱 안의 부가 모드"** 라는 메시지를 이 화면이 전달한다. 너무 공들일 필요는 없지만 은행 앱처럼 보여야 한다.

### 2. 직원 화면 (시연 10번 장면)
백엔드가 뜬 뒤 실제 연동한다.
- `/staff` — 6자리 코드 입력 → `GET /api/summaries/by-code/{code}` → 상세로 이동
- `/staff/summaries` — 목록 (번호표, 이름, 코드, 상태, 생성시각)
- `/staff/summaries/:id` — 항목별 체크박스 → `PATCH /api/staff/summaries/{id}/items/{itemId}` → 상태 배지가 `OPEN → IN_PROGRESS → DONE` 으로 바뀌는가
> **노트북 화면에 띄울 것**이므로 폰 프레임 없이 넓게, 글자는 읽기 좋게. 직원이 한눈에 "이 사람이 뭘 하러 왔는지" 파악되는 레이아웃이 중요하다.

### 3. 개발자 패널 (시연 안전장치)
`DevPanel.vue` — 화면 구석 ⚙ 아이콘으로 토글:
- **녹음 클립 입력 모드** — 마이크 대신 미리 녹음한 wav 파일을 `/ai/stt` 로 보낸다. **현장 소음이 심하면 이걸로 시연한다. 가장 중요한 백업이다.**
- 텍스트 직접 입력으로 턴 보내기
- 마지막 턴의 `debug` 표시 (intent, matched_candidate, score, decision, path) — 심사위원에게 "규칙으로 판정한다"를 보여줄 때 쓴다

### 4. 테스트셋 녹음 (Day 2 오후, 팀원 전원 동원)
`tools/measure/testset/manifest.csv` 에 14행이 있다. 각 행의 `file` 이름대로 wav 를 녹음해 같은 폴더에 넣는다.
- **한 사람이 6문장씩**, 느리게, **문장 중간에 1~2초 쉬면서**, 사투리도 섞어서
- 부족하면 행을 더 추가한다 (20~30건 목표)

### 5. 측정 실행
```powershell
cd tools/measure
python run_measure.py --ai http://localhost:8000 --manifest testset/manifest.csv --out results/
```
`results/results.md` 에 표가 나온다. **레이어 미적용 vs 적용의 의도 도달률·평균 시도 횟수·오실행 건수.**
> 이 표가 발표 7번 슬라이드다. "인식 정확도(WER)가 아니라 의도 도달률로 측정했다"가 핵심 메시지다. 숫자가 안 좋게 나와도 조작하지 마라. **"자체 구성 테스트셋 N건 기준"이라고 명시**하는 게 오히려 신뢰를 준다.

### 6. 발표 자료 (Day 2 밤 ~ Day 3)
`docs/06-presentation.md` 의 10장 구성대로 PPT 를 만든다. 배점을 기억해라:

| 항목 | 배점 |
|---|---|
| **기대효과** | **30** |
| 창의성 | 20 |
| 구현 가능성 | 20 |
| 발표력·전달력 | 20 |
| 적합성 | 10 |

기대효과가 최대 배점이다. 마지막 2장(기대효과·로드맵)에 가장 공을 들인다. 내용은 `docs/02-proposal-revisions.md` §7 에 이미 문장으로 써뒀으니 가져다 쓴다.

### 7. 리허설 (Day 2 20:00, Day 3 오전 2회)
`docs/03-demo-scenario.md` 의 리허설 체크리스트를 돌린다. **시간을 재라.** 시연은 2분 30초를 넘기면 안 된다.

## 규칙
- **시연 대본에 없는 기능을 만들지 마라.**
- 이성우 담당 파일(`views/senior/`, `composables/`, 음성 컴포넌트)을 수정하지 마라.
- `docs/contracts/` 를 혼자 바꾸지 마라.
- 측정 숫자를 꾸미지 마라. 심사위원은 과장을 알아본다.

**한 번에 한 가지씩 하고, 매번 브라우저나 실행 결과로 확인한 것을 보여줘라.**
