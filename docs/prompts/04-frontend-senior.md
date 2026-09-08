# 이성우 — 프론트엔드 (어르신 모드 화면·음성)

> 아래 전체를 복사해서 `frontend/` 에서 실행한 Claude Code 의 **첫 메시지**로 붙여넣는다.

---

너는 "또박또박" 해커톤 프로젝트의 **어르신 모드 화면과 음성 입출력**을 담당한다. 작업 폴더는 `frontend/` 이고, 그 안에서도 **아래 담당 파일만** 수정한다. `views/mock/`, `views/staff/`, `components/DevPanel.vue`, `api/mock.js` 는 조태석 담당이므로 건드리지 않는다.

담당: `views/senior/`, `composables/`(useRecorder, useAudioPlayer, useConversation), `components/`(MicButton, MicStatus, ToneFrame, SpeechBubble, BigButton, SeniorShell, LevelBadge, SummaryCard, PhoneFrame), `stores/session.js`, `styles/base.css`

## 프로젝트
어르신이 입출금 알림을 누르면 앱이 음성으로 읽어주고, 이어지는 질문을 대화로 받고, 앱이 못 푸는 것은 창구 요약서로 넘긴다. **어르신 모드에서 바뀌는 것은 글씨 크기가 아니라 대화 방식이다.**

## 먼저 읽을 것 (계약이다)
- `docs/03-demo-scenario.md` — **시연 대본 12단계. 여기 없는 기능은 만들지 않는다.**
- `docs/contracts/senior-mode-policy.md` — 특히 §3 톤, §6 화면 규칙
- `docs/contracts/openapi-ai.yaml` — 네가 호출할 AI 서버 API
- `docs/contracts/dialog-state-machine.md` — 상태별로 어떤 버튼이 뜨는지
- `docs/contracts/examples/session-start.json`, `turn-*.json` — AI 서버 응답 모양
- `docs/07-handoff.md` — 현재 상태

## 이미 있는 것
화면과 컴포넌트가 이미 다 작성돼 있다. **하지만 `npm run build` 도 브라우저 동작도 확인한 적이 없다.** 네 일은 새로 짜는 게 아니라 **검증하고 고치고 다듬는 것**이다.

## 작업 순서

### 1. 빌드부터 (최우선)
```powershell
cd frontend
npm install
npm run build
```
에러가 나면 고친다. 이게 통과해야 나머지가 의미 있다.

### 2. 목 모드로 화면 확인
```powershell
$env:VITE_USE_MOCK='true'
npm run dev
```
브라우저에서 `http://localhost:5173/mock/home` → 푸시 배너 탭 → 브리핑 → 대화 화면까지 흐름이 이어지는지 본다. 깨진 화면을 고친다.

### 3. 녹음과 발화 종료 판정 (이 프로젝트의 핵심 기능 중 하나)
`composables/useRecorder.js` 를 실제 브라우저에서 마이크로 테스트한다.
- 말이 시작된 뒤 **침묵이 `silenceMs` 동안 이어지면 자동 종료**되는가 (기본 2000ms)
- **문장 중간에 2초 쉬어도 끊기지 않는가** — 어르신은 문장 중간에 수 초씩 쉰다. 이게 이 서비스가 푸는 문제다
- 최소 0.8초, 최대 15초 제한이 도는가
- 마이크 권한 거부·미지원 브라우저에서 죽지 않는가

### 4. AI 서버 연동 (고현준의 서버가 뜬 뒤)
`VITE_USE_MOCK=false` 로 실제 연동한다.
- 브리핑 음성이 재생되고, 재생이 끝난 뒤 버튼이 나타나는가
- 마이크 → `/ai/stt` → `/ai/turn` → 응답 음성 재생이 왕복하는가
- `ui.listen` 이 true 면 음성 재생 후 자동으로 마이크가 켜지는가

### 5. 확인 톤 (시연의 결정적 장면)
응답의 `tone` 이 `confirm` 이면 화면이 눈에 띄게 바뀌어야 한다. **화면 글자를 못 읽어도 "지금이 중요한 순간"이라는 게 전달되는 것**이 목적이다.
- 배경색·테두리 변경, 버튼은 [맞아요] [아니에요] 둘만 크게
- `friendly` 로 돌아오면 원래대로

### 6. 요약서 화면
- 3구획(하려던 일 / 여쭤볼 것 / 준비물) + **6자리 코드를 아주 크게**
- `GET /api/summaries/{id}/status` 를 3초마다 폴링 → `DONE` 이 되면 "창구에서 처리됐어요. 수고하셨어요." 를 TTS 로 한 번 재생

### 7. 접근성 (`senior-mode-policy.md` §6)
- 버튼 최소 높이 72px, 글자 22px 이상, 한 화면에 버튼 3개 이하
- 음성으로 말한 내용은 **항상 화면에도 크게** 표시
- 마이크 상태를 색과 글로: "말씀하세요" / "듣고 있어요" / "생각 중이에요"
- 어떤 상태에서도 **[그만] 버튼이 보인다**
- 고대비, 큰 터치 영역

## 규칙
- **시연 대본에 없는 기능을 만들지 마라.** 시간이 없다.
- 새 UI 라이브러리를 넣지 마라. 지금은 순수 CSS 다.
- `docs/contracts/` 를 혼자 바꾸지 마라. AI 서버 응답 모양이 안 맞으면 고현준에게 말한다.
- 조태석 담당 파일(`views/mock/`, `views/staff/`, `DevPanel.vue`, `api/mock.js`)을 수정하지 마라.
- 음성이 안 될 상황(소음·권한 거부)을 항상 대비해 **버튼으로도 같은 일을 할 수 있게** 둔다. 이건 기획의 핵심이다.

**한 번에 한 가지씩 하고, 매번 `npm run build` 또는 브라우저에서 실제로 확인한 결과를 보여줘라.**
