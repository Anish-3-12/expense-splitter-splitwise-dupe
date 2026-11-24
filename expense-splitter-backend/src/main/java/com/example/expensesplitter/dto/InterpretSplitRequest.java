package com.example.expensesplitter.dto;

import jakarta.validation.constraints.NotBlank;
import java.math.BigDecimal;
import java.util.List;

public class InterpretSplitRequest {

    @NotBlank(message = "Natural language instruction is required")
    private String instruction;

    private BigDecimal totalAmount;
    private Long payerId;
    private List<ItemDraft> items;

    public static class ItemDraft {
        private String id;
        private String description;
        private BigDecimal amount;

        public String getId() { return id; }
        public void setId(String id) { this.id = id; }
        public String getDescription() { return description; }
        public void setDescription(String description) { this.description = description; }
        public BigDecimal getAmount() { return amount; }
        public void setAmount(BigDecimal amount) { this.amount = amount; }
    }

    public String getInstruction() { return instruction; }
    public void setInstruction(String instruction) { this.instruction = instruction; }
    public BigDecimal getTotalAmount() { return totalAmount; }
    public void setTotalAmount(BigDecimal totalAmount) { this.totalAmount = totalAmount; }
    public Long getPayerId() { return payerId; }
    public void setPayerId(Long payerId) { this.payerId = payerId; }
    public List<ItemDraft> getItems() { return items; }
    public void setItems(List<ItemDraft> items) { this.items = items; }
}
