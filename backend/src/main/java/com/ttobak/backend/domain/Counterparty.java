package com.ttobak.backend.domain;

import java.util.Arrays;
import java.util.List;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

/** counterparties 테이블 (원본 계좌번호는 외부로 나가지 않는다). */
@Data
public class Counterparty {
    private Long id;
    @JsonIgnore
    private Long userId;
    private String name;
    private String relation;
    private String kind;            // PERSON | INSTITUTION
    private String bankName;
    @JsonIgnore
    private String accountNumber;   // 마스킹 전 원본 - 응답에 절대 포함하지 않음
    @JsonIgnore
    private String aliases;         // "아들,철수,큰아들"
    @JsonIgnore
    private String memoPattern;     // 정규식
    private String category;

    public boolean isPerson() {
        return "PERSON".equals(kind);
    }

    public CounterpartyDto toDto() {
        List<String> aliasList = aliases == null || aliases.isBlank()
                ? List.of()
                : Arrays.stream(aliases.split(",")).map(String::trim).filter(s -> !s.isEmpty()).toList();
        return new CounterpartyDto(id, name, relation, kind, bankName,
                AccountNumberMasker.mask(accountNumber), aliasList, category);
    }
}
