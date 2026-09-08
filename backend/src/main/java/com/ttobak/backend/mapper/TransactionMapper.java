package com.ttobak.backend.mapper;

import com.ttobak.backend.domain.Transaction;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/** 조회 전용. 잔액을 바꾸거나 거래를 만드는 SQL 은 존재하지 않는다. */
@Mapper
public interface TransactionMapper {
    Transaction findById(@Param("id") long id);
}
