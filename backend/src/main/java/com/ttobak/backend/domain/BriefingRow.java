package com.ttobak.backend.domain;

import lombok.Data;

/** notifications ⋈ transactions 조회 결과 (브리핑 선별용) */
@Data
public class BriefingRow {
    private Long notificationId;
    private Transaction transaction;
}
