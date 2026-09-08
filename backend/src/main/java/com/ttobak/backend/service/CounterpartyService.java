package com.ttobak.backend.service;

import java.util.List;

import com.ttobak.backend.domain.Counterparty;
import com.ttobak.backend.domain.CounterpartyDto;
import com.ttobak.backend.provider.AuthProvider;
import com.ttobak.backend.provider.TransactionProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class CounterpartyService {

    private final TransactionProvider transactions;
    private final AuthProvider auth;

    public List<CounterpartyDto> list(long userId) {
        auth.assertUser(userId);
        return transactions.findCounterparties(userId).stream().map(Counterparty::toDto).toList();
    }
}
