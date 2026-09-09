package com.ttobak.backend.domain;

/** 현재 로그인 세션의 최소 사용자 정보. */
public record AuthUserDto(Long userId, String userName) {
}
