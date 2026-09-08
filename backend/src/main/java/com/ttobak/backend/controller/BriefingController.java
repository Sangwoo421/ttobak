package com.ttobak.backend.controller;

import com.ttobak.backend.domain.BriefingResponse;
import com.ttobak.backend.domain.MuteRule;
import com.ttobak.backend.service.BriefingService;
import com.ttobak.backend.service.MuteRuleService;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/** briefing 태그: 브리핑 선별, 들었음 기록, 뮤트 등록 (담당 안상우) */
@Tag(name = "briefing")
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class BriefingController {

    private final BriefingService briefingService;
    private final MuteRuleService muteRuleService;

    @GetMapping("/users/{userId}/briefing")
    public BriefingResponse briefing(@PathVariable long userId) {
        return briefingService.briefing(userId);
    }

    @PostMapping("/notifications/{notificationId}/heard")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void heard(@PathVariable long notificationId) {
        briefingService.markHeard(notificationId);
    }

    @PostMapping("/mute-rules")
    @ResponseStatus(HttpStatus.CREATED)
    public MuteRule createMuteRule(@Valid @RequestBody MuteRule rule) {
        return muteRuleService.create(rule);
    }
}
