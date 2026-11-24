package com.example.expensesplitter.service;

import com.example.expensesplitter.dto.BalanceDto;
import com.example.expensesplitter.dto.CreateExpenseRequest;
import com.example.expensesplitter.entity.Expense;
import com.example.expensesplitter.entity.ExpenseShare;
import com.example.expensesplitter.entity.Group;
import com.example.expensesplitter.entity.Membership;
import com.example.expensesplitter.entity.Settlement;
import com.example.expensesplitter.entity.User;
import com.example.expensesplitter.repository.ExpenseRepository;
import com.example.expensesplitter.repository.ExpenseShareRepository;
import com.example.expensesplitter.repository.GroupRepository;
import com.example.expensesplitter.repository.MembershipRepository;
import com.example.expensesplitter.repository.SettlementRepository;
import com.example.expensesplitter.repository.UserRepository;
import com.example.expensesplitter.util.SplitUtil;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

public class ExpenseServiceTest {

    @Mock
    private ExpenseRepository expenseRepository;
    @Mock
    private ExpenseShareRepository expenseShareRepository;
    @Mock
    private GroupRepository groupRepository;
    @Mock
    private MembershipRepository membershipRepository;
    @Mock
    private UserRepository userRepository;
    @Mock
    private SettlementRepository settlementRepository;

    @InjectMocks
    private ExpenseService expenseService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    // ==========================================
    // 1. EQUAL SPLIT AUDIT & EDGE CASES
    // ==========================================

    @Test
    @DisplayName("Equal split ₹100 among 3 people: exactly 33.34, 33.33, 33.33, sum = 100.00")
    void testEqualSplitThreePeopleHundredRupees() {
        long totalPaise = 10000L; // ₹100.00
        List<Long> members = List.of(101L, 102L, 103L);
        Map<Long, Long> result = SplitUtil.allocateEqual(totalPaise, members);

        assertEquals(3, result.size());
        assertEquals(3334L, result.get(101L)); // first gets the 1 paise remainder
        assertEquals(3333L, result.get(102L));
        assertEquals(3333L, result.get(103L));

        long sum = result.values().stream().mapToLong(Long::longValue).sum();
        assertEquals(totalPaise, sum);
    }

    @Test
    @DisplayName("Equal split ₹0.01 among 2 people: 1 gets 0.01, 2 gets 0.00, sum = 0.01")
    void testEqualSplitOnePaiseTwoPeople() {
        long totalPaise = 1L; // ₹0.01
        List<Long> members = List.of(1L, 2L);
        Map<Long, Long> result = SplitUtil.allocateEqual(totalPaise, members);

        assertEquals(2, result.size());
        assertEquals(1L, result.get(1L));
        assertEquals(0L, result.get(2L));
        assertEquals(1L, result.values().stream().mapToLong(Long::longValue).sum());
    }

    @Test
    @DisplayName("Equal split ₹0.02 among 3 people: two get 1 paise, one gets 0, sum = 2")
    void testEqualSplitTwoPaiseThreePeople() {
        long totalPaise = 2L; // ₹0.02
        List<Long> members = List.of(1L, 2L, 3L);
        Map<Long, Long> result = SplitUtil.allocateEqual(totalPaise, members);

        assertEquals(1L, result.get(1L));
        assertEquals(1L, result.get(2L));
        assertEquals(0L, result.get(3L));
        assertEquals(2L, result.values().stream().mapToLong(Long::longValue).sum());
    }

    @Test
    @DisplayName("Equal split ₹0.05 among 4 people: one gets 2 paise, three get 1 paise, sum = 5")
    void testEqualSplitFivePaiseFourPeople() {
        long totalPaise = 5L; // ₹0.05
        List<Long> members = List.of(10L, 20L, 30L, 40L);
        Map<Long, Long> result = SplitUtil.allocateEqual(totalPaise, members);

        assertEquals(2L, result.get(10L));
        assertEquals(1L, result.get(20L));
        assertEquals(1L, result.get(30L));
        assertEquals(1L, result.get(40L));
        assertEquals(5L, result.values().stream().mapToLong(Long::longValue).sum());
    }

    @Test
    @DisplayName("Equal split ₹1.00 among 7 people: sum = 100 paise exactly")
    void testEqualSplitOneRupeeSevenPeople() {
        long totalPaise = 100L; // ₹1.00
        List<Long> members = List.of(1L, 2L, 3L, 4L, 5L, 6L, 7L);
        Map<Long, Long> result = SplitUtil.allocateEqual(totalPaise, members);

        assertEquals(7, result.size());
        assertEquals(100L, result.values().stream().mapToLong(Long::longValue).sum());
    }

    @Test
    @DisplayName("Equal split ₹999.99 among 6 people: sum = 99999 paise exactly")
    void testEqualSplitLargeUneven() {
        long totalPaise = 99999L; // ₹999.99
        List<Long> members = List.of(1L, 2L, 3L, 4L, 5L, 6L);
        Map<Long, Long> result = SplitUtil.allocateEqual(totalPaise, members);

        assertEquals(99999L, result.values().stream().mapToLong(Long::longValue).sum());
    }

    @Test
    @DisplayName("Equal split single participant gets 100% of amount")
    void testEqualSplitSingleParticipant() {
        long totalPaise = 5000L;
        List<Long> members = List.of(42L);
        Map<Long, Long> result = SplitUtil.allocateEqual(totalPaise, members);

        assertEquals(1, result.size());
        assertEquals(5000L, result.get(42L));
    }

    @Test
    @DisplayName("Equal split large group of 50 people reconciles exactly")
    void testEqualSplitFiftyPeople() {
        long totalPaise = 1234567L; // ₹12,345.67
        List<Long> members = new ArrayList<>();
        for (long i = 1; i <= 50; i++) members.add(i);

        Map<Long, Long> result = SplitUtil.allocateEqual(totalPaise, members);
        assertEquals(50, result.size());
        assertEquals(totalPaise, result.values().stream().mapToLong(Long::longValue).sum());
    }

    @Test
    @DisplayName("Equal split rejects zero or negative amounts")
    void testEqualSplitRejectsNonPositive() {
        assertThrows(IllegalArgumentException.class, () -> SplitUtil.allocateEqual(0L, List.of(1L, 2L)));
        assertThrows(IllegalArgumentException.class, () -> SplitUtil.allocateEqual(-500L, List.of(1L, 2L)));
    }

    @Test
    @DisplayName("Equal split rejects empty or null participant list")
    void testEqualSplitRejectsEmptyParticipants() {
        assertThrows(IllegalArgumentException.class, () -> SplitUtil.allocateEqual(1000L, null));
        assertThrows(IllegalArgumentException.class, () -> SplitUtil.allocateEqual(1000L, Collections.emptyList()));
    }

    @Test
    @DisplayName("Property-based test: Equal split for 100 randomized valid amounts and participant counts")
    void testEqualSplitRandomizedInvariants() {
        Random rng = new Random(42);
        for (int i = 0; i < 100; i++) {
            long amount = rng.nextInt(10_000_000) + 1; // 1 paise to ₹100,000.00
            int n = rng.nextInt(25) + 1; // 1 to 25 participants
            List<Long> members = new ArrayList<>();
            for (long u = 1; u <= n; u++) members.add(u);

            Map<Long, Long> result = SplitUtil.allocateEqual(amount, members);
            long sum = result.values().stream().mapToLong(Long::longValue).sum();
            assertEquals(amount, sum, "Sum must equal total for amount " + amount + " and n " + n);
        }
    }

    // ==========================================
    // 2. PERCENT SPLIT AUDIT & EDGE CASES
    // ==========================================

    @Test
    @DisplayName("Percent split: 50% / 50% on ₹10.00")
    void testPercentSplitHalfHalf() {
        long total = 1000L; // ₹10.00
        Map<Long, BigDecimal> percents = Map.of(
                1L, new BigDecimal("50.00"),
                2L, new BigDecimal("50.00")
        );
        Map<Long, Long> result = SplitUtil.allocatePercent(total, percents);
        assertEquals(500L, result.get(1L));
        assertEquals(500L, result.get(2L));
        assertEquals(1000L, result.values().stream().mapToLong(Long::longValue).sum());
    }

    @Test
    @DisplayName("Percent split: 33.33%, 33.33%, 33.34% on ₹100.00 reconciles to exactly ₹100.00")
    void testPercentSplitDecimalSumsToHundred() {
        long total = 10000L; // ₹100.00
        Map<Long, BigDecimal> percents = Map.of(
                1L, new BigDecimal("33.33"),
                2L, new BigDecimal("33.33"),
                3L, new BigDecimal("33.34")
        );
        Map<Long, Long> result = SplitUtil.allocatePercent(total, percents);
        assertEquals(10000L, result.values().stream().mapToLong(Long::longValue).sum());
    }

    @Test
    @DisplayName("Percent split: 70% / 30% on ₹0.01 (1 paise total)")
    void testPercentSplitTinyAmount() {
        long total = 1L; // 1 paise
        Map<Long, BigDecimal> percents = Map.of(
                1L, new BigDecimal("70.00"),
                2L, new BigDecimal("30.00")
        );
        Map<Long, Long> result = SplitUtil.allocatePercent(total, percents);
        assertEquals(1L, result.get(1L)); // largest fractional part gets the 1 paise
        assertEquals(0L, result.get(2L));
        assertEquals(1L, result.values().stream().mapToLong(Long::longValue).sum());
    }

    @Test
    @DisplayName("Percent split rejects percentages that do not sum to 100.00")
    void testPercentSplitRejectsInvalidSum() {
        assertThrows(IllegalArgumentException.class, () -> SplitUtil.allocatePercent(1000L, Map.of(
                1L, new BigDecimal("50.00"),
                2L, new BigDecimal("49.00")
        )));

        assertThrows(IllegalArgumentException.class, () -> SplitUtil.allocatePercent(1000L, Map.of(
                1L, new BigDecimal("60.00"),
                2L, new BigDecimal("50.00")
        )));
    }

    @Test
    @DisplayName("Percent split rejects negative percentage")
    void testPercentSplitRejectsNegative() {
        assertThrows(IllegalArgumentException.class, () -> SplitUtil.allocatePercent(1000L, Map.of(
                1L, new BigDecimal("120.00"),
                2L, new BigDecimal("-20.00")
        )));
    }

    // ==========================================
    // 3. CUSTOM SPLIT AUDIT & EDGE CASES
    // ==========================================

    @Test
    @DisplayName("Custom split: valid exact reconciliation")
    void testCustomSplitExact() {
        long total = 1000L;
        Map<Long, BigDecimal> amounts = Map.of(
                1L, new BigDecimal("4.00"),
                2L, new BigDecimal("6.00")
        );
        Map<Long, Long> result = SplitUtil.allocateCustom(total, amounts);
        assertEquals(400L, result.get(1L));
        assertEquals(600L, result.get(2L));
        assertEquals(total, result.values().stream().mapToLong(Long::longValue).sum());
    }

    @Test
    @DisplayName("Custom split rejects sum mismatch (too low or too high)")
    void testCustomSplitRejectsMismatch() {
        assertThrows(IllegalArgumentException.class, () -> SplitUtil.allocateCustom(1000L, Map.of(
                1L, new BigDecimal("4.00"),
                2L, new BigDecimal("5.00") // total 9.00 vs 10.00
        )));

        assertThrows(IllegalArgumentException.class, () -> SplitUtil.allocateCustom(1000L, Map.of(
                1L, new BigDecimal("6.00"),
                2L, new BigDecimal("5.00") // total 11.00 vs 10.00
        )));
    }

    @Test
    @DisplayName("Custom split rejects negative share amounts")
    void testCustomSplitRejectsNegativeAmount() {
        assertThrows(IllegalArgumentException.class, () -> SplitUtil.allocateCustom(1000L, Map.of(
                1L, new BigDecimal("12.00"),
                2L, new BigDecimal("-2.00")
        )));
    }

    @Test
    @DisplayName("Custom split rejects amounts with more than 2 decimal places")
    void testCustomSplitRejectsSubPaise() {
        assertThrows(IllegalArgumentException.class, () -> SplitUtil.allocateCustom(1000L, Map.of(
                1L, new BigDecimal("5.005"),
                2L, new BigDecimal("4.995")
        )));
    }

    // ==========================================
    // 4. SETTLEMENT & BALANCE INVARIANTS
    // ==========================================

    @Test
    @DisplayName("Invariant: SUM(group member net balances) == 0 after expenses and settlements")
    void testSettlementCorrectsDebtsAndInvariantsHold() {
        Long groupId = 10L;

        User alice = new User();
        alice.setId(1L);
        alice.setName("Alice");

        User bob = new User();
        bob.setId(2L);
        bob.setName("Bob");

        User charlie = new User();
        charlie.setId(3L);
        charlie.setName("Charlie");

        Group group = new Group();
        group.setId(groupId);

        Membership m1 = new Membership(); m1.setUser(alice); m1.setGroup(group);
        Membership m2 = new Membership(); m2.setUser(bob); m2.setGroup(group);
        Membership m3 = new Membership(); m3.setUser(charlie); m3.setGroup(group);

        when(membershipRepository.findByGroup_Id(groupId)).thenReturn(List.of(m1, m2, m3));

        // Expense: Alice pays ₹300, split equally between Alice, Bob, Charlie (₹100 each)
        Expense exp = new Expense();
        exp.setId(100L);
        exp.setPayer(alice);
        exp.setAmount(new BigDecimal("300.00"));
        exp.setShares(Set.of(
                createShare(alice, new BigDecimal("100.00")),
                createShare(bob, new BigDecimal("100.00")),
                createShare(charlie, new BigDecimal("100.00"))
        ));

        when(expenseRepository.findByGroupId(groupId)).thenReturn(List.of(exp));

        // Before settlement:
        // Alice paid 300, owes 100 -> net = +200.00
        // Bob paid 0, owes 100 -> net = -100.00
        // Charlie paid 0, owes 100 -> net = -100.00
        when(settlementRepository.findByGroup_Id(groupId)).thenReturn(Collections.emptyList());
        List<BalanceDto> initialBalances = expenseService.computeBalances(groupId, alice);

        Map<Long, BigDecimal> initialMap = toBalanceMap(initialBalances);
        assertEquals(new BigDecimal("200.00"), initialMap.get(1L));
        assertEquals(new BigDecimal("-100.00"), initialMap.get(2L));
        assertEquals(new BigDecimal("-100.00"), initialMap.get(3L));

        BigDecimal initialSum = initialMap.values().stream().reduce(BigDecimal.ZERO, BigDecimal::add);
        assertEquals(0, initialSum.compareTo(BigDecimal.ZERO), "Sum of net balances must be zero");

        // Now Bob settles by paying Alice ₹100.00 (from Bob to Alice)
        Settlement s1 = new Settlement();
        s1.setId(1L);
        s1.setGroup(group);
        s1.setFromUser(bob); // Bob pays
        s1.setToUser(alice);  // Alice receives
        s1.setAmount(new BigDecimal("100.00"));

        when(settlementRepository.findByGroup_Id(groupId)).thenReturn(List.of(s1));
        List<BalanceDto> postSettlement = expenseService.computeBalances(groupId, alice);
        Map<Long, BigDecimal> postMap = toBalanceMap(postSettlement);

        // Bob has paid his debt -> Bob net = 0.00
        // Alice received 100 cash -> Alice credit reduced from 200 to 100.00
        // Charlie still owes 100 -> Charlie net = -100.00
        assertEquals(new BigDecimal("100.00"), postMap.get(1L), "Alice credit should decrease to 100");
        assertEquals(new BigDecimal("0.00"), postMap.get(2L), "Bob debt should be 0.00 after full settlement");
        assertEquals(new BigDecimal("-100.00"), postMap.get(3L), "Charlie still owes 100.00");

        BigDecimal postSum = postMap.values().stream().reduce(BigDecimal.ZERO, BigDecimal::add);
        assertEquals(0, postSum.compareTo(BigDecimal.ZERO), "Sum of net balances must remain zero after settlement");
    }

    // ==========================================
    // 5. EXTENDED REGRESSION: PARTIAL, MULTIPLE & ITEM-LEVEL
    // ==========================================

    @Test
    @DisplayName("Partial and multiple settlements with zero-sum invariant at each step")
    void testPartialAndMultipleSettlements() {
        Long groupId = 11L;
        Group group = new Group();
        group.setId(groupId);

        User alice = new User(); alice.setId(1L); alice.setName("Alice");
        User bob = new User(); bob.setId(2L); bob.setName("Bob");
        User charlie = new User(); charlie.setId(3L); charlie.setName("Charlie");

        Membership m1 = new Membership(); m1.setUser(alice); m1.setGroup(group);
        Membership m2 = new Membership(); m2.setUser(bob); m2.setGroup(group);
        Membership m3 = new Membership(); m3.setUser(charlie); m3.setGroup(group);

        when(membershipRepository.findByGroup_Id(groupId)).thenReturn(List.of(m1, m2, m3));

        // Alice pays ₹600.00, split ₹200 each
        Expense exp = new Expense();
        exp.setId(101L);
        exp.setPayer(alice);
        exp.setAmount(new BigDecimal("600.00"));
        exp.setShares(Set.of(
                createShare(alice, new BigDecimal("200.00")),
                createShare(bob, new BigDecimal("200.00")),
                createShare(charlie, new BigDecimal("200.00"))
        ));
        when(expenseRepository.findByGroupId(groupId)).thenReturn(List.of(exp));

        // Step 1: Bob pays partial settlement ₹75.00 to Alice
        Settlement s1 = new Settlement();
        s1.setId(1L); s1.setGroup(group); s1.setFromUser(bob); s1.setToUser(alice);
        s1.setAmount(new BigDecimal("75.00"));

        when(settlementRepository.findByGroup_Id(groupId)).thenReturn(List.of(s1));
        Map<Long, BigDecimal> map1 = toBalanceMap(expenseService.computeBalances(groupId, alice));
        assertEquals(new BigDecimal("325.00"), map1.get(1L)); // 400 - 75
        assertEquals(new BigDecimal("-125.00"), map1.get(2L)); // -200 + 75
        assertEquals(new BigDecimal("-200.00"), map1.get(3L));
        assertEquals(0, map1.values().stream().reduce(BigDecimal.ZERO, BigDecimal::add).compareTo(BigDecimal.ZERO));

        // Step 2: Bob pays remaining partial settlement ₹125.00 to Alice
        Settlement s2 = new Settlement();
        s2.setId(2L); s2.setGroup(group); s2.setFromUser(bob); s2.setToUser(alice);
        s2.setAmount(new BigDecimal("125.00"));

        when(settlementRepository.findByGroup_Id(groupId)).thenReturn(List.of(s1, s2));
        Map<Long, BigDecimal> map2 = toBalanceMap(expenseService.computeBalances(groupId, alice));
        assertEquals(new BigDecimal("200.00"), map2.get(1L));
        assertEquals(new BigDecimal("0.00"), map2.get(2L)); // Bob fully settled
        assertEquals(new BigDecimal("-200.00"), map2.get(3L));
        assertEquals(0, map2.values().stream().reduce(BigDecimal.ZERO, BigDecimal::add).compareTo(BigDecimal.ZERO));

        // Step 3: Charlie pays partial settlement ₹100.00 to Alice
        Settlement s3 = new Settlement();
        s3.setId(3L); s3.setGroup(group); s3.setFromUser(charlie); s3.setToUser(alice);
        s3.setAmount(new BigDecimal("100.00"));

        when(settlementRepository.findByGroup_Id(groupId)).thenReturn(List.of(s1, s2, s3));
        Map<Long, BigDecimal> map3 = toBalanceMap(expenseService.computeBalances(groupId, alice));
        assertEquals(new BigDecimal("100.00"), map3.get(1L));
        assertEquals(new BigDecimal("0.00"), map3.get(2L));
        assertEquals(new BigDecimal("-100.00"), map3.get(3L));
        assertEquals(0, map3.values().stream().reduce(BigDecimal.ZERO, BigDecimal::add).compareTo(BigDecimal.ZERO));
    }

    @Test
    @DisplayName("Repeated settlement operations do not drift balance precision")
    void testRepeatedSettlementsStability() {
        Long groupId = 12L;
        Group group = new Group();
        group.setId(groupId);

        User u1 = new User(); u1.setId(1L); u1.setName("User 1");
        User u2 = new User(); u2.setId(2L); u2.setName("User 2");

        Membership m1 = new Membership(); m1.setUser(u1); m1.setGroup(group);
        Membership m2 = new Membership(); m2.setUser(u2); m2.setGroup(group);

        when(membershipRepository.findByGroup_Id(groupId)).thenReturn(List.of(m1, m2));

        // Expense: u1 pays ₹10.00, split ₹5.00 each
        Expense exp = new Expense();
        exp.setId(102L);
        exp.setPayer(u1);
        exp.setAmount(new BigDecimal("10.00"));
        exp.setShares(Set.of(createShare(u1, new BigDecimal("5.00")), createShare(u2, new BigDecimal("5.00"))));
        when(expenseRepository.findByGroupId(groupId)).thenReturn(List.of(exp));

        // 5 settlements of ₹1.00 each from u2 to u1
        List<Settlement> settlements = new ArrayList<>();
        for (long s = 1; s <= 5; s++) {
            Settlement set = new Settlement();
            set.setId(s); set.setGroup(group); set.setFromUser(u2); set.setToUser(u1);
            set.setAmount(new BigDecimal("1.00"));
            settlements.add(set);
        }

        when(settlementRepository.findByGroup_Id(groupId)).thenReturn(settlements);
        Map<Long, BigDecimal> balances = toBalanceMap(expenseService.computeBalances(groupId, u1));

        assertEquals(new BigDecimal("0.00"), balances.get(1L));
        assertEquals(new BigDecimal("0.00"), balances.get(2L));
        assertEquals(0, balances.values().stream().reduce(BigDecimal.ZERO, BigDecimal::add).compareTo(BigDecimal.ZERO));
    }

    @Test
    @DisplayName("Item-level allocation: sum of item shares strictly matches total item price in paise")
    void testItemLevelAllocationExactSum() {
        // Item 1: ₹45.50 split equally among 3 users
        long itemPaise = 4550L;
        List<Long> participants = List.of(10L, 20L, 30L);
        Map<Long, Long> itemShares = SplitUtil.allocateEqual(itemPaise, participants);

        assertEquals(1517L, itemShares.get(10L)); // 4550 / 3 = 1516 r 2 -> first two get 1517
        assertEquals(1517L, itemShares.get(20L));
        assertEquals(1516L, itemShares.get(30L));
        assertEquals(itemPaise, itemShares.values().stream().mapToLong(Long::longValue).sum());
    }

    private ExpenseShare createShare(User user, BigDecimal amount) {
        ExpenseShare share = new ExpenseShare();
        share.setUser(user);
        share.setShareAmount(amount);
        return share;
    }

    private Map<Long, BigDecimal> toBalanceMap(List<BalanceDto> dtos) {
        Map<Long, BigDecimal> map = new HashMap<>();
        for (BalanceDto b : dtos) {
            map.put(b.getUserId(), b.getNetBalance());
        }
        return map;
    }
}
