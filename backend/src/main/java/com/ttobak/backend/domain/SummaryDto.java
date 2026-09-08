package com.ttobak.backend.domain;

import java.time.LocalDateTime;
import java.util.List;

/** openapi Summary 스키마 */
public record SummaryDto(
        Long id,
        String code,
        Integer ticketNo,
        String branchName,
        String status,
        Long userId,
        String userName,
        LocalDateTime createdAt,
        List<SummaryItemDto> items
) {
}
