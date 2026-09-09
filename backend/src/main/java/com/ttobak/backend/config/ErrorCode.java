package com.ttobak.backend.config;

import org.springframework.http.HttpStatus;

/** 업무 에러코드. 코드·사용자 메시지·HTTP 상태를 한 곳에서 관리한다. */
public enum ErrorCode {

    // ---- 범용 폴백 (구체적 코드가 마땅치 않을 때만) ----
    BAD_REQUEST("E000", "잘못된 요청입니다", HttpStatus.BAD_REQUEST),
    NOT_FOUND("E001", "요청한 정보를 찾을 수 없습니다", HttpStatus.NOT_FOUND),

    // ---- 공통 ----
    VALIDATION_FAILED("E002", "입력값이 올바르지 않습니다", HttpStatus.BAD_REQUEST),
    MALFORMED_REQUEST("E003", "요청 형식이 올바르지 않습니다", HttpStatus.BAD_REQUEST),
    INTERNAL_ERROR("E999", "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", HttpStatus.INTERNAL_SERVER_ERROR),

    // ---- 요약서 (SummaryService) ----
    SUMMARY_NOT_FOUND("E101", "요약서를 찾을 수 없습니다", HttpStatus.NOT_FOUND),
    SUMMARY_ITEM_NOT_FOUND("E102", "요약서 항목을 찾을 수 없습니다", HttpStatus.NOT_FOUND),
    INVALID_STAFF_STATUS_FILTER("E103", "상태 값이 올바르지 않습니다", HttpStatus.BAD_REQUEST),
    CONFIRMATION_REQUIRED("E104", "사용자 확인이 필요한 요청입니다", HttpStatus.BAD_REQUEST),
    INVALID_TRANSFER_TYPE("E105", "지원하지 않는 요청 유형입니다", HttpStatus.BAD_REQUEST),
    BRANCH_NAME_REQUIRED("E106", "지점 정보가 필요합니다", HttpStatus.BAD_REQUEST),
    UNKNOWN_USER("E107", "존재하지 않는 사용자입니다", HttpStatus.BAD_REQUEST),
    COUNTERPARTY_NOT_OWNED("E108", "등록되지 않은 수취인입니다", HttpStatus.BAD_REQUEST),
    EMPTY_SUMMARY("E109", "요약서에 저장할 내용이 없습니다", HttpStatus.BAD_REQUEST),

    // ---- 간편 로그인 ----
    AUTH_INVALID_CREDENTIALS("E301", "간편비밀번호가 올바르지 않습니다", HttpStatus.UNAUTHORIZED),
    AUTH_REQUIRED("E302", "로그인이 필요합니다", HttpStatus.UNAUTHORIZED),
    AUTH_FORBIDDEN("E303", "이 사용자 정보에 접근할 수 없습니다", HttpStatus.FORBIDDEN),

    // ---- 지점 대기표 ----
    BRANCH_NOT_FOUND("E401", "은행 지점을 찾을 수 없습니다", HttpStatus.NOT_FOUND),
    ACTIVE_TICKET_EXISTS("E402", "이미 사용 중인 대기표가 있습니다", HttpStatus.CONFLICT),
    BRANCH_TICKET_NOT_FOUND("E403", "대기표를 찾을 수 없습니다", HttpStatus.NOT_FOUND),
    BRANCH_TICKET_NOT_CANCELLABLE("E404", "지금은 대기표를 취소할 수 없습니다", HttpStatus.CONFLICT),
    BRANCH_TICKET_NOT_OWNED("E405", "이 대기표에 접근할 수 없습니다", HttpStatus.FORBIDDEN),

    // ---- 브리핑·분류·알림 (BriefingService, ClassificationService, MuteRuleService) ----
    USER_NOT_FOUND("E201", "사용자를 찾을 수 없습니다", HttpStatus.NOT_FOUND),
    NOTIFICATION_NOT_FOUND("E202", "알림을 찾을 수 없습니다", HttpStatus.NOT_FOUND),
    TRANSACTION_NOT_FOUND("E203", "거래 내역을 찾을 수 없습니다", HttpStatus.NOT_FOUND);

    private final String code;
    private final String message;
    private final HttpStatus status;

    ErrorCode(String code, String message, HttpStatus status) {
        this.code = code;
        this.message = message;
        this.status = status;
    }

    public String getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }

    public HttpStatus getStatus() {
        return status;
    }
}
