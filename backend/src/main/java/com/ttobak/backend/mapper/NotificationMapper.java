package com.ttobak.backend.mapper;

import java.util.List;

import com.ttobak.backend.domain.BriefingRow;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface NotificationMapper {
    /** heard_at IS NULL AND 뮤트 제외 → occurred_at DESC → LIMIT */
    List<BriefingRow> findUnheard(@Param("userId") long userId, @Param("limit") int limit);

    int countUnheard(@Param("userId") long userId);

    int markHeard(@Param("id") long notificationId);
}
