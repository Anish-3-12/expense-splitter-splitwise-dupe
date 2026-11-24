package com.example.expensesplitter.dto;

import java.math.BigDecimal;

public class AnomalyDto {
    private Long expenseId;
    private BigDecimal amount;
    private String status; // NORMAL, UNUSUAL, REQUIRES_REVIEW, INSUFFICIENT_DATA
    private Double anomalyScore;
    private String reason;
    private String description;
    private String expenseNote;
    private String payerName;
    private String categoryName;
    private String date;
    private boolean isAnomaly;

    public AnomalyDto() {}

    public AnomalyDto(Long expenseId, BigDecimal amount, String status, Double anomalyScore, String reason) {
        this.expenseId = expenseId;
        this.amount = amount;
        this.status = status;
        this.anomalyScore = anomalyScore;
        this.reason = reason;
        this.isAnomaly = !"NORMAL".equalsIgnoreCase(status) && !"INSUFFICIENT_DATA".equalsIgnoreCase(status);
    }

    public Long getExpenseId() { return expenseId; }
    public void setExpenseId(Long expenseId) { this.expenseId = expenseId; }
    public BigDecimal getAmount() { return amount; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Double getAnomalyScore() { return anomalyScore; }
    public void setAnomalyScore(Double anomalyScore) { this.anomalyScore = anomalyScore; }
    public String getReason() { return reason; }
    public void setReason(String reason) { this.reason = reason; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public String getExpenseNote() { return expenseNote; }
    public void setExpenseNote(String expenseNote) { this.expenseNote = expenseNote; }
    public String getPayerName() { return payerName; }
    public void setPayerName(String payerName) { this.payerName = payerName; }
    public String getCategoryName() { return categoryName; }
    public void setCategoryName(String categoryName) { this.categoryName = categoryName; }
    public String getDate() { return date; }
    public void setDate(String date) { this.date = date; }
    public boolean isAnomaly() { return isAnomaly; }
    public void setAnomaly(boolean anomaly) { isAnomaly = anomaly; }
}
