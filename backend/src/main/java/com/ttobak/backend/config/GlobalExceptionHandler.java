package com.ttobak.backend.config;

import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 전역 예외 처리기.
 * - 사용자에게는 ErrorCode 에 고정된 한글 메시지 + 코드만 응답한다. 예외 클래스명·스택트레이스·SQL 등은 절대 내려주지 않는다.
 * - 개발자는 서버 로그로 "어떤 요청이 어느 예외를 왜 발생시켰는지" 전부 확인할 수 있다.
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /** 업무 로직 위반: 예상된 상황이라 WARN. */
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> businessException(BusinessException e, HttpServletRequest req) {
        log.warn("[{}] {} {} -> {}: {}", e.getErrorCode().getCode(), req.getMethod(), requestLine(req),
                e.getClass().getSimpleName(), e.getMessage());
        return ResponseEntity.status(e.getErrorCode().getStatus()).body(ErrorResponse.of(e.getErrorCode()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> invalid(MethodArgumentNotValidException e, HttpServletRequest req) {
        StringBuilder detail = new StringBuilder();
        e.getBindingResult().getFieldErrors().forEach(fe ->
                detail.append(fe.getField()).append(": ").append(fe.getDefaultMessage()).append("; "));
        log.warn("[{}] {} {} -> validation failed: {}", ErrorCode.VALIDATION_FAILED.getCode(),
                req.getMethod(), requestLine(req), detail.toString().trim());
        return ResponseEntity.status(ErrorCode.VALIDATION_FAILED.getStatus())
                .body(ErrorResponse.of(ErrorCode.VALIDATION_FAILED));
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ErrorResponse> unreadable(HttpMessageNotReadableException e, HttpServletRequest req) {
        log.warn("[{}] {} {} -> malformed request body: {}", ErrorCode.MALFORMED_REQUEST.getCode(),
                req.getMethod(), requestLine(req), e.getMostSpecificCause().getMessage());
        return ResponseEntity.status(ErrorCode.MALFORMED_REQUEST.getStatus())
                .body(ErrorResponse.of(ErrorCode.MALFORMED_REQUEST));
    }

    /** 예상 못한 시스템 장애: ERROR + 전체 스택트레이스. 사용자에게는 정형화된 메시지만. */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> unexpected(Exception e, HttpServletRequest req) {
        log.error("[{}] {} {} -> unexpected {}", ErrorCode.INTERNAL_ERROR.getCode(),
                req.getMethod(), requestLine(req), e.getClass().getName(), e);
        return ResponseEntity.status(ErrorCode.INTERNAL_ERROR.getStatus())
                .body(ErrorResponse.of(ErrorCode.INTERNAL_ERROR));
    }

    private static String requestLine(HttpServletRequest req) {
        String query = req.getQueryString();
        return query == null ? req.getRequestURI() : req.getRequestURI() + "?" + query;
    }
}
