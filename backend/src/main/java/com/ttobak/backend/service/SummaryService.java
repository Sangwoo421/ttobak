package com.ttobak.backend.service;

import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ttobak.backend.config.BadRequestException;
import com.ttobak.backend.config.NotFoundException;
import com.ttobak.backend.domain.AccountNumberMasker;
import com.ttobak.backend.domain.CounterSummary;
import com.ttobak.backend.domain.Counterparty;
import com.ttobak.backend.domain.PrepItemPayload;
import com.ttobak.backend.domain.QuestionItemPayload;
import com.ttobak.backend.domain.RequestItemPayload;
import com.ttobak.backend.domain.StaffSummaryListItem;
import com.ttobak.backend.domain.SummaryCreateRequest;
import com.ttobak.backend.domain.SummaryDto;
import com.ttobak.backend.domain.SummaryItemDto;
import com.ttobak.backend.domain.SummaryItemRow;
import com.ttobak.backend.domain.SummaryStatusDto;
import com.ttobak.backend.domain.User;
import com.ttobak.backend.mapper.SummaryMapper;
import com.ttobak.backend.provider.AuthProvider;
import com.ttobak.backend.provider.TransactionProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 창구 요약서. "이체 요청"은 요약서 항목으로 저장될 뿐이며, 이 서비스는 돈을 움직이지 않는다.
 */
@Service
@RequiredArgsConstructor
public class SummaryService {

    private static final Set<String> STATUSES = Set.of("OPEN", "IN_PROGRESS", "DONE");
    private static final String SECTION_REQUEST = "REQUEST";
    private static final String SECTION_QUESTION = "QUESTION";
    private static final String SECTION_PREP = "PREP";
    private static final String TYPE_TRANSFER = "TRANSFER";

    private final SummaryMapper summaryMapper;
    private final TransactionProvider transactions;
    private final AuthProvider auth;
    private final ObjectMapper objectMapper;
    private final SecureRandom random = new SecureRandom();

    // ---------------------------------------------------------------- create

    @Transactional
    public SummaryDto create(SummaryCreateRequest req) {
        auth.assertUser(req.getUserId());
        User user = transactions.findUser(req.getUserId())
                .orElseThrow(() -> new BadRequestException("unknown user_id " + req.getUserId()));

        List<RequestItemPayload> requests = req.getRequests() == null ? List.of() : req.getRequests();
        List<QuestionItemPayload> questions = req.getQuestions() == null ? List.of() : req.getQuestions();

        for (RequestItemPayload r : requests) {
            if (!Boolean.TRUE.equals(r.getConfirmedByUser())) {
                throw new BadRequestException("requests[].confirmed_by_user must be true (CONFIRM 단계에서 '예'를 받아야 한다)");
            }
            if (!TYPE_TRANSFER.equals(r.getType())) {
                throw new BadRequestException("requests[].type must be TRANSFER");
            }
            if (r.getRecipientCounterpartyId() != null) {
                fillFromCounterparty(r, user.getId());
            }
        }

        String branch = req.getBranchName() == null || req.getBranchName().isBlank()
                ? user.getHomeBranch() : req.getBranchName().trim();
        if (branch == null || branch.isBlank()) {
            throw new BadRequestException("branch_name is required (user has no home_branch)");
        }

        CounterSummary summary = new CounterSummary();
        summary.setUserId(user.getId());
        summary.setCode(newUniqueCode());
        Integer maxTicket = summaryMapper.maxTicketNo();
        summary.setTicketNo(maxTicket == null ? 1 : maxTicket + 1);
        summary.setBranchName(branch);
        summary.setStatus("OPEN");
        summaryMapper.insertSummary(summary);

        int ordinal = 1;
        for (RequestItemPayload r : requests) {
            insertItem(summary.getId(), SECTION_REQUEST, ordinal++, r);
        }
        ordinal = 1;
        for (QuestionItemPayload q : questions) {
            insertItem(summary.getId(), SECTION_QUESTION, ordinal++, q);
        }
        // 준비물: TRANSFER 가 있으면 신분증 필수 + 통장/카드 권장, 아니면 신분증만
        boolean hasTransfer = requests.stream().anyMatch(r -> TYPE_TRANSFER.equals(r.getType()));
        insertItem(summary.getId(), SECTION_PREP, 1, new PrepItemPayload("신분증", true));
        if (hasTransfer) {
            insertItem(summary.getId(), SECTION_PREP, 2, new PrepItemPayload("통장 또는 카드", false));
        }
        return get(summary.getId());
    }

    private void fillFromCounterparty(RequestItemPayload r, long userId) {
        Counterparty cp = transactions.findCounterparty(r.getRecipientCounterpartyId())
                .filter(c -> c.getUserId() != null && c.getUserId() == userId)
                .orElseThrow(() -> new BadRequestException(
                        "recipient_counterparty_id " + r.getRecipientCounterpartyId() + " is not a registered counterparty of user " + userId));
        if (r.getRecipientName() == null || r.getRecipientName().isBlank()) {
            r.setRecipientName(cp.getName());
        }
        if (r.getRecipientRelation() == null) {
            r.setRecipientRelation(cp.getRelation());
        }
        if (r.getRecipientBank() == null) {
            r.setRecipientBank(cp.getBankName());
        }
        r.setRecipientAccountMasked(AccountNumberMasker.mask(cp.getAccountNumber()));
    }

    private String newUniqueCode() {
        for (int i = 0; i < 20; i++) {
            String code = String.format("%06d", random.nextInt(1_000_000));
            if (summaryMapper.countByCode(code) == 0) {
                return code;
            }
        }
        throw new IllegalStateException("could not allocate a unique 6-digit code");
    }

    private void insertItem(long summaryId, String section, int ordinal, Object payload) {
        SummaryItemRow row = new SummaryItemRow();
        row.setSummaryId(summaryId);
        row.setSection(section);
        row.setOrdinal(ordinal);
        row.setPayload(toJson(payload));
        summaryMapper.insertItem(row);
    }

    // ---------------------------------------------------------------- read

    public SummaryDto get(long summaryId) {
        CounterSummary s = summaryMapper.findById(summaryId);
        if (s == null) {
            throw new NotFoundException("summary " + summaryId + " not found");
        }
        return toDto(s, summaryMapper.findItems(summaryId));
    }

    public SummaryDto getByCode(String code) {
        CounterSummary s = summaryMapper.findByCode(code);
        if (s == null) {
            throw new NotFoundException("summary with code " + code + " not found");
        }
        return toDto(s, summaryMapper.findItems(s.getId()));
    }

    public SummaryStatusDto status(long summaryId) {
        CounterSummary s = summaryMapper.findById(summaryId);
        if (s == null) {
            throw new NotFoundException("summary " + summaryId + " not found");
        }
        List<SummaryItemRow> items = summaryMapper.findItems(summaryId);
        List<SummaryItemRow> core = items.stream().filter(i -> !i.isPrep()).toList();
        int handled = (int) core.stream().filter(SummaryItemRow::isHandled).count();
        LocalDateTime lastHandledAt = items.stream()
                .map(SummaryItemRow::getHandledAt)
                .filter(t -> t != null)
                .max(Comparator.naturalOrder())
                .orElse(null);
        return new SummaryStatusDto(s.getId(), s.getStatus(), handled, core.size(), lastHandledAt);
    }

    public List<StaffSummaryListItem> listForStaff(String status) {
        if (status != null && !status.isBlank() && !STATUSES.contains(status)) {
            throw new BadRequestException("status must be one of " + STATUSES);
        }
        return summaryMapper.findForStaff(status == null || status.isBlank() ? null : status);
    }

    // ---------------------------------------------------------------- staff update

    @Transactional
    public SummaryDto handleItem(long summaryId, long itemId, boolean handled) {
        if (summaryMapper.findById(summaryId) == null) {
            throw new NotFoundException("summary " + summaryId + " not found");
        }
        if (summaryMapper.findItem(summaryId, itemId) == null) {
            throw new NotFoundException("item " + itemId + " not found in summary " + summaryId);
        }
        summaryMapper.updateItemHandled(itemId, handled);
        recomputeStatus(summaryId);
        return get(summaryId);
    }

    /** 모든 REQUEST/QUESTION 처리 → DONE, 하나라도 처리 → IN_PROGRESS, 그 외 OPEN */
    private void recomputeStatus(long summaryId) {
        List<SummaryItemRow> items = summaryMapper.findItems(summaryId);
        List<SummaryItemRow> core = items.stream().filter(i -> !i.isPrep()).toList();
        String status;
        if (!core.isEmpty() && core.stream().allMatch(SummaryItemRow::isHandled)) {
            status = "DONE";
        } else if (items.stream().anyMatch(SummaryItemRow::isHandled)) {
            status = "IN_PROGRESS";
        } else {
            status = "OPEN";
        }
        summaryMapper.updateStatus(summaryId, status);
    }

    // ---------------------------------------------------------------- mapping

    private SummaryDto toDto(CounterSummary s, List<SummaryItemRow> rows) {
        List<SummaryItemDto> items = new ArrayList<>();
        for (SummaryItemRow r : rows) {
            items.add(new SummaryItemDto(r.getId(), r.getSection(), r.getOrdinal(),
                    fromJson(r.getPayload()), r.isHandled(), r.getHandledAt()));
        }
        return new SummaryDto(s.getId(), s.getCode(), s.getTicketNo(), s.getBranchName(), s.getStatus(),
                s.getUserId(), s.getUserName(), s.getCreatedAt(), items);
    }

    private String toJson(Object payload) {
        try {
            return objectMapper.writeValueAsString(payload);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("payload serialization failed", e);
        }
    }

    private Map<String, Object> fromJson(String json) {
        if (json == null) {
            return Map.of();
        }
        try {
            return objectMapper.readValue(json, new TypeReference<LinkedHashMap<String, Object>>() { });
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("payload deserialization failed", e);
        }
    }
}
