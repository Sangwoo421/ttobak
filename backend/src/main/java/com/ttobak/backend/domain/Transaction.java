package com.ttobak.backend.domain;

import java.time.LocalDateTime;

import lombok.Data;

/** transactions 테이블 = openapi Transaction 스키마 (필드 그대로 노출) */
@Data
public class Transaction {
    private Long id;
    private Long accountId;
    private String type;              // IN | OUT
    private Long amount;
    private String counterpartyName;
    private String memo;
    private String channel;
    private LocalDateTime occurredAt;
    private Long counterpartyId;

    public boolean isIn() {
        return "IN".equals(type);
    }
}
