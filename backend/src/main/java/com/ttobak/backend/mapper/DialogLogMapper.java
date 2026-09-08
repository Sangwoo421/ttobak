package com.ttobak.backend.mapper;

import com.ttobak.backend.domain.DialogLog;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface DialogLogMapper {
    int insert(DialogLog log);
}
