package com.ttobak.backend.domain;

import java.time.LocalDateTime;

/** 발급된 모바일 대기표와 현재 예상 대기 정보. */
public record BranchTicketDto(
        Long id,
        Long branchId,
        Long summaryId,
        String summaryCode,
        String branchName,
        String branchAddress,
        Integer ticketNo,
        String purpose,
        String status,
        int aheadCount,
        int estimatedWaitMinutes,
        LocalDateTime issuedAt
) {
}
