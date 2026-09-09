package com.ttobak.backend.controller;

import com.ttobak.backend.domain.AuthSessionDto;
import com.ttobak.backend.domain.AuthUserDto;
import com.ttobak.backend.domain.SimpleLoginRequest;
import com.ttobak.backend.service.SimpleAuthService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/** 해커톤용 간편 로그인 세션 API. */
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final SimpleAuthService authService;

    @PostMapping("/simple-login")
    public AuthSessionDto login(@Valid @RequestBody SimpleLoginRequest request) {
        return authService.login(request);
    }

    @GetMapping("/session")
    public AuthUserDto session(@RequestHeader(value = "Authorization", required = false) String authorization) {
        return authService.currentUser(authorization);
    }

    @PostMapping("/logout")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void logout(@RequestHeader(value = "Authorization", required = false) String authorization) {
        authService.logout(authorization);
    }
}
