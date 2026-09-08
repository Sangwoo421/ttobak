package com.ttobak.backend.domain;

import java.util.List;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

/** POST /api/summaries 요청 본문 */
@Data
public class SummaryCreateRequest {
    @NotNull
    private Long userId;
    private String sessionId;
    private String branchName;              // 없으면 users.home_branch
    @Valid
    private List<RequestItemPayload> requests;
    @Valid
    private List<QuestionItemPayload> questions;
}
