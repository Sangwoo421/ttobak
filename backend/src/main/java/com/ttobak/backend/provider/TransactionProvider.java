package com.ttobak.backend.provider;

import java.util.List;
import java.util.Optional;

import com.ttobak.backend.domain.BriefingRow;
import com.ttobak.backend.domain.Counterparty;
import com.ttobak.backend.domain.Transaction;
import com.ttobak.backend.domain.User;

/**
 * 외부 경계: 은행 앱의 사용자·계좌·거래·알림 데이터 공급자.
 * 시연에서는 시드 DB(MyBatis)로 구현하고, 실제 뱅킹 앱에 임베드될 때 이 인터페이스만 교체한다.
 * 조회와 "들었음" 기록만 있다. 잔액·거래를 바꾸는 메서드는 정의하지 않는다.
 */
public interface TransactionProvider {

    Optional<User> findUser(long userId);

    List<Counterparty> findCounterparties(long userId);

    Optional<Counterparty> findCounterparty(long counterpartyId);

    /** 거래가 속한 계좌의 소유자가 등록한 상대 목록 */
    List<Counterparty> findCounterpartiesByAccount(long accountId);

    Optional<Transaction> findTransaction(long transactionId);

    /** 미청취 + 뮤트 제외 + 최근순 */
    List<BriefingRow> findUnheardNotifications(long userId, int limit);

    int countUnheardNotifications(long userId);

    /** @return 갱신된 행이 있으면 true */
    boolean markNotificationHeard(long notificationId);
}
