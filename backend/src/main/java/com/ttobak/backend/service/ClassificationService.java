package com.ttobak.backend.service;

import java.util.List;

import com.ttobak.backend.config.BusinessException;
import com.ttobak.backend.config.ErrorCode;
import com.ttobak.backend.domain.Classification;
import com.ttobak.backend.domain.Counterparty;
import com.ttobak.backend.domain.Transaction;
import com.ttobak.backend.provider.TransactionProvider;
import com.ttobak.backend.rules.ClassificationRuleEngine;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ClassificationService {

    private final TransactionProvider transactions;
    private final ClassificationRuleEngine engine;

    public Classification classify(long transactionId) {
        Transaction tx = transactions.findTransaction(transactionId)
                .orElseThrow(() -> new BusinessException(ErrorCode.TRANSACTION_NOT_FOUND, "transaction " + transactionId + " not found"));
        return classify(tx, transactions.findCounterpartiesByAccount(tx.getAccountId()));
    }

    /** @param candidates 거래 계좌 소유자의 등록 상대 전체 */
    public Classification classify(Transaction tx, List<Counterparty> candidates) {
        Counterparty registered = null;
        if (tx.getCounterpartyId() != null) {
            registered = candidates.stream()
                    .filter(c -> tx.getCounterpartyId().equals(c.getId()))
                    .findFirst()
                    .orElseGet(() -> transactions.findCounterparty(tx.getCounterpartyId()).orElse(null));
        }
        return engine.classify(tx, registered, candidates);
    }
}
