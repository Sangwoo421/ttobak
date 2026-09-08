package com.ttobak.backend.domain;

import java.util.List;

public record BriefingResponse(
        Long userId,
        String userName,
        List<BriefingItem> items,
        int remainingCount
) {
}
