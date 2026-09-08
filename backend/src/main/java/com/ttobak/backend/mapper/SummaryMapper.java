package com.ttobak.backend.mapper;

import java.util.List;

import com.ttobak.backend.domain.CounterSummary;
import com.ttobak.backend.domain.StaffSummaryListItem;
import com.ttobak.backend.domain.SummaryItemRow;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface SummaryMapper {
    // ---- counter_summaries ----
    int insertSummary(CounterSummary summary);

    CounterSummary findById(@Param("id") long id);

    CounterSummary findByCode(@Param("code") String code);

    Integer maxTicketNo();

    int countByCode(@Param("code") String code);

    int updateStatus(@Param("id") long id, @Param("status") String status);

    List<StaffSummaryListItem> findForStaff(@Param("status") String status);

    // ---- summary_items ----
    int insertItem(SummaryItemRow item);

    List<SummaryItemRow> findItems(@Param("summaryId") long summaryId);

    SummaryItemRow findItem(@Param("summaryId") long summaryId, @Param("itemId") long itemId);

    int updateItemHandled(@Param("itemId") long itemId, @Param("handled") boolean handled);
}
