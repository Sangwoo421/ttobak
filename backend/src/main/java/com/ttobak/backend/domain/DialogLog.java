package com.ttobak.backend.domain;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

/** dialog_logs 테이블 + POST /api/dialog-logs 요청 본문 (P1, 사후 검증용) */
@Data
public class DialogLog {
    private Long id;
    @NotBlank
    private String sessionId;
    @NotNull
    private Long userId;
    @NotNull
    private Integer turnNo;
    private String userText;
    private String intent;
    private BigDecimal confidence;
    private String matched;
    private String decision;    // ACCEPT | ASK_AGAIN | BUTTON | LLM_TIEBREAK
    private String state;
    private LocalDateTime createdAt;
}
