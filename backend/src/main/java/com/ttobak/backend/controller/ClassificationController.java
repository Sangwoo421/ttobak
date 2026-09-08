package com.ttobak.backend.controller;

import com.ttobak.backend.domain.Classification;
import com.ttobak.backend.service.ClassificationService;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "classification")
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class ClassificationController {

    private final ClassificationService classificationService;

    @GetMapping("/transactions/{transactionId}/classification")
    public Classification classify(@PathVariable long transactionId) {
        return classificationService.classify(transactionId);
    }
}
