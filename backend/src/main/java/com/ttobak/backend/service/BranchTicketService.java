package com.ttobak.backend.service;

import java.util.List;

import com.ttobak.backend.config.BusinessException;
import com.ttobak.backend.config.ErrorCode;
import com.ttobak.backend.domain.BankBranch;
import com.ttobak.backend.domain.BankBranchDto;
import com.ttobak.backend.domain.BranchTicketCreateRequest;
import com.ttobak.backend.domain.BranchTicketDto;
import com.ttobak.backend.domain.BranchTicketRow;
import com.ttobak.backend.domain.CounterSummary;
import com.ttobak.backend.mapper.BranchTicketMapper;
import com.ttobak.backend.mapper.SummaryMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 지점 조회와 모바일 대기표 발급·조회·취소. 금융 거래를 수행하지 않는다. */
@Service
@RequiredArgsConstructor
public class BranchTicketService {

    private static final String WAITING = "WAITING";
    private final BranchTicketMapper mapper;
    private final SummaryMapper summaryMapper;
    private final SimpleAuthService authService;

    public List<BankBranchDto> branches() {
        return mapper.findActiveBranches().stream().map(branch -> {
            int waiting = mapper.countWaiting(branch.getId());
            return new BankBranchDto(branch.getId(), branch.getName(), branch.getDistrict(),
                    branch.getAddress(), branch.getOpeningHours(), waiting,
                    waiting * branch.getAvgServiceMinutes());
        }).toList();
    }

    @Transactional
    public BranchTicketDto issue(long branchId, BranchTicketCreateRequest request, String authorization) {
        authService.assertUser(authorization, request.getUserId());
        if (mapper.lockUser(request.getUserId()) == null) {
            throw new BusinessException(ErrorCode.UNKNOWN_USER, "unknown user " + request.getUserId());
        }
        CounterSummary linkedSummary = requireOwnedSummary(request.getSummaryId(), request.getUserId());

        BranchTicketRow active = mapper.findActiveTicketByUser(request.getUserId());
        if (active != null) {
            if (active.getBranchId() == branchId) {
                if (linkedSummary != null) {
                    mapper.attachSummary(active.getId(), linkedSummary.getId());
                    summaryMapper.updateBranchTicket(linkedSummary.getId(), active.getBranchName(), active.getTicketNo());
                    active = mapper.findTicketById(active.getId());
                }
                return toDto(active);
            }
            throw new BusinessException(ErrorCode.ACTIVE_TICKET_EXISTS,
                    "user already has an active ticket at branch " + active.getBranchId());
        }

        BankBranch branch = mapper.findBranchByIdForUpdate(branchId);
        if (branch == null) {
            throw new BusinessException(ErrorCode.BRANCH_NOT_FOUND, "unknown branch " + branchId);
        }

        int ticketNo = branch.getLastTicketNo() + 1;
        mapper.updateLastTicketNo(branchId, ticketNo);

        BranchTicketRow row = new BranchTicketRow();
        row.setBranchId(branchId);
        row.setUserId(request.getUserId());
        row.setSummaryId(request.getSummaryId());
        row.setTicketNo(ticketNo);
        row.setPurpose(normalizePurpose(request.getPurpose()));
        row.setStatus(WAITING);
        mapper.insertTicket(row);
        if (linkedSummary != null) {
            summaryMapper.updateBranchTicket(linkedSummary.getId(), branch.getName(), ticketNo);
        }
        return toDto(mapper.findTicketById(row.getId()));
    }

    public BranchTicketDto active(long userId, String authorization) {
        authService.assertUser(authorization, userId);
        BranchTicketRow row = mapper.findActiveTicketByUser(userId);
        return row == null ? null : toDto(row);
    }

    public BranchTicketDto get(long ticketId, String authorization) {
        long userId = authService.requireUser(authorization);
        BranchTicketRow row = requireTicket(ticketId);
        assertOwner(row, userId);
        return toDto(row);
    }

    @Transactional
    public BranchTicketDto cancel(long ticketId, String authorization) {
        long userId = authService.requireUser(authorization);
        BranchTicketRow row = requireTicket(ticketId);
        assertOwner(row, userId);
        if (!WAITING.equals(row.getStatus())) {
            throw new BusinessException(ErrorCode.BRANCH_TICKET_NOT_CANCELLABLE,
                    "ticket status is " + row.getStatus());
        }
        if (mapper.cancelTicket(ticketId) == 0) {
            throw new BusinessException(ErrorCode.BRANCH_TICKET_NOT_CANCELLABLE,
                    "ticket status changed before cancellation");
        }
        return toDto(mapper.findTicketById(ticketId));
    }

    private BranchTicketRow requireTicket(long ticketId) {
        BranchTicketRow row = mapper.findTicketById(ticketId);
        if (row == null) {
            throw new BusinessException(ErrorCode.BRANCH_TICKET_NOT_FOUND, "unknown ticket " + ticketId);
        }
        return row;
    }

    private static void assertOwner(BranchTicketRow row, long userId) {
        if (row.getUserId() != userId) {
            throw new BusinessException(ErrorCode.BRANCH_TICKET_NOT_OWNED,
                    "ticket does not belong to authenticated user");
        }
    }

    private BranchTicketDto toDto(BranchTicketRow row) {
        int ahead = WAITING.equals(row.getStatus())
                ? mapper.countAhead(row.getBranchId(), row.getTicketNo()) : 0;
        int minutes = ahead * row.getAvgServiceMinutes();
        return new BranchTicketDto(row.getId(), row.getBranchId(), row.getSummaryId(), row.getSummaryCode(),
                row.getBranchName(), row.getBranchAddress(), row.getTicketNo(), row.getPurpose(), row.getStatus(),
                ahead, minutes, row.getIssuedAt());
    }

    private CounterSummary requireOwnedSummary(Long summaryId, long userId) {
        if (summaryId == null) return null;
        CounterSummary summary = summaryMapper.findById(summaryId);
        if (summary == null) {
            throw new BusinessException(ErrorCode.SUMMARY_NOT_FOUND, "unknown summary " + summaryId);
        }
        if (summary.getUserId() != userId) {
            throw new BusinessException(ErrorCode.AUTH_FORBIDDEN, "summary does not belong to authenticated user");
        }
        return summary;
    }

    private static String normalizePurpose(String purpose) {
        return purpose == null || purpose.isBlank() ? "일반 상담" : purpose.trim();
    }
}
