-- 또박또박 시연용 스키마 + 시드 데이터
-- docker-compose 의 mysql 컨테이너가 최초 기동 시 자동 실행한다.
-- 시연 시나리오(docs/03-demo-scenario.md)와 1:1로 맞춰져 있으므로 값을 바꾸면 대본도 바꿀 것.

-- 이 줄을 지우지 말 것. 컨테이너 로케일에 따라 mysql 클라이언트가 이 파일을 latin1(CP1252)로
-- 읽어 한글이 이중 인코딩되어 저장된다. (김철수 -> ê¹€ì² ìˆ˜)
SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS ttobak CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ttobak;

DROP TABLE IF EXISTS dialog_logs;
DROP TABLE IF EXISTS summary_items;
DROP TABLE IF EXISTS counter_summaries;
DROP TABLE IF EXISTS mute_rules;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS counterparties;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  name          VARCHAR(50)  NOT NULL,
  birth_year    INT          NULL,
  senior_mode   TINYINT(1)   NOT NULL DEFAULT 0,
  home_branch   VARCHAR(100) NULL,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounts (
  id             BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id        BIGINT       NOT NULL,
  alias          VARCHAR(50)  NOT NULL,          -- "주거래 통장"
  bank_name      VARCHAR(50)  NOT NULL,
  number_masked  VARCHAR(30)  NOT NULL,          -- 화면·요약서에는 마스킹된 값만
  balance        BIGINT       NOT NULL DEFAULT 0,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 등록 수취인 / 자주 거래하는 상대. STT 어휘 힌트와 후보 대조의 원천.
CREATE TABLE counterparties (
  id              BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id         BIGINT       NOT NULL,
  name            VARCHAR(100) NOT NULL,
  relation        VARCHAR(30)  NULL,             -- 아들, 딸, 손자, 자동이체, 정기입금
  kind            VARCHAR(20)  NOT NULL,         -- PERSON | INSTITUTION
  bank_name       VARCHAR(50)  NULL,
  account_number  VARCHAR(40)  NULL,             -- 창구 요약서 생성용(마스킹해서 노출)
  aliases         VARCHAR(255) NULL,             -- 쉼표 구분. "아들,철수,큰아들"
  memo_pattern    VARCHAR(100) NULL,             -- 적요 매칭용 정규식. "한전|한국전력"
  category        VARCHAR(50)  NULL,             -- 전기요금, 연금
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE transactions (
  id                 BIGINT PRIMARY KEY AUTO_INCREMENT,
  account_id         BIGINT       NOT NULL,
  type               VARCHAR(3)   NOT NULL,      -- IN | OUT
  amount             BIGINT       NOT NULL,
  counterparty_name  VARCHAR(100) NOT NULL,      -- 통장에 찍히는 상대명
  memo               VARCHAR(100) NULL,          -- 적요
  channel            VARCHAR(30)  NULL,          -- 이체, 자동이체, 카드, 수수료
  occurred_at        DATETIME     NOT NULL,
  counterparty_id    BIGINT       NULL,          -- 매칭된 등록 상대(없으면 NULL)
  FOREIGN KEY (account_id) REFERENCES accounts(id),
  FOREIGN KEY (counterparty_id) REFERENCES counterparties(id)
);

CREATE TABLE notifications (
  id              BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id         BIGINT   NOT NULL,
  transaction_id  BIGINT   NOT NULL,
  sent_at         DATETIME NOT NULL,
  read_at         DATETIME NULL,
  heard_at        DATETIME NULL,                 -- 음성 브리핑으로 들은 시각. NULL이면 미청취
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (transaction_id) REFERENCES transactions(id)
);

-- "이건 매번 안 들어도 돼요" 사용자가 직접 끈 항목. 시스템이 판정하지 않는다.
CREATE TABLE mute_rules (
  id                 BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id            BIGINT       NOT NULL,
  counterparty_name  VARCHAR(100) NOT NULL,
  created_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE counter_summaries (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id      BIGINT       NOT NULL,
  code         CHAR(6)      NOT NULL UNIQUE,     -- 창구에서 보여주는 6자리
  ticket_no    INT          NOT NULL,            -- 번호표(목업)
  branch_name  VARCHAR(100) NOT NULL,
  status       VARCHAR(20)  NOT NULL DEFAULT 'OPEN',   -- OPEN | IN_PROGRESS | DONE
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE summary_items (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  summary_id   BIGINT      NOT NULL,
  section      VARCHAR(10) NOT NULL,             -- REQUEST | QUESTION | PREP
  ordinal      INT         NOT NULL DEFAULT 0,
  payload      JSON        NOT NULL,             -- 섹션별 구조는 openapi-backend.yaml 참조
  handled      TINYINT(1)  NOT NULL DEFAULT 0,
  handled_at   DATETIME    NULL,
  FOREIGN KEY (summary_id) REFERENCES counter_summaries(id)
);

-- 사후 검증용 대화 로그 (P1). 같은 입력 → 같은 판정을 증명하는 근거.
CREATE TABLE dialog_logs (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  session_id   VARCHAR(64)  NOT NULL,
  user_id      BIGINT       NOT NULL,
  turn_no      INT          NOT NULL,
  user_text    VARCHAR(500) NULL,
  intent       VARCHAR(40)  NULL,
  confidence   DECIMAL(4,3) NULL,
  matched      VARCHAR(100) NULL,
  decision     VARCHAR(40)  NULL,                -- ACCEPT | ASK_AGAIN | BUTTON | LLM_TIEBREAK
  state        VARCHAR(40)  NULL,
  created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------- 시드
INSERT INTO users (id, name, birth_year, senior_mode, home_branch) VALUES
  (1, '김영자', 1951, 1, 'KB국민은행 종로지점'),
  (2, '박지훈', 1990, 0, 'KB국민은행 여의도지점');   -- 비교용 일반 사용자(시연 미사용)

INSERT INTO accounts (id, user_id, alias, bank_name, number_masked, balance) VALUES
  (1, 1, '주거래 통장', 'KB국민은행', '123456-02-****78', 1532400),
  (2, 2, '월급 통장',   'KB국민은행', '654321-01-****12', 2210000);

INSERT INTO counterparties (id, user_id, name, relation, kind, bank_name, account_number, aliases, memo_pattern, category) VALUES
  (1, 1, '김철수',       '아들',     'PERSON',      'KB국민은행', '9876-54-321098',  '아들,철수,큰아들,우리 아들', NULL,             NULL),
  (2, 1, '김영희',       '딸',       'PERSON',      '신한은행',   '110-123-456789',  '딸,영희,우리 딸',           NULL,             NULL),
  (3, 1, '박민수',       '손자',     'PERSON',      '카카오뱅크', '3333-01-1234567', '손자,민수',                 NULL,             NULL),
  (4, 1, '한국전력공사', '자동이체', 'INSTITUTION', NULL,         NULL,              '한전,전기세,전기요금',       '한전|한국전력',   '전기요금'),
  (5, 1, '국민연금공단', '정기입금', 'INSTITUTION', NULL,         NULL,              '연금,국민연금',              '국민연금',        '연금');

-- 거래: 최근순. 101~103 이 시연에서 읽어주는 3건.
-- 시각은 "며칠 전 + 고정 시:분" 으로 박는다. NOW() 기준 상대 시간(-5시간 등)을 쓰면 리셋한
-- 시각에 따라 "오늘 아침"이 "오늘 오후"로 바뀌어 시연 대본·PPT 와 어긋난다.
-- 버킷: 새벽(~06) / 아침(06-12) / 오후(12-18) / 저녁(18~) — relative_time.py 와 같아야 한다.
INSERT INTO transactions (id, account_id, type, amount, counterparty_name, memo, channel, occurred_at, counterparty_id) VALUES
  (101, 1, 'IN',  300000, '김철수',        '김철수',          '이체',      DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 1 DAY), INTERVAL '15:12' HOUR_MINUTE), 1),  -- 어제 오후
  (102, 1, 'OUT',  42000, '한국전력공사',  '한전 전기요금',   '자동이체',  DATE_ADD(CURDATE(), INTERVAL '08:30' HOUR_MINUTE), 4),                            -- 오늘 아침
  (103, 1, 'OUT',  19000, '대한정보통신',  '대한정보통신',    '자동이체',  DATE_ADD(CURDATE(), INTERVAL '09:10' HOUR_MINUTE), NULL),                         -- 오늘 아침
  (104, 1, 'IN',  620000, '국민연금공단',  '국민연금',        '이체',      DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 3 DAY), INTERVAL '10:00' HOUR_MINUTE), 5),
  (105, 1, 'OUT',   3500, '수수료',        '타행이체수수료',  '수수료',    DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 5 DAY), INTERVAL '14:00' HOUR_MINUTE), NULL),
  (106, 1, 'IN',   50000, '김영희',        '엄마 용돈',       '이체',      DATE_ADD(DATE_SUB(CURDATE(), INTERVAL 7 DAY), INTERVAL '11:20' HOUR_MINUTE), 2);

-- 알림: 101~103 미청취(heard_at NULL), 나머지는 이미 들음.
INSERT INTO notifications (id, user_id, transaction_id, sent_at, read_at, heard_at) VALUES
  (1001, 1, 101, (SELECT occurred_at FROM transactions WHERE id = 101), NULL, NULL),
  (1002, 1, 102, (SELECT occurred_at FROM transactions WHERE id = 102), NULL, NULL),
  (1003, 1, 103, (SELECT occurred_at FROM transactions WHERE id = 103), NULL, NULL),
  (1004, 1, 104, DATE_SUB(NOW(), INTERVAL 3 DAY),  DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)),
  (1005, 1, 105, DATE_SUB(NOW(), INTERVAL 5 DAY),  DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY)),
  (1006, 1, 106, DATE_SUB(NOW(), INTERVAL 7 DAY),  DATE_SUB(NOW(), INTERVAL 7 DAY), DATE_SUB(NOW(), INTERVAL 7 DAY));

-- 직원 화면 시연용: 이미 처리된 과거 요약서 1건
INSERT INTO counter_summaries (id, user_id, code, ticket_no, branch_name, status, created_at) VALUES
  (1, 1, '118204', 7, 'KB국민은행 종로지점', 'DONE', DATE_SUB(NOW(), INTERVAL 10 DAY));
INSERT INTO summary_items (summary_id, section, ordinal, payload, handled, handled_at) VALUES
  (1, 'REQUEST',  1, JSON_OBJECT('type','TRANSFER','recipient_name','김영희','recipient_relation','딸','recipient_bank','신한은행','recipient_account_masked','110-123-****89','amount',100000,'note','생일 축하'), 1, DATE_SUB(NOW(), INTERVAL 10 DAY)),
  (1, 'QUESTION', 1, JSON_OBJECT('transaction_id',105,'text','타행이체수수료 3,500원이 왜 나갔는지'), 1, DATE_SUB(NOW(), INTERVAL 10 DAY)),
  (1, 'PREP',     1, JSON_OBJECT('item','신분증','required',true), 1, DATE_SUB(NOW(), INTERVAL 10 DAY));
