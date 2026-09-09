package com.ttobak.backend.domain;

/** 사용자에게 보여줄 지점별 현재 대기 현황. */
public record BankBranchDto(
        Long id,
        String name,
        String district,
        String address,
        String openingHours,
        int waitingCount,
        int estimatedWaitMinutes
) {
}
