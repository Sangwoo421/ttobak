package com.ttobak.backend.controller;

import java.util.List;

import com.ttobak.backend.domain.CounterpartyDto;
import com.ttobak.backend.service.CounterpartyService;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "counterparties")
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class CounterpartyController {

    private final CounterpartyService counterpartyService;

    @GetMapping("/users/{userId}/counterparties")
    public List<CounterpartyDto> list(@PathVariable long userId) {
        return counterpartyService.list(userId);
    }
}
