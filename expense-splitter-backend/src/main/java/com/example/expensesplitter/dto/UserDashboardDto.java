package com.example.expensesplitter.dto;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

public class UserDashboardDto {
    private Long userId;
    private String userName;
    private BigDecimal totalSpent;
    private BigDecimal totalOwedToUser;
    private BigDecimal totalUserOwes;
    private BigDecimal netTotalBalance;
    private int totalGroupsCount;
    private List<GroupDto> recentGroups = new ArrayList<>();
    private List<ExpenseDto> recentExpenses = new ArrayList<>();
    private List<GroupAnalyticsDto.CategorySpendingDto> topCategories = new ArrayList<>();

    public UserDashboardDto() {}

    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public String getUserName() { return userName; }
    public void setUserName(String userName) { this.userName = userName; }
    public BigDecimal getTotalSpent() { return totalSpent; }
    public void setTotalSpent(BigDecimal totalSpent) { this.totalSpent = totalSpent; }
    public BigDecimal getTotalOwedToUser() { return totalOwedToUser; }
    public void setTotalOwedToUser(BigDecimal totalOwedToUser) { this.totalOwedToUser = totalOwedToUser; }
    public BigDecimal getTotalUserOwes() { return totalUserOwes; }
    public void setTotalUserOwes(BigDecimal totalUserOwes) { this.totalUserOwes = totalUserOwes; }
    public BigDecimal getNetTotalBalance() { return netTotalBalance; }
    public void setNetTotalBalance(BigDecimal netTotalBalance) { this.netTotalBalance = netTotalBalance; }
    public int getTotalGroupsCount() { return totalGroupsCount; }
    public void setTotalGroupsCount(int totalGroupsCount) { this.totalGroupsCount = totalGroupsCount; }
    public List<GroupDto> getRecentGroups() { return recentGroups; }
    public void setRecentGroups(List<GroupDto> recentGroups) { this.recentGroups = recentGroups; }
    public List<ExpenseDto> getRecentExpenses() { return recentExpenses; }
    public void setRecentExpenses(List<ExpenseDto> recentExpenses) { this.recentExpenses = recentExpenses; }
    public List<GroupAnalyticsDto.CategorySpendingDto> getTopCategories() { return topCategories; }
    public void setTopCategories(List<GroupAnalyticsDto.CategorySpendingDto> topCategories) { this.topCategories = topCategories; }
}
