# 거래 확인 가능 여부 분류 규칙 (백엔드 규칙 엔진, 담당 안상우)

`GET /api/transactions/{id}/classification` 의 판정 규칙. **위에서 아래로 첫 매치.** 같은 입력이면 같은 출력이 나와야 하고, 응답에 `rule_id` 를 실어 어떤 규칙이 적용됐는지 남긴다.

| rule_id | 조건 | level | facts (앱이 아는 것) | unknowns (앱이 모르는 것) | counter_hint |
|---|---|---|---|---|---|
| `R1_REGISTERED_PERSON` | `transactions.counterparty_id` 가 있고 `kind=PERSON` | **CONFIRMED** | "등록된 {relation} {name} 님 계좌에서 온 돈" (IN) / "…으로 보낸 돈" (OUT), 금액, 시각, 은행명 | (없음) | null |
| `R2_REGISTERED_INSTITUTION` | `counterparty_id` 가 있고 `kind=INSTITUTION` | **PARTIAL** | "{name}({category})", 금액, 시각, 채널(자동이체) | "정확한 청구 내역(기간·사용량)" | "{name} {category} 청구 내역이 어떻게 되는지" |
| `R3_MEMO_PATTERN` | `counterparty_id` 없지만 `memo` 또는 `counterparty_name` 이 어떤 counterparty 의 `memo_pattern` 정규식과 매치 | **PARTIAL** | R2 와 동일 (매치된 counterparty 로) | R2 와 동일 | R2 와 동일 |
| `R4_FEE` | `channel = '수수료'` 또는 이름/적요에 `수수료` 포함 | **UNKNOWN** | "수수료로 표시된 출금", 금액, 시각 | "어떤 거래에 붙은 수수료인지" | "{시각} 수수료 {금액}원이 어떤 거래의 수수료인지" |
| `R5_UNKNOWN` | 그 외 전부 | **UNKNOWN** | "통장에 '{counterparty_name}'이라고 적힘", 금액, 시각, 채널 | "무엇에 대한 돈인지", "누가 청구했는지" | "'{counterparty_name}' {금액}원 {시각} 출금(입금)이 무엇인지" |

## spoken_name (음성용 생활어 상대명)

| kind / level | spoken_name | 예 |
|---|---|---|
| PERSON | `{relation 존칭} {name} 님` | 아드님 김철수 님 / 따님 김영희 님 / 손자 박민수 |
| INSTITUTION | `{name 축약}` | 한국전력 / 국민연금 |
| UNKNOWN | `'{counterparty_name}'이라는 곳` | '대한정보통신'이라는 곳 |

relation 존칭표: 아들→아드님, 딸→따님, 손자→손자, 손녀→손녀, 배우자→배우자, 그 외 그대로.
기관 축약표: 한국전력공사→한국전력, 국민연금공단→국민연금, 국민건강보험공단→건강보험, 그 외 그대로.

## 시드 데이터 기준 기대 결과

| transaction_id | 상대 | 규칙 | level |
|---|---|---|---|
| 101 | 김철수(아들) | R1 | CONFIRMED |
| 102 | 한국전력공사 | R2 | PARTIAL |
| 103 | 대한정보통신 | R5 | UNKNOWN |
| 104 | 국민연금공단 | R2 | PARTIAL |
| 105 | 수수료 | R4 | UNKNOWN |
| 106 | 김영희(딸) | R1 | CONFIRMED |

## 원칙

- 규칙 엔진은 **DB 값과 정규식만** 본다. LLM 호출 없음, 외부 호출 없음.
- `facts` 는 문장 조각이 아니라 완결된 짧은 문장으로 넣는다. AI 서버가 그대로 읽거나 LLM 에 그대로 넘긴다.
- 새 규칙은 표에 행을 추가하고 `rule_id` 를 부여한다. 코드에서 규칙 순서는 표와 같아야 한다.
- 브리핑 선별(무엇을 읽을지)은 이 규칙과 무관하다. 선별은 `heard_at IS NULL` + 뮤트 제외 + 최근순 3건뿐이다.
