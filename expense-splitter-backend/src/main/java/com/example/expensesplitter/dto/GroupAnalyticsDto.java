package com.example.expensesplitter.dto;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

public class GroupAnalyticsDto {
    private Long groupId;
    private BigDecimal totalExpenditure;
    private BigDecimal monthlyExpenditure;
    private BigDecimal averageExpense;
    private int expenseCount;
    private List<CategorySpendingDto> categoryBreakdown = new ArrayList<>();
    private List<MemberSpendingDto> memberSpending = new ArrayList<>();
    private List<MonthlyTrendDto> monthlyTrends = new ArrayList<>();
    private List<AnomalyDto> anomalies = new ArrayList<>();
    private String anomalyMethod;

    public static class CategorySpendingDto {
        private String category;
        private String icon;
        private BigDecimal totalAmount;
        private Double percentage;
        private int transactionCount;

        public CategorySpendingDto() {}
        public CategorySpendingDto(String category, String icon, BigDecimal totalAmount, Double percentage, int transactionCount) {
            this.category = category;
            this.icon = icon;
            this.totalAmount = totalAmount;
            this.percentage = percentage;
            this.transactionCount = transactionCount;
        }

        public String getCategory() { return category; }
        public void setCategory(String category) { this.category = category; }
        public String getIcon() { return icon; }
        public void setIcon(String icon) { this.icon = icon; }
        public BigDecimal getTotalAmount() { return totalAmount; }
        public void setTotalAmount(BigDecimal totalAmount) { this.totalAmount = totalAmount; }
        public Double getPercentage() { return percentage; }
        public void setPercentage(Double percentage) { this.percentage = percentage; }
        public int getTransactionCount() { return transactionCount; }
        public void setTransactionCount(int transactionCount) { this.transactionCount = transactionCount; }
    }

    public static class MemberSpendingDto {
        private Long userId;
        private String userName;
        private BigDecimal totalPaid;
        private BigDecimal totalShare;
        private BigDecimal netBalance;
        private Double percentage;

        public MemberSpendingDto() {}
        public MemberSpendingDto(Long userId, String userName, BigDecimal totalPaid, BigDecimal totalShare, BigDecimal netBalance) {
            this(userId, userName, totalPaid, totalShare, netBalance, 0.0);
        }

        public MemberSpendingDto(Long userId, String userName, BigDecimal totalPaid, BigDecimal totalShare, BigDecimal netBalance, Double percentage) {
            this.userId = userId;
            this.userName = userName;
            this.totalPaid = totalPaid;
            this.totalShare = totalShare;
            this.netBalance = netBalance;
            this.percentage = percentage;
        }

        public Long getUserId() { return userId; }
        public void setUserId(Long userId) { this.userId = userId; }
        public String getUserName() { return userName; }
        public void setUserName(String userName) { this.userName = userName; }
        public BigDecimal getTotalPaid() { return totalPaid; }
        public void setTotalPaid(BigDecimal totalPaid) { this.totalPaid = totalPaid; }
        public BigDecimal getTotalShare() { return totalShare; }
        public void setTotalShare(BigDecimal totalShare) { this.totalShare = totalShare; }
        public BigDecimal getNetBalance() { return netBalance; }
        public void setNetBalance(BigDecimal netBalance) { this.netBalance = netBalance; }
        public Double getPercentage() { return percentage; }
        public void setPercentage(Double percentage) { this.percentage = percentage; }
    }

    public static class MonthlyTrendDto {
        private String month; // e.g. "2026-03"
        private BigDecimal amount;
        private int count;

        public MonthlyTrendDto() {}
        public MonthlyTrendDto(String month, BigDecimal amount, int count) {
            this.month = month;
            this.amount = amount;
            this.count = count;
        }

        public String getMonth() { return month; }
        public void setMonth(String month) { this.month = month; }
        public BigDecimal getAmount() { return amount; }
        public void setAmount(BigDecimal amount) { this.amount = amount; }
        public int getCount() { return count; }
        public void setCount(int count) { this.count = count; }
    }

    public Long getGroupId() { return groupId; }
    public void setGroupId(Long groupId) { this.groupId = groupId; }
    public BigDecimal getTotalExpenditure() { return totalExpenditure; }
    public void setTotalExpenditure(BigDecimal totalExpenditure) { this.totalExpenditure = totalExpenditure; }
    public BigDecimal getTotalSpending() { return totalExpenditure; }
    public void setTotalSpending(BigDecimal totalSpending) { this.totalExpenditure = totalSpending; }
    public BigDecimal getMonthlyExpenditure() { return monthlyExpenditure; }
    public void setMonthlyExpenditure(BigDecimal monthlyExpenditure) { this.monthlyExpenditure = monthlyExpenditure; }
    public BigDecimal getAverageExpense() { return averageExpense; }
    public void setAverageExpense(BigDecimal averageExpense) { this.averageExpense = averageExpense; }
    public int getExpenseCount() { return expenseCount; }
    public void setExpenseCount(int expenseCount) { this.expenseCount = expenseCount; }
    public List<CategorySpendingDto> getCategoryBreakdown() { return categoryBreakdown; }
    public void setCategoryBreakdown(List<CategorySpendingDto> categoryBreakdown) { this.categoryBreakdown = categoryBreakdown; }
    public List<MemberSpendingDto> getMemberSpending() { return memberSpending; }
    public void setMemberSpending(List<MemberSpendingDto> memberSpending) { this.memberSpending = memberSpending; }
    public List<MonthlyTrendDto> getMonthlyTrends() { return monthlyTrends; }
    public void setMonthlyTrends(List<MonthlyTrendDto> monthlyTrends) { this.monthlyTrends = monthlyTrends; }
    public List<MonthlyTrendDto> getMonthlySpending() { return monthlyTrends; }
    public void setMonthlySpending(List<MonthlyTrendDto> monthlySpending) { this.monthlyTrends = monthlySpending; }
    public List<AnomalyDto> getAnomalies() { return anomalies; }
    public void setAnomalies(List<AnomalyDto> anomalies) { this.anomalies = anomalies; }
    public String getAnomalyMethod() { return anomalyMethod; }
    public void setAnomalyMethod(String anomalyMethod) { this.anomalyMethod = anomalyMethod; }
}
