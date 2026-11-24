# Financial Calculation Engine Audit & Verification Report

**Product**: Splitwise AI (Intelligent Expense Management & Financial Insights Platform)
**Author**: Autonomous Full-Stack Architecture & Engineering Team
**Date**: November 2026
**Status**: VERIFIED & PRODUCTION READY

---

## 1. Executive Summary

A comprehensive financial logic audit was conducted across the expense splitting, remainder reconciliation, and balance settlement engine.

### Critical Vulnerabilities & Defects Identified:
1. **Critical Settlement Debt Inversion Bug in `ExpenseService.java:275-285`**:
   - *Defect*: When processing a recorded settlement where Member A paid Member B an amount $X$, the balance computation code executed:
     ```java
     // DEFECTIVE ORIGINAL:
     bFrom.setNetBalance(bFrom.getNetBalance().subtract(s.getAmount()));
     bTo.setNetBalance(bTo.getNetBalance().add(s.getAmount()));
     ```
   - *Impact*: In Splitwise/Ledger accounting, when a debtor (someone who owes money, with a negative net balance) pays a creditor, their debt is *reduced* (their balance moves closer to 0, which means **adding** the paid amount). The previous implementation **subtracted** the amount from the payer, doubling their recorded debt!
   - *Resolution*: Corrected to:
     ```java
     // VERIFIED CORRECTION:
     bFrom.setNetBalance(bFrom.getNetBalance().add(s.getAmount()));
     bTo.setNetBalance(bTo.getNetBalance().subtract(s.getAmount()));
     ```

2. **Rounding & Remainder Loss in `SplitUtil.java`**:
   - *Defect*: Floating-point / inexact division arithmetic allowed sub-cent/paise remainders to be dropped or misallocated.
   - *Resolution*: Implemented deterministic integer-paise (cents) arithmetic where:
     $$\text{totalPaise} = \text{round}(\text{totalAmount} \times 100)$$
     $$\text{baseSharePaise} = \lfloor \text{totalPaise} / N \rfloor$$
     $$\text{remainderPaise} = \text{totalPaise} \pmod N$$
     The remaining $k$ paise are deterministically allocated to the first $k$ participants (1 paise each). This strictly guarantees that:
     $$\sum_{i=1}^{N} \text{share}_i \equiv \text{totalAmount} \quad \text{to 0.000000 precision}$$

3. **Validation Guards**:
   - Added validation against negative amounts, zero amounts, scale exceeding 2 decimal places, missing participants, duplicate user IDs, and percentages deviating from $100.00\%$.

---

## 2. Invariants & Proofs

### Invariant 1: Conservation of Money
For any expense $E$ of amount $A$ split among $N$ participants with shares $S_1, S_2, \dots, S_N$:
$$\sum_{i=1}^{N} S_i = A$$
No currency units are created or destroyed due to rounding.

### Invariant 2: Net-Zero Balance Invariant
For any group $G$ with members $M_1, M_2, \dots, M_K$ and net balances $B(M_j)$:
$$\sum_{j=1}^{K} B(M_j) = 0.00$$
This holds invariant across all operations:
- **Creating an expense**: Payer is credited $A - S_{\text{payer}}$; each participant $i$ is debited $S_i$.
  $$\Delta B(\text{payer}) + \sum_{i \neq \text{payer}} \Delta B(i) = (A - S_{\text{payer}}) - \sum_{i \neq \text{payer}} S_i = A - \sum_{i=1}^N S_i = 0$$
- **Recording a settlement**: Payer pays $X$ to recipient:
  $$\Delta B(\text{payer}) = +X, \quad \Delta B(\text{recipient}) = -X$$
  $$\Delta B(\text{payer}) + \Delta B(\text{recipient}) = (+X) + (-X) = 0$$
Since initial balances start at $0.00$ and every state transition preserves the sum, $\sum B(M_j) \equiv 0.00$ at all times.

---

## 3. Test Coverage & Edge Cases

The following unit and property-based test suites were added to `ExpenseServiceTest.java` and verified:

| Test Case | Description | Result |
| :--- | :--- | :--- |
| `testEqualSplit_ThreeWayOddCent` | ₹100 split 3 ways: ₹33.34, ₹33.33, ₹33.33 | **PASSED** (Sum = ₹100.00) |
| `testEqualSplit_OneCent` | ₹0.01 split 2 ways: ₹0.01 to first, ₹0.00 to second | **PASSED** (Sum = ₹0.01) |
| `testEqualSplit_LargeGroup` | ₹1,000,000.00 split across 17 participants | **PASSED** (Exact paise match) |
| `testEqualSplit_SubsetMembers` | Split equally among a subset of group members | **PASSED** |
| `testPercentSplit_Exact100` | Percentages summing to 100% | **PASSED** |
| `testPercentSplit_UnevenDecimals` | 33.33%, 33.33%, 33.34% on ₹1000.00 | **PASSED** (Sum = ₹1000.00) |
| `testPercentSplit_SumNot100_ThrowsException` | 60% + 30% = 90% | **PASSED** (Rejected) |
| `testCustomSplit_ExactTotal` | Custom amounts matching total | **PASSED** |
| `testCustomSplit_Mismatch_ThrowsException` | Custom amounts totaling ₹95 for ₹100 expense | **PASSED** (Rejected) |
| `testSettlement_NetBalanceZeroInvariant` | Multiple expenses and settlements | **PASSED** ($\sum \text{balances} = 0$) |
| `testSettlement_ReducesDebtCorrectly` | Payer debt verified to reduce towards zero | **PASSED** |
| `testNegativeOrZeroAmount_ThrowsException` | ₹0.00 or -₹50.00 expense creation | **PASSED** (Rejected) |
