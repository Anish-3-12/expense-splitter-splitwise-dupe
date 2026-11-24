package com.example.expensesplitter.service;

import com.example.expensesplitter.dto.BalanceDto;
import com.example.expensesplitter.dto.CreateExpenseRequest;
import com.example.expensesplitter.entity.Expense;
import com.example.expensesplitter.entity.ExpenseShare;
import com.example.expensesplitter.entity.Group;
import com.example.expensesplitter.entity.Membership;
import com.example.expensesplitter.entity.User;
import com.example.expensesplitter.repository.ExpenseRepository;
import com.example.expensesplitter.repository.ExpenseShareRepository;
import com.example.expensesplitter.repository.GroupRepository;
import com.example.expensesplitter.repository.MembershipRepository;
import com.example.expensesplitter.repository.UserRepository;
import com.example.expensesplitter.util.SplitUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class ExpenseService {

    private static final Logger log = LoggerFactory.getLogger(ExpenseService.class);

    @Autowired
    private ExpenseRepository expenseRepository;

    @Autowired
    private ExpenseShareRepository expenseShareRepository;

    @Autowired
    private GroupRepository groupRepository;

    @Autowired
    private MembershipRepository membershipRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private com.example.expensesplitter.repository.SettlementRepository settlementRepository;

    @Autowired
    private com.example.expensesplitter.repository.ExpenseCategoryRepository categoryRepository;

    @Autowired(required = false)
    private com.example.expensesplitter.client.AiServiceClient aiServiceClient;

    // ---------------- CREATE EXPENSE ----------------
    @Transactional
    public Expense createExpense(Long groupId, User creator, CreateExpenseRequest req) {
        Group group = groupRepository.findById(groupId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Group not found"));

        List<Membership> memberships = membershipRepository.findByGroup_Id(group.getId());
        if (memberships == null || memberships.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Group has no members");
        }

        List<Long> memberUserIds = memberships.stream()
                .map(Membership::getUser)
                .filter(Objects::nonNull)
                .map(User::getId)
                .collect(Collectors.toList());

        if (!memberUserIds.contains(creator.getId())) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "You are not a member of this group");
        }

        User payer = userRepository.findById(req.getPayerId())
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST, "Payer not found"));
        if (!memberUserIds.contains(payer.getId())) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Payer is not a member of this group");
        }

        BigDecimal amount = req.getAmount();
        if (amount == null) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Amount is required");
        }
        amount = amount.setScale(2, RoundingMode.HALF_EVEN);

        long totalCents = SplitUtil.toCents(amount);

        String splitType = req.getSplitType() == null ? "EQUAL" : req.getSplitType().trim().toUpperCase(Locale.ROOT);
        Map<Long, Long> allocationInCents;

        switch (splitType) {
            case "EQUAL":
                List<Long> equalParticipants = memberUserIds;
                if (req.getShares() != null && !req.getShares().isEmpty()) {
                    equalParticipants = req.getShares().stream()
                            .map(CreateExpenseRequest.ShareLine::getUserId)
                            .filter(Objects::nonNull)
                            .distinct()
                            .collect(Collectors.toList());
                    if (equalParticipants.isEmpty()) {
                        throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "At least one participant required for EQUAL split");
                    }
                    for (Long participantId : equalParticipants) {
                        if (!memberUserIds.contains(participantId)) {
                            throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                                    "Participant " + participantId + " is not a member of the group");
                        }
                    }
                }
                allocationInCents = SplitUtil.allocateEqual(totalCents, equalParticipants);
                break;

            case "PERCENT":
                if (req.getShares() == null || req.getShares().isEmpty()) {
                    throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Shares required for PERCENT split");
                }
                Map<Long, BigDecimal> percentMap = new LinkedHashMap<>();
                for (CreateExpenseRequest.ShareLine sl : req.getShares()) {
                    if (sl.getUserId() == null || sl.getPercent() == null) {
                        throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                                "Each share line must include userId and percent for PERCENT split");
                    }
                    if (!memberUserIds.contains(sl.getUserId())) {
                        throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                                "User " + sl.getUserId() + " is not a member of the group");
                    }
                    percentMap.put(sl.getUserId(), sl.getPercent());
                }
                try {
                    allocationInCents = SplitUtil.allocatePercent(totalCents, percentMap);
                } catch (IllegalArgumentException ex) {
                    throw new ResponseStatusException(HttpStatus.BAD_REQUEST, ex.getMessage());
                }
                break;

            case "CUSTOM":
                if (req.getShares() == null || req.getShares().isEmpty()) {
                    throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Shares required for CUSTOM split");
                }
                Map<Long, BigDecimal> amountMap = new LinkedHashMap<>();
                for (CreateExpenseRequest.ShareLine sl : req.getShares()) {
                    if (sl.getUserId() == null || sl.getAmount() == null) {
                        throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                                "Each share line must include userId and amount for CUSTOM split");
                    }
                    if (!memberUserIds.contains(sl.getUserId())) {
                        throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                                "User " + sl.getUserId() + " is not a member of the group");
                    }
                    amountMap.put(sl.getUserId(), sl.getAmount().setScale(2, RoundingMode.HALF_EVEN));
                }
                try {
                    allocationInCents = SplitUtil.allocateCustom(totalCents, amountMap);
                } catch (IllegalArgumentException ex) {
                    throw new ResponseStatusException(HttpStatus.BAD_REQUEST, ex.getMessage());
                }
                break;

            default:
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Unknown splitType: " + splitType);
        }

        Expense expense = new Expense();
        expense.setGroup(group);
        expense.setCreatedBy(creator);
        expense.setPayer(payer);
        expense.setAmount(amount);
        String currency = req.getCurrency() == null ? "INR" : req.getCurrency().trim();
        if (!"INR".equalsIgnoreCase(currency)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Unsupported currency: '" + currency + "'. The expense ledger only supports INR (₹).");
        }
        expense.setCurrency("INR");
        expense.setSplitType(splitType);
        expense.setNote(req.getNote());

        if (req.getCategoryId() != null && categoryRepository != null) {
            categoryRepository.findById(req.getCategoryId()).ifPresent(expense::setCategory);
        } else if (categoryRepository != null && aiServiceClient != null) {
            try {
                Map<String, Object> catRes = aiServiceClient.categorizeExpense(null, req.getNote(), req.getAmount());
                String catName = (String) catRes.get("category");
                if (catName != null) {
                    categoryRepository.findByNameIgnoreCase(catName).ifPresent(expense::setCategory);
                }
            } catch (Exception ex) {
                log.info("Auto-categorization error: {}", ex.getMessage());
            }
        }

        if (req.getItems() != null && !req.getItems().isEmpty()) {
            for (CreateExpenseRequest.ItemLine il : req.getItems()) {
                com.example.expensesplitter.entity.ExpenseItem ei = new com.example.expensesplitter.entity.ExpenseItem();
                ei.setDescription(il.getDescription());
                ei.setQuantity(il.getQuantity() != null ? il.getQuantity() : BigDecimal.ONE);
                ei.setUnitPrice(il.getUnitPrice() != null ? il.getUnitPrice() : BigDecimal.ZERO);
                ei.setLineTotal(il.getLineTotal() != null ? il.getLineTotal() : ei.getUnitPrice());
                expense.addItem(ei);
            }
        }

        for (Map.Entry<Long, Long> entry : allocationInCents.entrySet()) {
            Long uid = entry.getKey();
            long cents = entry.getValue();

            if (!memberUserIds.contains(uid)) {
                throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                        "Shared user is not a member of the group: " + uid);
            }
            User u = userRepository.findById(uid)
                    .orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST,
                            "User not found in shares: " + uid));

            ExpenseShare share = new ExpenseShare();
            share.setUser(u);
            share.setShareAmount(SplitUtil.centsToBigDecimal(cents));
            expense.addShare(share);
        }

        return expenseRepository.save(expense);
    }

    // ---------------- LIST EXPENSES ----------------
    public List<com.example.expensesplitter.dto.ExpenseDto> listGroupExpenses(Long groupId, User requester) {
        List<Membership> memberships = membershipRepository.findByGroup_Id(groupId);
        if (memberships == null) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Group not found or no memberships");
        }
        List<Long> memberUserIds = memberships.stream()
                .map(Membership::getUser)
                .filter(Objects::nonNull)
                .map(User::getId)
                .collect(Collectors.toList());

        if (!memberUserIds.contains(requester.getId())) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Not a group member");
        }

        List<Expense> expenses = expenseRepository.findByGroupId(groupId);
        List<com.example.expensesplitter.dto.ExpenseDto> dtos = new ArrayList<>();
        for (Expense e : expenses) {
            com.example.expensesplitter.dto.ExpenseDto dto = new com.example.expensesplitter.dto.ExpenseDto();
            dto.setId(e.getId());
            dto.setGroupId(e.getGroup().getId());
            dto.setCreatedById(e.getCreatedBy().getId());
            dto.setPayerId(e.getPayer().getId());
            if (e.getPayer() != null) {
                dto.setPayerName(e.getPayer().getName());
            }
            dto.setAmount(e.getAmount());
            dto.setCurrency(e.getCurrency());
            dto.setSplitType(e.getSplitType());
            dto.setNote(e.getNote());
            if (e.getCategory() != null) {
                dto.setCategoryId(e.getCategory().getId());
                dto.setCategoryName(e.getCategory().getName());
                dto.setCategoryIcon(e.getCategory().getIcon());
            }
            dto.setCreatedAt(e.getCreatedAt());

            List<com.example.expensesplitter.dto.ExpenseDto.ShareDto> shareDtos = new ArrayList<>();
            for (ExpenseShare s : e.getShares()) {
                com.example.expensesplitter.dto.ExpenseDto.ShareDto sd = new com.example.expensesplitter.dto.ExpenseDto.ShareDto();
                sd.setUserId(s.getUser().getId());
                sd.setShareAmount(s.getShareAmount());
                sd.setSettled(s.isSettled());
                shareDtos.add(sd);
            }
            dto.setShares(shareDtos);
            dtos.add(dto);
        }
        return dtos;
    }

    // ---------------- COMPUTE BALANCES ----------------
    public List<BalanceDto> computeBalances(Long groupId, User requester) {
        log.info("Computing balances for group {} by user {}", groupId, requester.getId());

        List<Membership> memberships = membershipRepository.findByGroup_Id(groupId);
        if (memberships == null || memberships.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Group not found or has no members");
        }

        List<Long> memberUserIds = memberships.stream()
                .map(m -> m.getUser().getId())
                .toList();

        if (!memberUserIds.contains(requester.getId())) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Not a group member");
        }

        Map<Long, BigDecimal> balances = new HashMap<>();
        for (Membership m : memberships) {
            balances.put(m.getUser().getId(), BigDecimal.ZERO);
        }

        // Expenses
        List<Expense> expenses = Optional.ofNullable(expenseRepository.findByGroupId(groupId)).orElse(Collections.emptyList());
        for (Expense expense : expenses) {
            if (expense.getPayer() == null) continue; // defensive
            Long payerId = expense.getPayer().getId();
            BigDecimal amount = expense.getAmount() != null ? expense.getAmount() : BigDecimal.ZERO;
            balances.put(payerId, balances.getOrDefault(payerId, BigDecimal.ZERO).add(amount));

            // NOTE: expense.getShares() is a Set<ExpenseShare> in your domain; use emptySet() here
            for (ExpenseShare share : Optional.ofNullable(expense.getShares()).orElse(Collections.emptySet())) {
                if (share.getUser() == null) continue;
                Long uid = share.getUser().getId();
                BigDecimal shareAmt = share.getShareAmount() != null ? share.getShareAmount() : BigDecimal.ZERO;
                balances.put(uid, balances.getOrDefault(uid, BigDecimal.ZERO).subtract(shareAmt));
            }
        }

        // Settlements: when 'fromUser' pays 'toUser', fromUser's debt decreases (add to net balance)
        // and toUser's credit decreases (subtract from net balance).
        List<com.example.expensesplitter.entity.Settlement> settlements =
                Optional.ofNullable(settlementRepository.findByGroup_Id(groupId)).orElse(Collections.emptyList());
        for (com.example.expensesplitter.entity.Settlement s : settlements) {
            if (s.getFromUser() == null || s.getToUser() == null) continue;
            Long from = s.getFromUser().getId();
            Long to = s.getToUser().getId();
            BigDecimal amt = s.getAmount() != null ? s.getAmount() : BigDecimal.ZERO;
            balances.put(from, balances.getOrDefault(from, BigDecimal.ZERO).add(amt));
            balances.put(to, balances.getOrDefault(to, BigDecimal.ZERO).subtract(amt));
        }

        List<BalanceDto> result = new ArrayList<>();
        for (Membership m : memberships) {
            Long uid = m.getUser().getId();
            String name = m.getUser().getName();
            BigDecimal net = balances.getOrDefault(uid, BigDecimal.ZERO).setScale(2, RoundingMode.HALF_EVEN);
            result.add(new BalanceDto(uid, name, net));
        }

        log.info("Computed balances: {}", result);
        return result;
    }
}
