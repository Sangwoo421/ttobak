package com.ttobak.backend.domain;

/** 간편 로그인 후 프론트가 보관할 세션 정보. */
public record AuthSessionDto(
        String accessToken,
        String tokenType,
        long expiresInSeconds,
        Long userId,
        String userName
) {
}
