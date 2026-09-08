# 대화 상태 머신 (AI 서버, 담당 고현준)

세션은 AI 서버 메모리에 산다. 상태는 아래 중 하나이고, 모든 전이는 이 문서를 따른다.
LLM 은 **설명 문장 생성**과 **동점 후보 선택**, **규칙이 못 잡은 의도 분류**에만 쓴다. 전이 결정은 코드가 한다.

## 상태

| 상태 | 뜻 | 화면 버튼(기본) |
|---|---|---|
| `BRIEFING` | 브리핑 음성 재생 중 | (없음, 재생 끝나면 LISTENING) |
| `LISTENING` | 사용자 발화/버튼 대기 | ASK_MORE(더 물어보기) · GO_COUNTER(창구 갈 일 정리) · STOP(그만) |
| `EXPLAIN` | 거래 설명 응답 직후 (자동으로 LISTENING 복귀) | REPEAT · GO_COUNTER · STOP |
| `OFFER_ADD_QUESTION` | "창구 목록에 적어둘까요?" 예/아니오 대기 | YES(네, 적어주세요) · NO(아니요) |
| `SLOT_RECIPIENT` | 받는 사람 확인/되묻기 | (후보 최대 3개 choices) · NO |
| `SLOT_AMOUNT` | 금액 되묻기 | NO |
| `CONFIRM` | **확인 톤**. "받는 사람 X, 금액 Y. 맞습니까?" | YES(맞아요) · NO(아니에요) |
| `CLARIFY` | 못 알아들음 → 후보 3개 버튼 | choices 3개 · REPEAT |
| `SUMMARY` | 요약서 생성·안내 완료 | OPEN_SUMMARY 액션 → 프론트가 요약서 화면으로 |
| `DONE` | 직원 처리 대기/완료 | (요약서 화면에서 status 폴링) |
| `END` | 종료 | |

## 의도 (intent)

| intent | 예시 발화 | 1차 키워드 규칙 (정규식, 순서대로 검사) |
|---|---|---|
| `REPEAT` | 다시 들려줘, 못 들었어, 한 번 더 | `다시|한 ?번 ?더|못 ?들` |
| `STOP` | 그만, 됐어, 끝 | `그만|됐어|끝|종료` |
| `GO_COUNTER` | 창구 갈래, 은행 가서 할게, 정리해줘 | `창구|은행 ?가|정리` |
| `REQUEST_TRANSFER` | 아들한테 보내야 해, 이체, 부쳐줘, 송금 | `보내|부쳐|이체|송금|넣어` |
| `ASK_WHO` | 누가 보낸 거야 | `누가|누구` |
| `ASK_AMOUNT` | 얼마야, 얼마 나갔어 | `얼마` |
| `ASK_ABOUT_TX` | 첫 번째 거 뭐야, 그 정보통신 뭐야, 이거 뭐야 | `뭐야|뭐지|무슨|뭔|어디` 또는 서수(`첫|두|세|1|2|3`)/거래명 매칭 |
| `MUTE_ITEM` | 이건 매번 안 들어도 돼 | `안 ?들어도|끄|빼줘` |
| `YES` | 응, 맞아, 그래, 네 | `^(응|어|네|예|맞|그래|좋아|해줘)` |
| `NO` | 아니, 아니야, 틀려 | `^(아니|아냐|틀|안 ?해)` |
| `UNKNOWN` | (위에 없음) | → LLM 구조화 분류 → 확신 < `INTENT_MIN_CONF` 이면 CLARIFY |

규칙은 위에서 아래로 첫 매치. `YES/NO` 는 `OFFER_ADD_QUESTION`, `CONFIRM`, `SLOT_*` 상태에서만 의도로 인정한다(LISTENING 에서 "응"은 UNKNOWN).

## 개체(entity) 해결

후보 목록(세션에 저장)은 세 종류:
- `TX:{id}` 브리핑한 거래 (표면형: "첫 번째/둘째/1번…", spoken_name, counterparty_name, 금액 표현)
- `CP:{id}` 등록 수취인 (표면형: name, aliases, relation)
- `INTENT:{name}` 의도 자체 (CLARIFY 선택지용 라벨)

점수 = 자모 분해 후 정규화 편집거리 유사도(0~1). 발화 전체가 아니라 **발화의 n-gram 창(2~6음절)** 과 각 표면형을 비교해 최대값을 쓴다.

| 최고 점수 s | 상위 1·2위 차 | 결정 | decision |
|---|---|---|---|
| ≥ 0.80 | ≥ 0.10 | 채택 | `ACCEPT` |
| ≥ 0.80 | < 0.10 | 후보 2~3개를 LLM 에 넘겨 선택 (facts 만 제공) | `LLM_TIEBREAK` |
| 0.60 ~ 0.80 | — | 되묻기: "{후보} 말씀이세요?" (YES/NO) | `ASK_AGAIN` |
| < 0.60 | — | CLARIFY 로 전이, 상위 3개 버튼 | `BUTTON` |

금액은 `amount_parser`(한국어 수사 → 정수)로 규칙 파싱. 못 찾으면 `SLOT_AMOUNT` 되묻기.

## 전이

```
BRIEFING ──(재생 끝)──> LISTENING

LISTENING ── ASK_ABOUT_TX / ASK_WHO / ASK_AMOUNT ──> EXPLAIN
    EXPLAIN: 백엔드 classification(facts) → 템플릿 + (자유 질문이면 LLM 설명, facts 밖 정보 금지)
    level=UNKNOWN 이면 ──> OFFER_ADD_QUESTION
    그 외 ──> LISTENING

OFFER_ADD_QUESTION ── YES ──> actions:[ADD_QUESTION] ──> LISTENING ("적어뒀어요. 더 물어보실 것 있으세요?")
                   ── NO  ──> LISTENING

LISTENING ── REQUEST_TRANSFER ──>
    수취인 후보 해결:
      ACCEPT       ──> 금액 있음? CONFIRM : SLOT_AMOUNT
      ASK_AGAIN    ──> SLOT_RECIPIENT ("아드님 김철수 님 말씀이세요?")
      BUTTON       ──> SLOT_RECIPIENT (choices = 등록 수취인 상위 3)
SLOT_RECIPIENT ── YES / choice ──> 금액 있음? CONFIRM : SLOT_AMOUNT
               ── NO ──> (2회째면 choices 버튼) SLOT_RECIPIENT
SLOT_AMOUNT ── 금액 파싱 성공 ──> CONFIRM
            ── 실패 2회 ──> "금액은 창구에서 말씀하셔도 돼요" ──> CONFIRM(amount=null)
CONFIRM(tone=confirm) ── YES ──> actions:[ADD_REQUEST(confirmed_by_user=true)] ──> LISTENING
                               ("이체는 창구에서 직원이 도와드려요. 요약서에 적어둘게요.")
                      ── NO  ──> SLOT_RECIPIENT (처음부터)

LISTENING ── GO_COUNTER ──> SUMMARY (POST /ai/session/{id}/summary 와 동일 처리) ──> actions:[OPEN_SUMMARY] ──> DONE
LISTENING ── REPEAT ──> 마지막 assistant_text 재생 ──> 이전 상태 유지
LISTENING ── MUTE_ITEM ──> 대상 TX 해결 → actions:[MUTE] ──> LISTENING
LISTENING ── STOP ──> END ("네, 다음에 또 불러 주세요.")
LISTENING ── UNKNOWN(저확신) ──> CLARIFY (choices: 최근 거래 3건 or 의도 3개) ──> choice ──> 해당 전이
```

**절대 규칙**
1. `ADD_REQUEST` 는 `CONFIRM` 에서 `YES` 를 받은 직후에만 생성된다. 다른 경로 없음.
2. 어떤 상태에서도 돈이 움직이는 API 는 호출하지 않는다. 백엔드에도 그런 API 가 없다.
3. `EXPLAIN` 에서 LLM 응답에 facts 에 없는 숫자·고유명사가 있으면 템플릿 문장으로 대체한다(P1).
4. 응답은 한 번에 한 가지만 묻는다. 두 가지를 물어야 하면 두 턴으로 나눈다.

## 시연 시나리오 턴 예시

| 턴 | 입력 | intent / entity | 결정 | 상태 |
|---|---|---|---|---|
| 1 | "첫 번째 거 그게 뭐야" | ASK_ABOUT_TX / TX:101 (s=0.92 "첫 번째") | ACCEPT | EXPLAIN → LISTENING |
| 2 | "세 번째 그 정보통신인가 그건 뭐야" | ASK_ABOUT_TX / TX:103 (s=0.88) | ACCEPT, level=UNKNOWN | OFFER_ADD_QUESTION |
| 3 | YES 버튼 | YES | ADD_QUESTION | LISTENING |
| 4 | "아들이 뭐 보내라는데 이십만 원인가" | REQUEST_TRANSFER / CP:1 (s=0.95 "아들"), amount=200000 | ACCEPT | CONFIRM(confirm 톤) |
| 5 | "맞아" | YES | ADD_REQUEST | LISTENING |
| 6 | (웅얼) "으음 그 저기" | UNKNOWN (LLM conf 0.3) | BUTTON | CLARIFY |
| 7 | choice INTENT:GO_COUNTER | GO_COUNTER | — | SUMMARY → DONE |
