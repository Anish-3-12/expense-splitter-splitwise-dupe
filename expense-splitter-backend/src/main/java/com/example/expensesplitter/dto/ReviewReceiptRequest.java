package com.example.expensesplitter.dto;

import java.math.BigDecimal;
import java.util.List;

public class ReviewReceiptRequest {
    private String merchantName;
    private String receiptDate;
    private BigDecimal totalAmount;
    private BigDecimal subtotal;
    private BigDecimal tax;
    private String currency;
    private List<ItemUpdate> items;

    public static class ItemUpdate {
        private String description;
        private BigDecimal quantity;
        private BigDecimal unitPrice;
        private BigDecimal lineTotal;

        public String getDescription() { return description; }
        public void setDescription(String description) { this.description = description; }
        public BigDecimal getQuantity() { return quantity; }
        public void setQuantity(BigDecimal quantity) { this.quantity = quantity; }
        public BigDecimal getUnitPrice() { return unitPrice; }
        public void setUnitPrice(BigDecimal unitPrice) { this.unitPrice = unitPrice; }
        public BigDecimal getLineTotal() { return lineTotal; }
        public void setLineTotal(BigDecimal lineTotal) { this.lineTotal = lineTotal; }
    }

    public String getMerchantName() { return merchantName; }
    public void setMerchantName(String merchantName) { this.merchantName = merchantName; }
    public String getReceiptDate() { return receiptDate; }
    public void setReceiptDate(String receiptDate) { this.receiptDate = receiptDate; }
    public BigDecimal getTotalAmount() { return totalAmount; }
    public void setTotalAmount(BigDecimal totalAmount) { this.totalAmount = totalAmount; }
    public BigDecimal getSubtotal() { return subtotal; }
    public void setSubtotal(BigDecimal subtotal) { this.subtotal = subtotal; }
    public BigDecimal getTax() { return tax; }
    public void setTax(BigDecimal tax) { this.tax = tax; }
    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency; }
    public List<ItemUpdate> getItems() { return items; }
    public void setItems(List<ItemUpdate> items) { this.items = items; }
}
