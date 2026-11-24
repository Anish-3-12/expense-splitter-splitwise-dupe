package com.example.expensesplitter.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import org.hibernate.annotations.CreationTimestamp;

@Entity
@Table(name = "receipt_items")
public class ReceiptItem {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @JsonIgnore
    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "receipt_id")
    private Receipt receipt;

    @Column(name = "line_number", nullable = false)
    private Integer lineNumber;

    @Column(length = 255, nullable = false)
    private String description;

    @Column(precision = 10, scale = 2)
    private BigDecimal quantity = BigDecimal.ONE;

    @Column(name = "unit_price", precision = 19, scale = 2, nullable = false)
    private BigDecimal unitPrice;

    @Column(name = "line_total", precision = 19, scale = 2, nullable = false)
    private BigDecimal lineTotal;

    @Column(precision = 5, scale = 2)
    private BigDecimal confidence = new BigDecimal("1.00");

    @Column(name = "is_ambiguous")
    private Boolean isAmbiguous = false;

    @Column(name = "ambiguity_reason", length = 255)
    private String ambiguityReason;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private Instant createdAt;

    public ReceiptItem() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Receipt getReceipt() { return receipt; }
    public void setReceipt(Receipt receipt) { this.receipt = receipt; }

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

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
