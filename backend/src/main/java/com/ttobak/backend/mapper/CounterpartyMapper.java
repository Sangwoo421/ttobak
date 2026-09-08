package com.ttobak.backend.mapper;

import java.util.List;

import com.ttobak.backend.domain.Counterparty;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface CounterpartyMapper {
    Counterparty findById(@Param("id") long id);

    List<Counterparty> findByUserId(@Param("userId") long userId);

    /** 거래의 계좌 소유자가 등록한 상대 목록 (규칙 엔진 R3 memo_pattern 대조용) */
    List<Counterparty> findByAccountId(@Param("accountId") long accountId);
}
