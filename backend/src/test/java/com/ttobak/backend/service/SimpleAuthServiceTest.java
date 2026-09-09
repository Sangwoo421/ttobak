package com.ttobak.backend.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.when;

import com.ttobak.backend.config.BusinessException;
import com.ttobak.backend.config.ErrorCode;
import com.ttobak.backend.domain.AuthSessionDto;
import com.ttobak.backend.domain.SimpleLoginRequest;
import com.ttobak.backend.domain.User;
import com.ttobak.backend.mapper.UserMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

@ExtendWith(MockitoExtension.class)
class SimpleAuthServiceTest {

    @Mock
    private UserMapper userMapper;

    private SimpleAuthService service;

    @BeforeEach
    void setUp() {
        service = new SimpleAuthService(userMapper);
        ReflectionTestUtils.setField(service, "demoPin", "123456");
        ReflectionTestUtils.setField(service, "sessionMinutes", 30L);
    }

    @Test
    void correctPinCreatesUsableSession() {
        User user = new User();
        user.setId(1L);
        user.setName("김영자");
        when(userMapper.findById(1L)).thenReturn(user);

        SimpleLoginRequest request = new SimpleLoginRequest();
        request.setUserId(1L);
        request.setPin("123456");

        AuthSessionDto session = service.login(request);

        assertThat(session.accessToken()).isNotBlank();
        assertThat(service.currentUser("Bearer " + session.accessToken()).userName()).isEqualTo("김영자");
    }

    @Test
    void wrongPinIsRejected() {
        User user = new User();
        user.setId(1L);
        when(userMapper.findById(1L)).thenReturn(user);

        SimpleLoginRequest request = new SimpleLoginRequest();
        request.setUserId(1L);
        request.setPin("000000");

        assertThatThrownBy(() -> service.login(request))
                .isInstanceOfSatisfying(BusinessException.class,
                        error -> assertThat(error.getErrorCode()).isEqualTo(ErrorCode.AUTH_INVALID_CREDENTIALS));
    }
}
