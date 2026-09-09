package com.ttobak.backend.domain;

import lombok.Data;

/** 모바일 대기표를 발급할 수 있는 은행 지점. */
@Data
public class BankBranch {
    private Long id;
    private String name;
    private String district;
    private String address;
    private String openingHours;
    private Integer currentServingNo;
    private Integer lastTicketNo;
    private Integer avgServiceMinutes;
    private Boolean active;
}
