# AGENTS.md

이 문서는 이 저장소에서 작업하는 코딩 에이전트의 공통 규칙이다. 저장소 루트와 모든 하위 디렉터리에 적용한다. 더 구체적인 하위 `AGENTS.md`가 생기면 해당 디렉터리에서는 하위 문서가 우선한다.

## 프로젝트 목표

`또박또박`은 어르신이 입출금 알림을 음성으로 듣고 질문한 뒤, 앱이 확실히 답하지 못하는 일은 창구 요약서로 이어 주는 해커톤 프로젝트다.

항상 다음 원칙을 지킨다.

- 사용자가 잘못 말하거나 음성 인식에 실패해도 버튼과 재질문으로 원래 목적에 도달하게 한다.
- 모르는 내용을 추측하지 않는다. 확인할 수 없는 내용은 창구 질문 또는 요청으로 넘긴다.
- AI가 돈을 움직이게 하지 않는다. 이체 실행, 잔액 변경 등 금융 거래를 수행하는 API나 코드를 만들지 않는다.
- 되돌리기 어려운 요청은 `confirm` 단계에서 사용자가 명시적으로 확인해야 한다.
- 음성으로 안내한 핵심 내용은 화면에도 표시한다.

## 먼저 읽을 문서와 우선순위

작업을 시작하기 전에 관련 문서를 읽는다. 충돌이 있으면 아래 순서로 따른다.

1. 사용자의 현재 요청
2. `docs/contracts/`의 API, 상태 머신, 정책, 예시
3. `docs/03-demo-scenario.md`
4. `docs/07-handoff.md`
5. 이 문서와 `docs/prompts/`의 담당자별 지침
6. 기존 구현

`docs/contracts/`는 서비스 간 단일 진실 공급원이다. 계약과 구현이 다르면 임의로 계약을 바꾸지 말고 차이를 보고한다. 계약 변경은 팀 합의 후 별도 변경으로 진행한다.

## 현재 기본 담당: 이성우 — 프론트 어르신 모드

별도 지시가 없으면 이 저장소에서 에이전트의 주 작업 범위는 다음과 같다.

- `frontend/src/views/senior/`
- `frontend/src/composables/`
- `frontend/src/components/Mic*`
- `frontend/src/components/Tone*`
- `frontend/src/components/SpeechBubble.vue`
- `frontend/src/components/BigButton.vue`
- `frontend/src/components/SeniorShell.vue`
- `frontend/src/stores/session.js`

다음 파일과 영역은 다른 담당자의 소유이므로 읽고 연동할 수는 있지만, 사용자가 명시적으로 요청하지 않는 한 수정하지 않는다.

- `frontend/src/views/mock/`
- `frontend/src/views/staff/`
- `frontend/src/components/DevPanel.vue`
- `frontend/src/api/mock.js`
- `backend/`, `ai-server/`, `infra/`, `tools/measure/`
- `docs/contracts/`

담당 밖의 수정이 필요하면 먼저 원인, 필요한 변경, 영향을 설명한다. 단순히 빌드를 통과시키기 위해 계약이나 다른 담당자의 코드를 우회하지 않는다. 기존 사용자 변경사항과 무관한 파일은 되돌리거나 정리하지 않는다.

## 이성우 작업 순서

새 기능을 넓히기보다 이미 작성된 화면과 음성 흐름을 아래 순서로 검증하고 고친다.

1. `npm run build`를 실행하고 실패 원인을 담당 범위 안에서 수정한다.
2. `frontend/.env.local`에 `VITE_USE_MOCK=true`를 설정한 목 모드에서 `/mock/home` → 브리핑 → 대화 흐름을 확인한다. `.env.local`은 커밋하지 않는다.
3. 실제 브라우저에서 녹음과 VAD를 확인한다. 기본 침묵 대기는 2000ms, 비교 모드는 700ms이며 최소 800ms, 최대 15초 제한도 확인한다.
4. AI 서버가 준비되면 `VITE_USE_MOCK=false`로 STT → 턴 → TTS 왕복과 `ui.listen` 자동 마이크를 확인한다.
5. `tone=confirm`일 때 화면과 말투가 명확히 바뀌고, 선택지는 큰 `[맞아요]`, `[아니에요]` 버튼으로 제한되는지 확인한다. `friendly`로 돌아오면 원래 표현으로 복귀해야 한다.
6. 요약서 화면의 세 구획과 6자리 코드를 확인하고, 상태를 3초마다 조회해 `DONE`일 때 완료 안내를 한 번만 재생하는지 확인한다.
7. 접근성을 점검한다. 본문 글자는 22px 이상, 주요 버튼 높이는 72px 이상, 한 화면의 선택 버튼은 최대 3개, `[그만]`은 항상 보여야 한다. 상태는 색만이 아니라 글로도 전달한다.
8. 개발자 패널의 녹음 클립 입력으로 `/ai/stt` 대체 시연 경로를 검증한다. 패널 자체 수정이 필요하면 담당자에게 변경을 요청한다.

침묵 시간 2000ms/700ms 전환과 VAD 임계값은 기존 `DevPanel.vue`와 `session.silenceOverride`를 사용한다. 사용자가 별도로 요청하지 않으면 이 기능을 중복 구현하지 않는다.

## 구현 규칙

### 프론트엔드

- Vue 3 Composition API와 현재 Pinia 구조를 유지한다.
- 기존 순수 CSS를 사용한다. 새 UI 프레임워크나 상태 관리 라이브러리를 추가하지 않는다.
- 서버 응답 필드는 계약대로 `snake_case`를 유지한다.
- 세션 데이터는 `stores/session.js`, 녹음·재생·대화 조합은 `composables/`에 둔다. 뷰에서 API 흐름을 중복 구현하지 않는다.
- `tone`, `state`, `ui.buttons`, `ui.choices`, `ui.listen`, `actions`를 임의로 추론하지 말고 서버 응답과 상태 머신에 따라 렌더링한다.
- 음성 실패, 권한 거부, 소음 상황에서도 같은 일을 할 수 있는 버튼 경로를 유지한다.
- 시연 대본에 없는 기능을 추가하지 않는다.

### 안전과 계약

- `ADD_REQUEST`는 `CONFIRM` 상태에서 사용자의 `YES` 직후에만 허용한다.
- `confirmed_by_user` 검증을 제거하거나 우회하지 않는다.
- 계좌번호와 민감 정보는 화면, 로그, 오류 메시지에서도 마스킹한다.
- 규칙 기반 판정을 LLM 추측으로 대체하지 않는다.
- 테스트를 위해 기존 시드 데이터를 삭제하지 않는다. 새 테스트 데이터가 필요하면 ID 9000 이상을 쓴다.

## 실행과 검증

저장소 루트 기준으로 필요한 명령만 실행한다.

```bash
# 프론트 의존성 설치 및 빌드
cd frontend
npm install
npm run build

# 프론트 개발 서버
npm run dev

# 백엔드 정적 빌드
cd ../backend
./gradlew build

# AI 서버 테스트
cd ../ai-server
pytest -q

# 전체 서비스
cd ..
docker compose -f infra/docker-compose.yml --profile full up --build
```

- 프론트 변경 후 최소 검증은 `npm run build`다.
- 화면, 마이크, 오디오, 폴링처럼 빌드만으로 확인할 수 없는 변경은 브라우저에서 실제 흐름을 검증한다.
- 목 모드 확인만으로 실제 연동이 완료됐다고 판단하지 않는다.
- 백엔드 또는 AI 서버가 없어 통합 검증을 못 했다면, 통과한 검증과 못 한 검증을 구분해 보고한다.
- 완료 보고에는 변경 파일, 실행한 명령, 결과, 남은 수동 검증을 짧게 적는다. 실행하지 않은 검증을 성공했다고 표현하지 않는다.

## 환경 변수와 비밀정보

- 루트 설정은 `.env.example`, 프론트 설정은 `frontend/.env.example`을 기준으로 한다.
- 실제 키가 든 `.env`, `.env.local`, 오디오 캐시, 녹음 파일을 커밋하지 않는다.
- API 키나 개인정보를 코드, 예시, 로그, 스크린샷에 넣지 않는다.
- 로컬 MySQL 포트는 충돌할 수 있으므로 `MYSQL_PORT` 값을 확인한다.

## 변경 방식

- 작업 전 `git status --short`로 기존 변경을 확인한다.
- 한 번에 한 목적의 작은 변경을 만든다.
- 새 의존성, 계약 변경, 담당 범위 밖 수정은 필요한 이유를 먼저 설명한다.
- 사용자가 요청하지 않으면 커밋, 푸시, 대규모 리팩터링을 하지 않는다.
- 생성물과 캐시는 Git에 추가하지 않는다.
