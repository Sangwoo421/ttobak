package com.ttobak.backend.domain;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

/**
 * 요약서 REQUEST 항목 payload. "이체 요청"은 창구 요약서에 담기는 것뿐이며 이 서버는 돈을 움직이지 않는다.
 */
@Data
public class RequestItemPayload {
    @NotBlank
    private String type;                    // TRANSFER
    private Long recipientCounterpartyId;
    @NotBlank
    private String recipientName;
    private String recipientRelation;
    private String recipientBank;
    private String recipientAccountMasked;  // 서버가 counterparty 로 채운다
    @NotNull
    private Long amount;
    private String note;
    private Boolean confirmedByUser;        // false/null 이면 400
}
