package com.ttobak.backend.mapper;

import com.ttobak.backend.domain.MuteRule;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface MuteRuleMapper {
    int insert(MuteRule rule);
}
