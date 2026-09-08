package com.ttobak.backend.provider;

/**
 * 외부 경계: 사용자 인증/권한. 시연은 항상 통과(DemoAuthProvider).
 * 실제 앱에서는 로그인 세션·토큰 검증 구현으로 교체한다.
 */
public interface AuthProvider {

    /** 요청 주체가 user_id 에 접근할 수 있는지 확인. 불가하면 예외. */
    void assertUser(long userId);
}
