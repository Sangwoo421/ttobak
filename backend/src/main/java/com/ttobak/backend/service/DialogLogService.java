package com.ttobak.backend.service;

import com.ttobak.backend.domain.DialogLog;
import com.ttobak.backend.mapper.DialogLogMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class DialogLogService {

    private final DialogLogMapper dialogLogMapper;

    public DialogLog save(DialogLog log) {
        dialogLogMapper.insert(log);
        return log;
    }
}
