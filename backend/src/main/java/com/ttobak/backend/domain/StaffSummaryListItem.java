package com.ttobak.backend.domain;

import java.time.LocalDateTime;

import lombok.Data;

/** openapi StaffSummaryListItem 스키마 (item_count 는 PREP 제외) */
@Data
public class StaffSummaryListItem {
    private Long id;
    private String code;
    private Integer ticketNo;
    private String userName;
    private String status;
    private LocalDateTime createdAt;
    private Integer itemCount;
}
