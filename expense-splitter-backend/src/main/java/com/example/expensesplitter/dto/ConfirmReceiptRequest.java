package com.example.expensesplitter.dto;

import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.List;

public class ConfirmReceiptRequest {

    @NotNull(message = "PayerId is required")
    private Long payerId;

    private String splitType = "EQUAL"; // EQUAL, PERCENT, CUSTOM
    private Long categoryId;
    private String note;
    private List<CreateExpenseRequest.ShareLine> shares;

    public Long getPayerId() { return payerId; }
    public void setPayerId(Long payerId) { this.payerId = payerId; }

    public String getSplitType() { return splitType; }
    public void setSplitType(String splitType) { this.splitType = splitType; }

    public Long getCategoryId() { return categoryId; }
    public void setCategoryId(Long categoryId) { this.categoryId = categoryId; }

    public String getNote() { return note; }
    public void setNote(String note) { this.note = note; }

    public List<CreateExpenseRequest.ShareLine> getShares() { return shares; }
    public void setShares(List<CreateExpenseRequest.ShareLine> shares) { this.shares = shares; }
}
