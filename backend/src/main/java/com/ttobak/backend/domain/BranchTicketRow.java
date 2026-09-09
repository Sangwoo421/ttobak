package com.ttobak.backend.domain;

import java.time.LocalDateTime;

import lombok.Data;

/** branch_tickets 조회·저장용 행 모델. */
@Data
public class BranchTicketRow {
    private Long id;
    private Long branchId;
    private Long userId;
    private Long summaryId;
    private Integer ticketNo;
    private String purpose;
    private String status;
    private LocalDateTime issuedAt;
    private LocalDateTime calledAt;
    private LocalDateTime cancelledAt;
    private String branchName;
    private String branchAddress;
    private String summaryCode;
    private Integer currentServingNo;
    private Integer avgServiceMinutes;
}
