package com.ttobak.backend.domain;

import java.time.LocalDateTime;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

/** mute_rules 테이블 + POST /api/mute-rules 요청 본문 */
@Data
public class MuteRule {
    private Long id;
    @NotNull
    private Long userId;
    @NotBlank
    private String counterpartyName;
    private LocalDateTime createdAt;
}
