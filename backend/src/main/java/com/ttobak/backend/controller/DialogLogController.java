package com.ttobak.backend.controller;

import com.ttobak.backend.domain.DialogLog;
import com.ttobak.backend.service.DialogLogService;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/** logs 태그: AI 서버가 턴마다 남기는 판정 근거 (P1, 담당 안상우) */
@Tag(name = "logs")
@RestController
@RequestMapping("/api/dialog-logs")
@RequiredArgsConstructor
public class DialogLogController {

    private final DialogLogService dialogLogService;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public DialogLog create(@Valid @RequestBody DialogLog log) {
        return dialogLogService.save(log);
    }
}
