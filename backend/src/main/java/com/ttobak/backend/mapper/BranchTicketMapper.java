package com.ttobak.backend.mapper;

import java.util.List;

import com.ttobak.backend.domain.BankBranch;
import com.ttobak.backend.domain.BranchTicketRow;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface BranchTicketMapper {
    Long lockUser(@Param("userId") long userId);
    List<BankBranch> findActiveBranches();
    BankBranch findBranchByIdForUpdate(@Param("id") long id);
    int countWaiting(@Param("branchId") long branchId);
    int countAhead(@Param("branchId") long branchId, @Param("ticketNo") int ticketNo);
    void updateLastTicketNo(@Param("branchId") long branchId, @Param("ticketNo") int ticketNo);
    void insertTicket(BranchTicketRow ticket);
    void attachSummary(@Param("id") long id, @Param("summaryId") long summaryId);
    BranchTicketRow findTicketById(@Param("id") long id);
    BranchTicketRow findActiveTicketByUser(@Param("userId") long userId);
    int cancelTicket(@Param("id") long id);
}
