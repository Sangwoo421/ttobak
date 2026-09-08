package com.ttobak.backend.domain;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/** 요약서 QUESTION 항목 payload */
@Data
public class QuestionItemPayload {
    private Long transactionId;
    @NotBlank
    private String text;
}
