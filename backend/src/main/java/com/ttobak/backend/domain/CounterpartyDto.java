package com.ttobak.backend.domain;

import java.util.List;

/** openapi Counterparty 스키마 */
public record CounterpartyDto(
        Long id,
        String name,
        String relation,
        String kind,
        String bankName,
        String accountNumberMasked,
        List<String> aliases,
        String category
) {
}
