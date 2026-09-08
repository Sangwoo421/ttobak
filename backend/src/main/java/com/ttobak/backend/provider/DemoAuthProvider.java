package com.ttobak.backend.provider;

import org.springframework.stereotype.Component;

/** 해커톤 시연용: 인증 항상 OK. */
@Component
public class DemoAuthProvider implements AuthProvider {

    @Override
    public void assertUser(long userId) {
        // 시연에서는 검증하지 않는다.
    }
}
