package com.ttobak.backend.service;

import java.util.ArrayList;
import java.util.List;

import com.ttobak.backend.config.NotFoundException;
import com.ttobak.backend.domain.BriefingItem;
import com.ttobak.backend.domain.BriefingResponse;
import com.ttobak.backend.domain.BriefingRow;
import com.ttobak.backend.domain.Classification;
import com.ttobak.backend.domain.Counterparty;
import com.ttobak.backend.domain.Transaction;
import com.ttobak.backend.domain.User;
import com.ttobak.backend.provider.AuthProvider;
import com.ttobak.backend.provider.TransactionProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class BriefingService {

    /** 한 번에 읽어주는 최대 건수 */
    private static final int MAX_ITEMS = 3;

    private final TransactionProvider transactions;
    private final AuthProvider auth;
    private final ClassificationService classification;

    public BriefingResponse briefing(long userId) {
        auth.assertUser(userId);
        User user = transactions.findUser(userId)
                .orElseThrow(() -> new NotFoundException("user " + userId + " not found"));

        List<Counterparty> counterparties = transactions.findCounterparties(userId);
        List<BriefingRow> rows = transactions.findUnheardNotifications(userId, MAX_ITEMS);
        int unheardTotal = transactions.countUnheardNotifications(userId);

        List<BriefingItem> items = new ArrayList<>();
        int ordinal = 1;
        for (BriefingRow row : rows) {
            Transaction tx = row.getTransaction();
            Classification c = classification.classify(tx, counterparties);
            items.add(new BriefingItem(ordinal++, row.getNotificationId(), tx, c));
        }
        return new BriefingResponse(user.getId(), user.getName(), items, Math.max(0, unheardTotal - items.size()));
    }

    public void markHeard(long notificationId) {
        if (!transactions.markNotificationHeard(notificationId)) {
            throw new NotFoundException("notification " + notificationId + " not found");
        }
    }
}
