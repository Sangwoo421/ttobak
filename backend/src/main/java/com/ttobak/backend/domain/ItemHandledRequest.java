package com.ttobak.backend.domain;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

/** PATCH /api/staff/summaries/{id}/items/{item_id} 요청 본문 */
@Data
public class ItemHandledRequest {
    @NotNull
    private Boolean handled;
}
