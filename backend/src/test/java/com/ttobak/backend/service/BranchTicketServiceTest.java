package com.ttobak.backend.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.ttobak.backend.domain.BankBranch;
import com.ttobak.backend.domain.BranchTicketCreateRequest;
import com.ttobak.backend.domain.BranchTicketDto;
import com.ttobak.backend.domain.BranchTicketRow;
import com.ttobak.backend.domain.CounterSummary;
import com.ttobak.backend.mapper.BranchTicketMapper;
import com.ttobak.backend.mapper.SummaryMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class BranchTicketServiceTest {

    @Mock
    private BranchTicketMapper mapper;
    @Mock
    private SummaryMapper summaryMapper;
    @Mock
    private SimpleAuthService authService;

    private BranchTicketService service;

    @BeforeEach
    void setUp() {
        service = new BranchTicketService(mapper, summaryMapper, authService);
    }

    @Test
    void issuingTicketUpdatesLinkedSummaryBranchAndNumber() {
        BankBranch branch = new BankBranch();
        branch.setId(1L);
        branch.setName("KB국민은행 종로지점");
        branch.setLastTicketNo(14);
        branch.setAvgServiceMinutes(6);

        CounterSummary summary = new CounterSummary();
        summary.setId(2L);
        summary.setUserId(1L);

        BranchTicketRow stored = new BranchTicketRow();
        stored.setId(100L);
        stored.setBranchId(1L);
        stored.setUserId(1L);
        stored.setSummaryId(2L);
        stored.setSummaryCode("482913");
        stored.setBranchName(branch.getName());
        stored.setBranchAddress("서울 종로구 종로");
        stored.setTicketNo(15);
        stored.setPurpose("창구 요약서 업무");
        stored.setStatus("WAITING");
        stored.setAvgServiceMinutes(6);

        when(summaryMapper.findById(2L)).thenReturn(summary);
        when(mapper.lockUser(1L)).thenReturn(1L);
        when(mapper.findActiveTicketByUser(1L)).thenReturn(null);
        when(mapper.findBranchByIdForUpdate(1L)).thenReturn(branch);
        doAnswer(invocation -> {
            BranchTicketRow row = invocation.getArgument(0);
            row.setId(100L);
            return null;
        }).when(mapper).insertTicket(any(BranchTicketRow.class));
        when(mapper.findTicketById(100L)).thenReturn(stored);
        when(mapper.countAhead(1L, 15)).thenReturn(3);

        BranchTicketCreateRequest request = new BranchTicketCreateRequest();
        request.setUserId(1L);
        request.setSummaryId(2L);
        request.setPurpose("창구 요약서 업무");

        BranchTicketDto result = service.issue(1L, request, "Bearer token");

        assertThat(result.ticketNo()).isEqualTo(15);
        assertThat(result.summaryId()).isEqualTo(2L);
        assertThat(result.aheadCount()).isEqualTo(3);
        assertThat(result.estimatedWaitMinutes()).isEqualTo(18);
        verify(authService).assertUser("Bearer token", 1L);
        verify(mapper).updateLastTicketNo(1L, 15);
        verify(summaryMapper).updateBranchTicket(2L, "KB국민은행 종로지점", 15);
    }
}
