package com.ttobak.backend.domain;

import java.time.LocalDateTime;

import lombok.Data;

/** summary_items 테이블 (payload 는 JSON 문자열) */
@Data
public class SummaryItemRow {
    private Long id;
    private Long summaryId;
    private String section;     // REQUEST | QUESTION | PREP
    private Integer ordinal;
    private String payload;
    private Boolean handled;
    private LocalDateTime handledAt;

    public boolean isPrep() {
        return "PREP".equals(section);
    }

    public boolean isHandled() {
        return Boolean.TRUE.equals(handled);
    }
}
