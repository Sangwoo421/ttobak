package com.ttobak.backend.domain;

import java.time.LocalDateTime;

import lombok.Data;

/** users 테이블 */
@Data
public class User {
    private Long id;
    private String name;
    private Integer birthYear;
    private Boolean seniorMode;
    private String homeBranch;
    private LocalDateTime createdAt;
}
