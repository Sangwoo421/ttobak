package com.ttobak.backend.domain;

public record BriefingItem(
        int ordinal,
        Long notificationId,
        Transaction transaction,
        Classification classification
) {
}
