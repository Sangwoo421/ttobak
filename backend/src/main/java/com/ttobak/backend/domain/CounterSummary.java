package com.ttobak.backend.domain;

import java.time.LocalDateTime;

import lombok.Data;

/** counter_summaries 테이블 (+ users.name 조인) */
@Data
public class CounterSummary {
    private Long id;
    private Long userId;
    private String userName;
    private String code;
    private Integer ticketNo;
    private String branchName;
    private String status;      // OPEN | IN_PROGRESS | DONE
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
