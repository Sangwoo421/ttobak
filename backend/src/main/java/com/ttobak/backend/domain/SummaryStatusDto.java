package com.ttobak.backend.domain;

import java.time.LocalDateTime;

/** openapi SummaryStatus 스키마 (PREP 제외 집계) */
public record SummaryStatusDto(
        Long id,
        String status,
        int handledCount,
        int totalCount,
        LocalDateTime lastHandledAt
) {
}
