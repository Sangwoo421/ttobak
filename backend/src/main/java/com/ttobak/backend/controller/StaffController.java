package com.ttobak.backend.controller;

import java.util.List;

import com.ttobak.backend.domain.ItemHandledRequest;
import com.ttobak.backend.domain.StaffSummaryListItem;
import com.ttobak.backend.domain.SummaryDto;
import com.ttobak.backend.service.SummaryService;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** staff 태그: 직원용 조회·처리 (담당 강두형) */
@Tag(name = "staff")
@RestController
@RequestMapping("/api/staff/summaries")
@RequiredArgsConstructor
public class StaffController {

    private final SummaryService summaryService;

    @GetMapping
    public List<StaffSummaryListItem> list(@RequestParam(required = false) String status) {
        return summaryService.listForStaff(status);
    }

    @PatchMapping("/{summaryId}/items/{itemId}")
    public SummaryDto handleItem(@PathVariable long summaryId,
                                 @PathVariable long itemId,
                                 @Valid @RequestBody ItemHandledRequest body) {
        return summaryService.handleItem(summaryId, itemId, body.getHandled());
    }
}
