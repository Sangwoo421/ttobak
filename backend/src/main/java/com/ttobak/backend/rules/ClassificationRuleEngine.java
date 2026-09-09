package com.ttobak.backend.rules;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;
import java.util.regex.PatternSyntaxException;

import com.ttobak.backend.domain.Classification;
import com.ttobak.backend.domain.Counterparty;
import com.ttobak.backend.domain.Transaction;
import org.springframework.stereotype.Component;

/**
 * docs/contracts/classification-rules.md 의 규칙 엔진.
 * 위에서 아래로 첫 매치(R1 → R2 → R3 → R4 → R5). DB 값과 정규식만 본다. LLM·외부 호출 없음.
 * 같은 입력(거래, 상대 목록, 오늘 날짜) → 같은 출력.
 */
@Component
public class ClassificationRuleEngine {

    public static final String R1 = "R1_REGISTERED_PERSON";
    public static final String R2 = "R2_REGISTERED_INSTITUTION";
    public static final String R3 = "R3_MEMO_PATTERN";
    public static final String R4 = "R4_FEE";
    public static final String R5 = "R5_UNKNOWN";

    private static final ZoneId KST = ZoneId.of("Asia/Seoul");

    /** relation 존칭표 (그 외는 그대로) */
    private static final Map<String, String> HONORIFIC = Map.of(
            "아들", "아드님",
            "딸", "따님",
            "손자", "손자",
            "손녀", "손녀",
            "배우자", "배우자");

    /** 기관 축약표 (그 외는 그대로) */
    private static final Map<String, String> INSTITUTION_SHORT = Map.of(
            "한국전력공사", "한국전력",
            "국민연금공단", "국민연금",
            "국민건강보험공단", "건강보험");

    /**
     * @param tx           판정할 거래
     * @param registered   tx.counterparty_id 로 찾은 등록 상대 (없으면 null)
     * @param candidates   거래 계좌 소유자의 등록 상대 전체 (R3 memo_pattern 대조용)
     */
    public Classification classify(Transaction tx, Counterparty registered, List<Counterparty> candidates) {
        return classify(tx, registered, candidates, LocalDate.now(KST));
    }

    public Classification classify(Transaction tx, Counterparty registered, List<Counterparty> candidates, LocalDate today) {
        // R1: 등록된 사람
        if (registered != null && registered.isPerson()) {
            return registeredPerson(tx, registered, today);
        }
        // R2: 등록된 기관
        if (registered != null) {
            return institution(tx, registered, today, R2);
        }
        // R3: 적요/상대명이 memo_pattern 정규식과 매치
        Counterparty memoMatch = matchMemoPattern(tx, candidates);
        if (memoMatch != null) {
            return institution(tx, memoMatch, today, R3);
        }
        // R4: 수수료
        if (isFee(tx)) {
            return fee(tx, today);
        }
        // R5: 그 외 전부
        return unknown(tx, today);
    }

    // ---------------------------------------------------------------- rules

    private Classification registeredPerson(Transaction tx, Counterparty cp, LocalDate today) {
        boolean in = tx.isIn();
        String who = (cp.getRelation() == null ? "" : cp.getRelation() + " ") + cp.getName() + " 님";
        List<String> facts = new ArrayList<>();
        facts.add(in ? "등록된 " + who + " 계좌에서 온 돈입니다." : "등록된 " + who + " 계좌로 보낸 돈입니다.");
        facts.add(amountFact(tx));
        facts.add(whenFact(tx, today));
        if (cp.getBankName() != null) {
            facts.add(in ? "보낸 은행은 " + cp.getBankName() + "입니다." : "받는 은행은 " + cp.getBankName() + "입니다.");
        }
        String honorific = cp.getRelation() == null ? null : HONORIFIC.getOrDefault(cp.getRelation(), cp.getRelation());
        String spokenName = (honorific == null ? "" : honorific + " ") + cp.getName() + " 님";
        return new Classification(tx.getId(), "CONFIRMED", R1, spokenName, facts, List.of(), null, cp.toDto());
    }

    private Classification institution(Transaction tx, Counterparty cp, LocalDate today, String ruleId) {
        boolean in = tx.isIn();
        String label = cp.getCategory() == null ? cp.getName() : cp.getName() + "(" + cp.getCategory() + ")";
        List<String> facts = new ArrayList<>();
        facts.add(in ? label + "에서 들어온 돈입니다." : label + "로 나간 돈입니다.");
        facts.add(amountFact(tx));
        facts.add(whenFact(tx, today));
        if ("자동이체".equals(tx.getChannel())) {
            facts.add(in ? "매달 자동으로 들어오는 돈입니다." : "매달 자동으로 나가는 돈입니다.");
        } else if (tx.getChannel() != null) {
            facts.add(channelFact(tx));
        }
        String hintSubject = cp.getCategory() == null ? cp.getName() : cp.getName() + " " + cp.getCategory();
        String spokenName = INSTITUTION_SHORT.getOrDefault(cp.getName(), cp.getName());
        return new Classification(tx.getId(), "PARTIAL", ruleId, spokenName, facts,
                List.of("정확한 청구 내역(기간·사용량)"),
                hintSubject + " 청구 내역이 어떻게 되는지",
                cp.toDto());
    }

    private Classification fee(Transaction tx, LocalDate today) {
        List<String> facts = new ArrayList<>();
        facts.add("수수료로 표시된 출금입니다.");
        facts.add(amountFact(tx));
        facts.add(whenFact(tx, today));
        return new Classification(tx.getId(), "UNKNOWN", R4, "수수료", facts,
                List.of("어떤 거래에 붙은 수수료인지"),
                dayWord(tx.getOccurredAt(), today) + " 수수료 " + amount(tx) + "원이 어떤 거래의 수수료인지",
                null);
    }

    private Classification unknown(Transaction tx, LocalDate today) {
        boolean in = tx.isIn();
        String name = tx.getCounterpartyName();
        List<String> facts = new ArrayList<>();
        facts.add("통장에 '" + name + "'이라고 적혀 있습니다.");
        facts.add(amountFact(tx));
        facts.add(whenFact(tx, today));
        if (tx.getChannel() != null) {
            facts.add(channelFact(tx));
        }
        return new Classification(tx.getId(), "UNKNOWN", R5, "'" + name + "'이라는 곳", facts,
                List.of("무엇에 대한 돈인지", "누가 청구했는지"),
                "'" + name + "' " + amount(tx) + "원 " + dayWord(tx.getOccurredAt(), today) + (in ? " 입금이 무엇인지" : " 출금이 무엇인지"),
                null);
    }

    // ---------------------------------------------------------------- conditions

    private static Counterparty matchMemoPattern(Transaction tx, List<Counterparty> candidates) {
        if (candidates == null) {
            return null;
        }
        for (Counterparty cp : candidates) {
            if (cp.getMemoPattern() == null || cp.getMemoPattern().isBlank()) {
                continue;
            }
            try {
                Pattern p = Pattern.compile(cp.getMemoPattern());
                if ((tx.getMemo() != null && p.matcher(tx.getMemo()).find())
                        || (tx.getCounterpartyName() != null && p.matcher(tx.getCounterpartyName()).find())) {
                    return cp;
                }
            } catch (PatternSyntaxException ignored) {
                // 잘못된 정규식은 매치하지 않는 것으로 본다
            }
        }
        return null;
    }

    private static boolean isFee(Transaction tx) {
        return "수수료".equals(tx.getChannel())
                || (tx.getCounterpartyName() != null && tx.getCounterpartyName().contains("수수료"))
                || (tx.getMemo() != null && tx.getMemo().contains("수수료"));
    }

    // ---------------------------------------------------------------- sentence helpers

    private static String amount(Transaction tx) {
        return String.format("%,d", tx.getAmount());
    }

    private static String amountFact(Transaction tx) {
        return "금액은 " + amount(tx) + "원입니다.";
    }

    private static String whenFact(Transaction tx, LocalDate today) {
        String when = dayWord(tx.getOccurredAt(), today) + " " + partOfDay(tx.getOccurredAt());
        return when + (tx.isIn() ? "에 들어왔습니다." : "에 나갔습니다.");
    }

    private static String channelFact(Transaction tx) {
        return tx.getChannel() + (tx.isIn() ? "로 들어왔습니다." : "로 나갔습니다.");
    }

    /** 오늘 / 어제 / 그저께 / N일 전 */
    static String dayWord(LocalDateTime at, LocalDate today) {
        long days = ChronoUnit.DAYS.between(at.toLocalDate(), today);
        if (days <= 0) {
            return "오늘";
        }
        if (days == 1) {
            return "어제";
        }
        if (days == 2) {
            return "그저께";
        }
        return days + "일 전";
    }

    /**
     * 새벽(~06) / 아침(06-12) / 오후(12-18) / 저녁(18~).
     *
     * <p>경계는 AI 서버 {@code app/core/relative_time.py:part_of_day} 와 반드시 같아야 한다.
     * 예전에는 아침 05-11 / 오후 11-17 이라 05-06, 11-12, 17-18, 21-05 구간에서 두 서비스가
     * 엇갈렸다. 브리핑 문장(AI 서버)과 설명 facts(여기)가 같은 거래를 "오늘 아침"과 "오늘 오후"로
     * 다르게 말하는 일이 실제로 났다. 한쪽을 고치면 다른 쪽도 같이 고칠 것.
     */
    static String partOfDay(LocalDateTime at) {
        int h = at.getHour();
        if (h < 6) {
            return "새벽";
        }
        if (h < 12) {
            return "아침";
        }
        if (h < 18) {
            return "오후";
        }
        return "저녁";
    }
}
