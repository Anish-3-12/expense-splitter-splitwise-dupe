package com.example.expensesplitter.dto;

import java.math.BigDecimal;

public class ReceiptItemDto {
    private Long id;
    private Integer lineNumber;
    private String description;
    private BigDecimal quantity;
    private BigDecimal unitPrice;
    private BigDecimal lineTotal;
    private BigDecimal confidence;
    private Boolean isAmbiguous;
    private String ambiguityReason;

    public ReceiptItemDto() {}

    public ReceiptItemDto(Long id, Integer lineNumber, String description, BigDecimal quantity, BigDecimal unitPrice, BigDecimal lineTotal, BigDecimal confidence) {
        this.id = id;
        this.lineNumber = lineNumber;
        this.description = description;
        this.quantity = quantity;
        this.unitPrice = unitPrice;
        this.lineTotal = lineTotal;
        this.confidence = confidence;
    }

    public ReceiptItemDto(Long id, Integer lineNumber, String description, BigDecimal quantity, BigDecimal unitPrice, BigDecimal lineTotal, BigDecimal confidence, Boolean isAmbiguous, String ambiguityReason) {
        this.id = id;
        this.lineNumber = lineNumber;
        this.description = description;
        this.quantity = quantity;
        this.unitPrice = unitPrice;
        this.lineTotal = lineTotal;
        this.confidence = confidence;
        this.isAmbiguous = isAmbiguous;
        this.ambiguityReason = ambiguityReason;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Integer getLineNumber() { return lineNumber; }
    public void setLineNumber(Integer lineNumber) { this.lineNumber = lineNumber; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public BigDecimal getQuantity() { return quantity; }
    public void setQuantity(BigDecimal quantity) { this.quantity = quantity; }
    public BigDecimal getUnitPrice() { return unitPrice; }
    public void setUnitPrice(BigDecimal unitPrice) { this.unitPrice = unitPrice; }
    public BigDecimal getLineTotal() { return lineTotal; }
    public void setLineTotal(BigDecimal lineTotal) { this.lineTotal = lineTotal; }
    public BigDecimal getConfidence() { return confidence; }
    public void setConfidence(BigDecimal confidence) { this.confidence = confidence; }
    public Boolean getIsAmbiguous() { return isAmbiguous; }
    public void setIsAmbiguous(Boolean isAmbiguous) { this.isAmbiguous = isAmbiguous; }
    public String getAmbiguityReason() { return ambiguityReason; }
    public void setAmbiguityReason(String ambiguityReason) { this.ambiguityReason = ambiguityReason; }
}
