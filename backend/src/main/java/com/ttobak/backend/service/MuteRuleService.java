package com.ttobak.backend.service;

import com.ttobak.backend.config.BadRequestException;
import com.ttobak.backend.domain.MuteRule;
import com.ttobak.backend.mapper.MuteRuleMapper;
import com.ttobak.backend.provider.AuthProvider;
import com.ttobak.backend.provider.TransactionProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class MuteRuleService {

    private final MuteRuleMapper muteRuleMapper;
    private final TransactionProvider transactions;
    private final AuthProvider auth;

    public MuteRule create(MuteRule rule) {
        auth.assertUser(rule.getUserId());
        if (transactions.findUser(rule.getUserId()).isEmpty()) {
            throw new BadRequestException("unknown user_id " + rule.getUserId());
        }
        rule.setCounterpartyName(rule.getCounterpartyName().trim());
        muteRuleMapper.insert(rule);
        return rule;
    }
}
