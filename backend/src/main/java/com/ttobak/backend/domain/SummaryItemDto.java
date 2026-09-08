package com.ttobak.backend.domain;

import java.time.LocalDateTime;

/** openapi SummaryItem 스키마 (payload 는 섹션별 객체) */
public record SummaryItemDto(
        Long id,
        String section,
        Integer ordinal,
        Object payload,
        boolean handled,
        LocalDateTime handledAt
) {
}
