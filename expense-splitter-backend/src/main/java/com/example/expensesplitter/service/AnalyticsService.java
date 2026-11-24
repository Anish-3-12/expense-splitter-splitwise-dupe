package com.example.expensesplitter.service;

import com.example.expensesplitter.client.AiServiceClient;
import com.example.expensesplitter.dto.*;
import com.example.expensesplitter.entity.*;
import com.example.expensesplitter.repository.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class AnalyticsService {

    private static final Logger log = LoggerFactory.getLogger(AnalyticsService.class);

    private final GroupRepository groupRepository;
    private final MembershipRepository membershipRepository;
    private final ExpenseRepository expenseRepository;
    private final ExpenseCategoryRepository categoryRepository;
    private final ExpenseService expenseService;
    private final AiServiceClient aiServiceClient;

    private static final DateTimeFormatter MONTH_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM").withZone(ZoneId.systemDefault());

    public AnalyticsService(
            GroupRepository groupRepository,
            MembershipRepository membershipRepository,
            ExpenseRepository expenseRepository,
            ExpenseCategoryRepository categoryRepository,
            ExpenseService expenseService,
            AiServiceClient aiServiceClient
    ) {
        this.groupRepository = groupRepository;
        this.membershipRepository = membershipRepository;
        this.expenseRepository = expenseRepository;
        this.categoryRepository = categoryRepository;
        this.expenseService = expenseService;
        this.aiServiceClient = aiServiceClient;
    }

    private void validateGroupMembership(Group group, User user) {
        membershipRepository.findByGroupAndUser(group, user)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.FORBIDDEN, "Not a group member"));
    }

    @Transactional(readOnly = true)
    public GroupAnalyticsDto getGroupAnalytics(Long groupId, User requester) {
        Group group = groupRepository.findById(groupId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Group not found"));
        validateGroupMembership(group, requester);

        List<Expense> expenses = Optional.ofNullable(expenseRepository.findByGroupId(groupId)).orElse(Collections.emptyList());
        List<Membership> memberships = membershipRepository.findByGroup_Id(groupId);

        GroupAnalyticsDto dto = new GroupAnalyticsDto();
        dto.setGroupId(groupId);

        if (expenses.isEmpty()) {
            dto.setTotalExpenditure(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_EVEN));
            dto.setMonthlyExpenditure(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_EVEN));
            dto.setAverageExpense(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_EVEN));
            dto.setExpenseCount(0);
            return dto;
        }

        BigDecimal total = expenses.stream()
                .map(e -> e.getAmount() != null ? e.getAmount() : BigDecimal.ZERO)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .setScale(2, RoundingMode.HALF_EVEN);
        dto.setTotalExpenditure(total);

        // Current month expenditure
        String currentMonth = MONTH_FORMATTER.format(Instant.now());
        BigDecimal monthly = expenses.stream()
                .filter(e -> e.getCreatedAt() != null && MONTH_FORMATTER.format(e.getCreatedAt()).equals(currentMonth))
                .map(e -> e.getAmount() != null ? e.getAmount() : BigDecimal.ZERO)
                .reduce(BigDecimal.ZERO, BigDecimal::add)
                .setScale(2, RoundingMode.HALF_EVEN);
        dto.setMonthlyExpenditure(monthly);

        dto.setExpenseCount(expenses.size());
        dto.setAverageExpense(total.divide(new BigDecimal(expenses.size()), 2, RoundingMode.HALF_EVEN));

        // Category breakdown
        Map<String, BigDecimal> catTotals = new HashMap<>();
        Map<String, Integer> catCounts = new HashMap<>();
        Map<String, String> catIcons = new HashMap<>();

        for (Expense e : expenses) {
            String catName = (e.getCategory() != null) ? e.getCategory().getName() : "Other";
            String catIcon = (e.getCategory() != null && e.getCategory().getIcon() != null) ? e.getCategory().getIcon() : "category";
            BigDecimal amt = e.getAmount() != null ? e.getAmount() : BigDecimal.ZERO;

            catTotals.put(catName, catTotals.getOrDefault(catName, BigDecimal.ZERO).add(amt));
            catCounts.put(catName, catCounts.getOrDefault(catName, 0) + 1);
            catIcons.put(catName, catIcon);
        }

        List<GroupAnalyticsDto.CategorySpendingDto> catList = new ArrayList<>();
        for (Map.Entry<String, BigDecimal> entry : catTotals.entrySet()) {
            double pct = total.compareTo(BigDecimal.ZERO) > 0
                    ? entry.getValue().multiply(new BigDecimal(100)).divide(total, 1, RoundingMode.HALF_EVEN).doubleValue()
                    : 0.0;
            catList.add(new GroupAnalyticsDto.CategorySpendingDto(
                    entry.getKey(),
                    catIcons.get(entry.getKey()),
                    entry.getValue().setScale(2, RoundingMode.HALF_EVEN),
                    pct,
                    catCounts.get(entry.getKey())
            ));
        }
        catList.sort((a, b) -> b.getTotalAmount().compareTo(a.getTotalAmount()));
        dto.setCategoryBreakdown(catList);

        // Member-wise spending
        Map<Long, BigDecimal> paidMap = new HashMap<>();
        Map<Long, BigDecimal> shareMap = new HashMap<>();

        for (Expense e : expenses) {
            if (e.getPayer() != null) {
                Long pid = e.getPayer().getId();
                paidMap.put(pid, paidMap.getOrDefault(pid, BigDecimal.ZERO).add(e.getAmount()));
            }
            if (e.getShares() != null) {
                for (ExpenseShare s : e.getShares()) {
                    if (s.getUser() != null) {
                        Long uid = s.getUser().getId();
                        shareMap.put(uid, shareMap.getOrDefault(uid, BigDecimal.ZERO).add(s.getShareAmount()));
                    }
                }
            }
        }

        List<BalanceDto> netBalances = expenseService.computeBalances(groupId, requester);
        Map<Long, BigDecimal> netMap = netBalances.stream().collect(Collectors.toMap(BalanceDto::getUserId, BalanceDto::getNetBalance));

        List<GroupAnalyticsDto.MemberSpendingDto> memberList = new ArrayList<>();
        for (Membership m : memberships) {
            Long uid = m.getUser().getId();
            BigDecimal paid = paidMap.getOrDefault(uid, BigDecimal.ZERO).setScale(2, RoundingMode.HALF_EVEN);
            BigDecimal share = shareMap.getOrDefault(uid, BigDecimal.ZERO).setScale(2, RoundingMode.HALF_EVEN);
            BigDecimal net = netMap.getOrDefault(uid, BigDecimal.ZERO).setScale(2, RoundingMode.HALF_EVEN);
            double pct = total.compareTo(BigDecimal.ZERO) > 0
                    ? paid.multiply(new BigDecimal(100)).divide(total, 2, RoundingMode.HALF_EVEN).doubleValue()
                    : 0.0;
            memberList.add(new GroupAnalyticsDto.MemberSpendingDto(
                    uid,
                    m.getUser().getName(),
                    paid,
                    share,
                    net,
                    pct
            ));
        }
        dto.setMemberSpending(memberList);

        // Monthly trends
        Map<String, BigDecimal> monthMap = new TreeMap<>();
        Map<String, Integer> monthCountMap = new HashMap<>();
        for (Expense e : expenses) {
            String m = e.getCreatedAt() != null ? MONTH_FORMATTER.format(e.getCreatedAt()) : currentMonth;
            monthMap.put(m, monthMap.getOrDefault(m, BigDecimal.ZERO).add(e.getAmount()));
            monthCountMap.put(m, monthCountMap.getOrDefault(m, 0) + 1);
        }

        List<GroupAnalyticsDto.MonthlyTrendDto> trendList = new ArrayList<>();
        for (Map.Entry<String, BigDecimal> entry : monthMap.entrySet()) {
            trendList.add(new GroupAnalyticsDto.MonthlyTrendDto(
                    entry.getKey(),
                    entry.getValue().setScale(2, RoundingMode.HALF_EVEN),
                    monthCountMap.get(entry.getKey())
            ));
        }
        dto.setMonthlyTrends(trendList);

        Map<Long, Expense> expenseMap = expenses.stream().collect(Collectors.toMap(Expense::getId, e -> e));

        // Anomaly Detection via AI microservice
        try {
            List<Map<String, Object>> expPoints = expenses.stream().map(e -> {
                Map<String, Object> p = new HashMap<>();
                p.put("expense_id", e.getId());
                p.put("amount", e.getAmount() != null ? e.getAmount().doubleValue() : 0.0);
                p.put("payer_id", e.getPayer() != null ? e.getPayer().getId() : 0);
                p.put("category", e.getCategory() != null ? e.getCategory().getName() : "Other");
                p.put("created_at", e.getCreatedAt() != null ? e.getCreatedAt().toString() : "");
                p.put("note", e.getNote() != null ? e.getNote() : "");
                return p;
            }).collect(Collectors.toList());

            Map<String, Object> aiAnomalies = aiServiceClient.detectAnomalies(groupId, expPoints);
            if (aiAnomalies != null && aiAnomalies.get("method_used") != null) {
                dto.setAnomalyMethod(aiAnomalies.get("method_used").toString());
            } else {
                dto.setAnomalyMethod(expenses.size() >= 10 ? "ISOLATION_FOREST" : (expenses.size() >= 5 ? "STATISTICAL_IQR" : "INSUFFICIENT_DATA"));
            }
            List<Map<String, Object>> results = (List<Map<String, Object>>) (aiAnomalies != null ? aiAnomalies.get("results") : null);
            if (results != null) {
                List<AnomalyDto> anomalyDtos = new ArrayList<>();
                for (Map<String, Object> r : results) {
                    String status = (String) r.get("status");
                    boolean isAnomaly = "UNUSUAL".equalsIgnoreCase(status) || "REQUIRES_REVIEW".equalsIgnoreCase(status);
                    if (isAnomaly) {
                        Long expId = Long.valueOf(r.get("expense_id").toString());
                        Expense exp = expenseMap.get(expId);
                        AnomalyDto anom = new AnomalyDto();
                        anom.setExpenseId(expId);
                        anom.setAmount(new BigDecimal(r.get("amount").toString()));
                        anom.setStatus(status);
                        anom.setAnomalyScore(Double.valueOf(r.get("anomaly_score").toString()));
                        anom.setReason((String) r.get("reason"));
                        anom.setAnomaly(true);
                        if (exp != null) {
                            String note = exp.getNote() != null ? exp.getNote() : "Expense #" + expId;
                            anom.setDescription(note);
                            anom.setExpenseNote(note);
                            anom.setPayerName(exp.getPayer() != null ? exp.getPayer().getName() : "Unknown");
                            anom.setCategoryName(exp.getCategory() != null ? exp.getCategory().getName() : "General");
                            anom.setDate(exp.getCreatedAt() != null ? exp.getCreatedAt().toString() : "");
                        }
                        anomalyDtos.add(anom);
                    }
                }
                dto.setAnomalies(anomalyDtos);
            }
        } catch (Exception e) {
            log.warn("Anomaly detection call failed: {}", e.getMessage());
        }

        return dto;
    }

    @Transactional(readOnly = true)
    public UserDashboardDto getUserDashboard(User user) {
        UserDashboardDto dto = new UserDashboardDto();
        dto.setUserId(user.getId());
        dto.setUserName(user.getName());

        List<Membership> memberships = membershipRepository.findByUser(user);
        dto.setTotalGroupsCount(memberships.size());

        BigDecimal totalPaid = BigDecimal.ZERO;
        BigDecimal totalOwedToUser = BigDecimal.ZERO;
        BigDecimal totalUserOwes = BigDecimal.ZERO;

        List<GroupDto> groupDtos = new ArrayList<>();
        List<ExpenseDto> allUserExpenses = new ArrayList<>();

        for (Membership m : memberships) {
            Group g = m.getGroup();
            int memberCount = membershipRepository.findByGroup_Id(g.getId()).size();
            groupDtos.add(new GroupDto(g.getId(), g.getName(), g.getOwner().getId(), memberCount));

            try {
                List<BalanceDto> balances = expenseService.computeBalances(g.getId(), user);
                for (BalanceDto b : balances) {
                    if (b.getUserId().equals(user.getId())) {
                        BigDecimal net = b.getNetBalance();
                        if (net.compareTo(BigDecimal.ZERO) > 0) {
                            totalOwedToUser = totalOwedToUser.add(net);
                        } else if (net.compareTo(BigDecimal.ZERO) < 0) {
                            totalUserOwes = totalUserOwes.add(net.abs());
                        }
                    }
                }

                List<ExpenseDto> gExpenses = expenseService.listGroupExpenses(g.getId(), user);
                allUserExpenses.addAll(gExpenses);

                for (ExpenseDto ed : gExpenses) {
                    if (ed.getPayerId().equals(user.getId())) {
                        totalPaid = totalPaid.add(ed.getAmount());
                    }
                }
            } catch (Exception e) {
                log.warn("Could not compute dashboard stats for group {}: {}", g.getId(), e.getMessage());
            }
        }

        dto.setTotalSpent(totalPaid.setScale(2, RoundingMode.HALF_EVEN));
        dto.setTotalOwedToUser(totalOwedToUser.setScale(2, RoundingMode.HALF_EVEN));
        dto.setTotalUserOwes(totalUserOwes.setScale(2, RoundingMode.HALF_EVEN));
        dto.setNetTotalBalance(totalOwedToUser.subtract(totalUserOwes).setScale(2, RoundingMode.HALF_EVEN));
        dto.setRecentGroups(groupDtos.stream().limit(5).collect(Collectors.toList()));

        // Sort expenses by createdAt desc
        allUserExpenses.sort((a, b) -> {
            if (a.getCreatedAt() == null || b.getCreatedAt() == null) return 0;
            return b.getCreatedAt().compareTo(a.getCreatedAt());
        });
        dto.setRecentExpenses(allUserExpenses.stream().limit(8).collect(Collectors.toList()));

        return dto;
    }
}
