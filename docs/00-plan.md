# 또박또박 — 본선 2박3일 실행 계획

## 0. 상황
- 본선 현장, 2박3일, 코드 0에서 시작. 팀 "유종의 미" 5명, 전원 Claude Code 로 코딩.
- 기획서: 어르신이 입출금 알림을 눌러 들어오면 AI 가 음성으로 읽어주고, 대화로 질문을 받고, 앱이 못 푸는 건 창구 요약서로 넘기는 서비스.
- 심사기준(100): 기대효과 **30** / 창의성 20 / 구현 가능성 20 / 발표력 20 / 적합성 10 → 상세 `01-judging-strategy.md`
- 트랙(예년 기준): '세상을 바꾸는 소프트웨어' — ① MZ 금융비서 ② **디지털 금융약자 지원** ③ 소상공인 지원.

이 계획의 목적 세 가지: **점수가 나는 곳에 시간을 쓴다** · **첫 3시간 안에 계약을 고정해 5명이 병렬로 간다** · **발표 3분 시연이 무조건 돌아간다**.

## 1. 시간 배분
개발 60% / 시연 안정화·측정 20% / 발표 자료·리허설 20%. 기대효과 30점은 코드가 아니라 문서·발표에서 나오므로 **Day 3 오전을 통째로** 비운다. 시간표는 `05-timeline.md`.

## 2. 북극성 = 시연 대본
`03-demo-scenario.md` 의 12단계. 여기 없는 기능은 만들지 않는다. 각 단계는 기획서 구현 목표 ①②③④ 에 대응한다.

## 3. 기술 결정

| 항목 | 결정 | 이유 |
|---|---|---|
| 프론트 | Vue 3 + Vite, 모바일 웹. `/mock/*` 진입 목업, `/senior/*` 어르신 모드, `/staff/*` 직원 | 기획서 유지, 배포 1개 |
| 백엔드 | Spring Boot 3 + Java 17 + MyBatis + MySQL 8(docker) | Legacy XML 제거로 AI 코딩 속도↑, 기획서의 MyBatis/MySQL 유지 |
| AI 서버 | Python + FastAPI | 기획서 유지 |
| STT | OpenAI `gpt-4o-transcribe` (`prompt` 로 어휘 힌트) | 키 1개, 한국어 양호 |
| TTS | OpenAI `gpt-4o-mini-tts` (`instructions` 로 친근/확인 톤, `speed`) | 기획서 "말투 전환"을 그대로 구현 |
| LLM | 기본 OpenAI(같은 키). `LLM_PROVIDER=anthropic` 이면 Claude 로 교체 가능한 어댑터 | 운영 단순성, 벤더 비종속 |
| 발화 종료 판정 | 브라우저 에너지 VAD: 일반 700ms vs 어르신 2000ms | 재현 가능, A/B 측정 쉬움 |
| 후보 대조 | 자모 분해 + 편집거리 유사도, 동점 시 LLM 선택, 금액은 수사 파서 | 기획서 ① 그대로 |
| 세션 | AI 서버 메모리 | 데모 |
| 인프라 | docker-compose(mysql + 3서비스), 노트북 1대에서 전체 구동 | 현장 네트워크 대비 |
| 저장소 | 모노레포 `github.com/Sangwoo421/ttobak` | 계약 파일 한 곳 |

## 4. 아키텍처

```
[Vue 모바일웹] ──(오디오/버튼)──> [FastAPI AI 서버] ──(REST)──> [Spring Boot 백엔드] ── MySQL
      │                               │  STT/TTS/LLM 외부 API
      └──(요약서 조회·직원 화면)──────────────────────────────> [Spring Boot 백엔드]
```

**책임 분리**: 백엔드 = 데이터·판정(규칙 엔진)·요약서. AI 서버 = 음성·대화·말투. 프론트 = 화면·녹음·재생.
**LLM 은 설명 문장만 만들고, 판정과 분류는 백엔드 규칙 엔진이 한다.** 돈이 움직이는 API 는 존재하지 않는다.

계약(단일 진실) — `docs/contracts/`
- `openapi-backend.yaml`, `openapi-ai.yaml` — REST
- `dialog-state-machine.md` — 상태·의도·신뢰도 정책(≥0.8 채택 / 0.6~0.8 되묻기 / 동점 LLM / <0.6 버튼)
- `classification-rules.md` — R1~R5 (CONFIRMED / PARTIAL / UNKNOWN)
- `senior-mode-policy.md` — 템플릿·생활어 치환·톤
- `seed-data.sql`, `examples/*.json` — 시연 데이터와 기대 응답(목으로도 사용)

## 5. 역할 (상세 `04-roles-and-tasks.md`)

| 사람 | 담당 |
|---|---|
| 고현준 | AI 서버·통합 리드. 음성 레이어, 상태 머신, 응답 정책, 요약서 문장, 계약 관리 |
| 안상우 | 백엔드 A. DB·시드, 브리핑 선별, 분류 규칙 엔진, 알림·뮤트 |
| 강두형 | 백엔드 B. 요약서·직원 API, Provider 추상화, Docker·CI, 시연 환경·영상 |
| 이성우 | 프론트 A. 어르신 모드 화면, 녹음·VAD, TTS 재생, 확인 톤, 접근성, 시연자 |
| 조태석 | 프론트 B. 진입 목업, 직원 화면, 측정 도구, 대본·PPT, 발표자 |

## 6. AI 코딩 운영
- 각자 서비스 폴더에서 Claude Code. 계약 파일 경로와 규칙은 로컬 `CLAUDE.md`(저장소 미포함) 또는 `04-roles-and-tasks.md` 의 프롬프트 템플릿.
- 목 우선: 백엔드가 늦으면 AI 서버는 `BACKEND_MODE=mock`, AI 서버가 늦으면 프론트는 `VITE_USE_MOCK=true`.
- 브랜치 `feat/<이름>/<작업>` → PR → main. 체크포인트마다 main 에서 compose 전체 구동.
- 완료 = 실행해서 확인한 결과를 보고한 것.

## 7. 리스크

| 리스크 | 대응 |
|---|---|
| 현장 소음 STT 실패 | 헤드셋, 녹음 클립 입력 모드, 버튼 경로 자체가 시연 포인트 |
| API 한도·장애 | 키 2개, 시연 대사 TTS 캐시, LLM 실패 시 템플릿 폴백(코드에 내장) |
| 네트워크 | 전체 로컬 compose, 핫스팟, 시연 영상 |
| 통합 지연 | 계약 선고정 + 목 + 체크포인트 3회 |
| 범위 폭발 | Day 2 22:00 기능 동결 |
| 수면 | Day 1 5시간, Day 2 자정 이후 발표자 취침 |

## 8. 발표
`06-presentation.md`. 10장, 시연 2분 30초, 마지막 2장은 기대효과·로드맵. Q&A 15문답.

## 9. 측정
`tools/measure/`. 자체 테스트셋 20~30건, baseline(힌트 없음·700ms 절단·문자열 매칭) vs layered. 지표: 의도 도달률·평균 시도 횟수·오실행.

## 10. 저장소 구성
```
backend/     Spring Boot (안상우·강두형)      ai-server/  FastAPI (고현준)
frontend/    Vue 3 (이성우·조태석)            tools/measure/  측정 (조태석)
infra/       docker-compose (강두형)          docs/       계획·계약·발표 (전원)
```
