package com.ttobak.backend.config;

/**
 * 업무 로직 위반의 공통 부모. 시스템 장애(IllegalStateException 등)와 구조적으로 분리된다.
 * getMessage() 는 서버 로그용 상세 설명이며, 사용자에게는 절대 노출하지 않는다
 * (클라이언트 응답에는 {@link #getErrorCode()}.getMessage() 의 고정 문구만 나간다).
 */
public class BusinessException extends RuntimeException {

    private final ErrorCode errorCode;

    public BusinessException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.errorCode = errorCode;
    }

    /** @param logDetail 서버 로그에만 남는 상세 설명 (예: "summary 5 not found") */
    public BusinessException(ErrorCode errorCode, String logDetail) {
        super(logDetail);
        this.errorCode = errorCode;
    }

    public ErrorCode getErrorCode() {
        return errorCode;
    }
}
