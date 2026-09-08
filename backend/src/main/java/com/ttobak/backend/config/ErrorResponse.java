package com.ttobak.backend.config;

import java.time.LocalDateTime;

/** 클라이언트에 나가는 오류 응답. 예외 객체·스택트레이스는 절대 담지 않는다. */
public record ErrorResponse(String code, String message, LocalDateTime timestamp) {

    public static ErrorResponse of(ErrorCode errorCode) {
        return new ErrorResponse(errorCode.getCode(), errorCode.getMessage(), LocalDateTime.now());
    }
}
