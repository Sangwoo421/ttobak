package com.ttobak.backend.provider;

import java.util.List;
import java.util.Optional;

import com.ttobak.backend.domain.BriefingRow;
import com.ttobak.backend.domain.Counterparty;
import com.ttobak.backend.domain.Transaction;
import com.ttobak.backend.domain.User;
import com.ttobak.backend.mapper.CounterpartyMapper;
import com.ttobak.backend.mapper.NotificationMapper;
import com.ttobak.backend.mapper.TransactionMapper;
import com.ttobak.backend.mapper.UserMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

/** 시연용 구현: docs/contracts/seed-data.sql 로 채운 MySQL 을 MyBatis 로 읽는다. */
@Component
@RequiredArgsConstructor
public class DemoTransactionProvider implements TransactionProvider {

    private final UserMapper userMapper;
    private final CounterpartyMapper counterpartyMapper;
    private final TransactionMapper transactionMapper;
    private final NotificationMapper notificationMapper;

    @Override
    public Optional<User> findUser(long userId) {
        return Optional.ofNullable(userMapper.findById(userId));
    }

    @Override
    public List<Counterparty> findCounterparties(long userId) {
        return counterpartyMapper.findByUserId(userId);
    }

    @Override
    public Optional<Counterparty> findCounterparty(long counterpartyId) {
        return Optional.ofNullable(counterpartyMapper.findById(counterpartyId));
    }

    @Override
    public List<Counterparty> findCounterpartiesByAccount(long accountId) {
        return counterpartyMapper.findByAccountId(accountId);
    }

    @Override
    public Optional<Transaction> findTransaction(long transactionId) {
        return Optional.ofNullable(transactionMapper.findById(transactionId));
    }

    @Override
    public List<BriefingRow> findUnheardNotifications(long userId, int limit) {
        return notificationMapper.findUnheard(userId, limit);
    }

    @Override
    public int countUnheardNotifications(long userId) {
        return notificationMapper.countUnheard(userId);
    }

    @Override
    public boolean markNotificationHeard(long notificationId) {
        return notificationMapper.markHeard(notificationId) > 0;
    }
}
