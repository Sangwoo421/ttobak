package com.ttobak.backend.domain;

import java.util.List;

public record BriefingResponse(
        Long userId,
        String userName,
        List<BriefingItem> items,
        int remainingCount,
        // 뮤트 제외 후 heard_at IS NULL 인 알림의 총 개수(countUnheard). items 로 잘라내기 전 값이라
        // 화면 뱃지는 이 값을 봐야 한다. remainingCount = max(0, unheardCount - items.size()).
        int unheardCount
) {
}
