package com.ttobak.backend.service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import com.ttobak.backend.config.BusinessException;
import com.ttobak.backend.config.ErrorCode;
import com.ttobak.backend.domain.AuthSessionDto;
import com.ttobak.backend.domain.AuthUserDto;
import com.ttobak.backend.domain.SimpleLoginRequest;
import com.ttobak.backend.domain.User;
import com.ttobak.backend.mapper.UserMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * 해커톤용 간편 로그인 경계.
 * 실제 은행 환경에서는 이 구현을 인증 서버·FIDO/생체인증 SDK로 교체한다.
 * PIN 원문은 저장하지 않으며, 발급한 토큰은 서버 메모리에만 TTL 동안 유지한다.
 */
@Service
@RequiredArgsConstructor
public class SimpleAuthService {

    private static final SecureRandom RANDOM = new SecureRandom();

    private final UserMapper userMapper;
    private final Map<String, Session> sessions = new ConcurrentHashMap<>();

    @Value("${ttobak.auth.demo-pin:123456}")
    private String demoPin;

    @Value("${ttobak.auth.session-minutes:30}")
    private long sessionMinutes;

    public AuthSessionDto login(SimpleLoginRequest request) {
        User user = userMapper.findById(request.getUserId());
        if (user == null || !same(request.getPin(), demoPin)) {
            throw new BusinessException(ErrorCode.AUTH_INVALID_CREDENTIALS, "invalid user or PIN");
        }

        Instant expiresAt = Instant.now().plus(Duration.ofMinutes(sessionMinutes));
        String token = newToken();
        sessions.put(token, new Session(user.getId(), user.getName(), expiresAt));
        return new AuthSessionDto(token, "Bearer", Duration.ofMinutes(sessionMinutes).toSeconds(),
                user.getId(), user.getName());
    }

    public AuthUserDto currentUser(String authorization) {
        Session session = requireSession(authorization);
        return new AuthUserDto(session.userId(), session.userName());
    }

    public long requireUser(String authorization) {
        return requireSession(authorization).userId();
    }

    public void assertUser(String authorization, long requestedUserId) {
        if (requireUser(authorization) != requestedUserId) {
            throw new BusinessException(ErrorCode.AUTH_FORBIDDEN, "authenticated user does not match request user");
        }
    }

    public void logout(String authorization) {
        String token = bearerToken(authorization);
        sessions.remove(token);
    }

    private Session requireSession(String authorization) {
        String token = bearerToken(authorization);
        Session session = sessions.get(token);
        if (session == null || session.expiresAt().isBefore(Instant.now())) {
            sessions.remove(token);
            throw new BusinessException(ErrorCode.AUTH_REQUIRED, "missing or expired auth session");
        }
        return session;
    }

    private static String bearerToken(String authorization) {
        if (authorization == null || !authorization.startsWith("Bearer ")) {
            throw new BusinessException(ErrorCode.AUTH_REQUIRED, "Bearer token is required");
        }
        String token = authorization.substring(7).trim();
        if (token.isEmpty()) {
            throw new BusinessException(ErrorCode.AUTH_REQUIRED, "Bearer token is empty");
        }
        return token;
    }

    private static String newToken() {
        byte[] bytes = new byte[32];
        RANDOM.nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }

    private static boolean same(String actual, String expected) {
        return MessageDigest.isEqual(
                actual.getBytes(StandardCharsets.UTF_8),
                expected.getBytes(StandardCharsets.UTF_8));
    }

    private record Session(long userId, String userName, Instant expiresAt) {
    }
}
