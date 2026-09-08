package com.ttobak.backend.controller;

import com.ttobak.backend.domain.BriefingItem;
import com.ttobak.backend.mapper.CounterpartyMapper;
import com.ttobak.backend.mapper.TransactionMapper;
import com.ttobak.backend.domain.Counterparty;
import com.ttobak.backend.domain.Transaction;
import com.ttobak.backend.service.ClassificationService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 어르신 모드 홈과 거래내역 화면이 쓰는 조회 API.
 *
 * <p>브리핑({@code /briefing})과 다른 점: 브리핑은 "아직 안 들은 알림"만 최대 3건 주므로 한 번 들으면
 * 비어 버린다. 내역 화면은 들었든 안 들었든 최근 거래를 그대로 보여줘야 해서 별도 경로가 필요하다.
 *
 * <p>조회 전용이다. 이체를 실행하거나 잔액을 바꾸는 경로는 이 시스템에 없다.
 */
@RestController
@RequiredArgsConstructor
public class TransactionListController {

    private static final int DEFAULT_LIMIT = 10;
    private static final int MAX_LIMIT = 50;

    private final TransactionMapper transactionMapper;
    private final CounterpartyMapper counterpartyMapper;
    private final ClassificationService classificationService;

    @GetMapping("/api/users/{userId}/transactions")
    public List<BriefingItem> list(@PathVariable long userId,
                                   @RequestParam(required = false) Integer limit) {
        int size = Math.min(limit == null ? DEFAULT_LIMIT : Math.max(limit, 1), MAX_LIMIT);
        List<Transaction> transactions = transactionMapper.findRecentByUser(userId, size);
        List<Counterparty> candidates = counterpartyMapper.findByUserId(userId);

        // 브리핑 항목과 같은 모양으로 돌려준다. AI 서버가 두 경로를 같은 코드로 다룰 수 있다.
        // notification_id 는 없다. 이 화면은 알림이 아니라 거래에서 출발하기 때문이다.
        return java.util.stream.IntStream.range(0, transactions.size())
                .mapToObj(i -> {
                    Transaction tx = transactions.get(i);
                    return new BriefingItem(i + 1, null, tx, classificationService.classify(tx, candidates));
                })
                .toList();
    }
}
