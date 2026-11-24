package com.example.expensesplitter.client;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.time.Duration;
import java.util.*;

/**
 * Client for communicating with the internal Python FastAPI AI microservice.
 * All requests authenticate with the shared X-Internal-Secret header.
 */
@Component
public class AiServiceClient {

    private static final Logger log = LoggerFactory.getLogger(AiServiceClient.class);

    private final RestTemplate restTemplate;
    private final String baseUrl;
    private final String internalSecret;

    public AiServiceClient(
            RestTemplateBuilder builder,
            @Value("${app.ai-service.url:http://localhost:8000}") String baseUrl,
            @Value("${app.ai-service.secret:splitwise-ai-internal-secret-2026}") String internalSecret,
            @Value("${app.ai-service.timeout-ms:45000}") long timeoutMs
    ) {
        this.baseUrl = baseUrl.replaceAll("/+$", "");
        this.internalSecret = internalSecret;
        this.restTemplate = builder
                .setConnectTimeout(Duration.ofMillis(5000))
                .setReadTimeout(Duration.ofMillis(timeoutMs))
                .build();
    }

    private HttpHeaders createHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("X-Internal-Secret", internalSecret);
        return headers;
    }

    public boolean isHealthy() {
        try {
            ResponseEntity<Map> resp = restTemplate.getForEntity(baseUrl + "/health", Map.class);
            return resp.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            log.warn("AI service health check failed at {}: {}", baseUrl, e.getMessage());
            return false;
        }
    }

    // 1. Receipt extraction
    public Map<String, Object> extractReceipt(String filePath, String rawOcrText, Long groupId) {
        String url = baseUrl + "/internal/v1/receipts/extract";
        Map<String, Object> body = new HashMap<>();
        if (filePath != null) body.put("file_path", filePath);
        if (rawOcrText != null) body.put("raw_ocr_text", rawOcrText);
        if (groupId != null) body.put("group_id", groupId);

        try {
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, createHeaders());
            ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);
            return response.getBody();
        } catch (Exception e) {
            log.error("Failed to extract receipt via AI service: {}", e.getMessage());
            // Fallback response so user can still manually review
            Map<String, Object> fallback = new HashMap<>();
            fallback.put("merchant", "Receipt");
            fallback.put("currency", "INR");
            fallback.put("total", 0.0);
            fallback.put("items", Collections.emptyList());
            fallback.put("warnings", List.of("AI service was unavailable. Please enter receipt items manually."));
            return fallback;
        }
    }

    // 2. Natural language split interpretation
    public Map<String, Object> interpretSplit(String instruction, List<Map<String, Object>> groupMembers, BigDecimal totalAmount, List<Map<String, Object>> items, Long payerId) {
        String url = baseUrl + "/internal/v1/expenses/interpret-split";
        Map<String, Object> body = new HashMap<>();
        body.put("instruction", instruction);
        body.put("group_members", groupMembers);
        body.put("total_amount", totalAmount != null ? totalAmount.doubleValue() : 0.0);
        body.put("items", items != null ? items : Collections.emptyList());
        if (payerId != null) body.put("payer_id", payerId);

        try {
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, createHeaders());
            ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);
            return response.getBody();
        } catch (Exception e) {
            log.error("Failed to interpret split via AI service: {}", e.getMessage());
            Map<String, Object> fallback = new HashMap<>();
            fallback.put("original_instruction", instruction);
            fallback.put("allocations", Collections.emptyList());
            fallback.put("participant_allocations", Collections.emptyList());
            fallback.put("unresolved_references", Collections.emptyList());
            fallback.put("clarification_required", true);
            fallback.put("clarification_question", "AI service is currently busy. Please choose split type manually.");
            fallback.put("confidence", 0.0);
            return fallback;
        }
    }

    // 3. Categorize expense
    public Map<String, Object> categorizeExpense(String merchant, String note, BigDecimal amount) {
        String url = baseUrl + "/internal/v1/expenses/categorize";
        Map<String, Object> body = new HashMap<>();
        if (merchant != null) body.put("merchant", merchant);
        if (note != null) body.put("note", note);
        if (amount != null) body.put("amount", amount.doubleValue());

        try {
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, createHeaders());
            ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);
            return response.getBody();
        } catch (Exception e) {
            log.warn("AI categorization failed, defaulting to 'Other': {}", e.getMessage());
            return Map.of("category", "Other", "confidence", 0.5, "method", "FALLBACK");
        }
    }

    // 4. Anomaly detection
    public Map<String, Object> detectAnomalies(Long groupId, List<Map<String, Object>> historicalExpenses) {
        String url = baseUrl + "/internal/v1/analytics/detect-anomalies";
        Map<String, Object> body = new HashMap<>();
        body.put("group_id", groupId);
        body.put("historical_expenses", historicalExpenses);

        try {
            HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, createHeaders());
            ResponseEntity<Map> response = restTemplate.postForEntity(url, entity, Map.class);
            return response.getBody();
        } catch (Exception e) {
            log.warn("Anomaly detection failed: {}", e.getMessage());
            return Map.of(
                    "results", Collections.emptyList(),
                    "method_used", "INSUFFICIENT_DATA",
                    "historical_count", historicalExpenses.size()
            );
        }
    }
}
