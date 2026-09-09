package com.ttobak.backend.domain;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

/** 해커톤 시연용 6자리 간편비밀번호 로그인 요청. */
@Data
public class SimpleLoginRequest {

    @NotNull
    private Long userId;

    @NotBlank
    @Pattern(regexp = "^[0-9]{6}$")
    private String pin;
}
