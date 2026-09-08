package com.ttobak.backend.domain;

import java.util.List;

/** openapi Classification 스키마. 규칙 엔진의 출력 (결정적). */
public record Classification(
        Long transactionId,
        String level,          // CONFIRMED | PARTIAL | UNKNOWN
        String ruleId,         // R1_.. ~ R5_..
        String spokenName,
        List<String> facts,
        List<String> unknowns,
        String counterHint,
        CounterpartyDto counterparty
) {
}
