package com.ttobak.backend.domain;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

/** 지점 모바일 대기표 발급 요청. */
@Data
public class BranchTicketCreateRequest {

    @NotNull
    private Long userId;

    private Long summaryId;

    @Size(max = 60)
    private String purpose;
}
