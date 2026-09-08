package com.ttobak.backend.controller;

import com.ttobak.backend.domain.SummaryCreateRequest;
import com.ttobak.backend.domain.SummaryDto;
import com.ttobak.backend.domain.SummaryStatusDto;
import com.ttobak.backend.service.SummaryService;
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

/** summaries 태그: 창구 요약서 (담당 강두형). 돈을 움직이는 엔드포인트는 없다. */
@Tag(name = "summaries")
@RestController
@RequestMapping("/api/summaries")
@RequiredArgsConstructor
public class SummaryController {

    private final SummaryService summaryService;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public SummaryDto create(@Valid @RequestBody SummaryCreateRequest request) {
        return summaryService.create(request);
    }

    @GetMapping("/{summaryId}")
    public SummaryDto get(@PathVariable long summaryId) {
        return summaryService.get(summaryId);
    }

    @GetMapping("/by-code/{code}")
    public SummaryDto getByCode(@PathVariable String code) {
        return summaryService.getByCode(code);
    }

    @GetMapping("/{summaryId}/status")
    public SummaryStatusDto status(@PathVariable long summaryId) {
        return summaryService.status(summaryId);
    }
}
