package com.ttobak.backend.controller;

import java.util.List;

import com.ttobak.backend.domain.BankBranchDto;
import com.ttobak.backend.domain.BranchTicketCreateRequest;
import com.ttobak.backend.domain.BranchTicketDto;
import com.ttobak.backend.service.BranchTicketService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/** 은행 지점과 모바일 대기표 API. */
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class BranchTicketController {

    private final BranchTicketService branchTicketService;

    @GetMapping("/branches")
    public List<BankBranchDto> branches() {
        return branchTicketService.branches();
    }

    @PostMapping("/branches/{branchId}/tickets")
    @ResponseStatus(HttpStatus.CREATED)
    public BranchTicketDto issue(
            @PathVariable long branchId,
            @Valid @RequestBody BranchTicketCreateRequest request,
            @RequestHeader(value = "Authorization", required = false) String authorization) {
        return branchTicketService.issue(branchId, request, authorization);
    }

    @GetMapping("/branch-tickets/active")
    public BranchTicketDto active(
            @RequestParam long userId,
            @RequestHeader(value = "Authorization", required = false) String authorization) {
        return branchTicketService.active(userId, authorization);
    }

    @GetMapping("/branch-tickets/{ticketId}")
    public BranchTicketDto get(
            @PathVariable long ticketId,
            @RequestHeader(value = "Authorization", required = false) String authorization) {
        return branchTicketService.get(ticketId, authorization);
    }

    @DeleteMapping("/branch-tickets/{ticketId}")
    public BranchTicketDto cancel(
            @PathVariable long ticketId,
            @RequestHeader(value = "Authorization", required = false) String authorization) {
        return branchTicketService.cancel(ticketId, authorization);
    }
}
