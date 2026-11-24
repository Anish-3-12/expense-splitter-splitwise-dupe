package com.example.expensesplitter.util;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.*;

/**
 * Utility for exact financial splitting using integer paise (cents).
 * Guarantees that:
 * 1. No paise is created or destroyed due to rounding.
 * 2. Sum of allocated shares equals total expense paise exactly.
 * 3. Remainder distribution is strictly deterministic.
 */
public class SplitUtil {

    /**
     * Converts a monetary BigDecimal amount to integer paise (or cents).
     * Rejects null, zero, negative, or amounts with more than 2 decimal places.
     */
    public static long toCents(BigDecimal amount) {
        if (amount == null) {
            throw new IllegalArgumentException("Amount cannot be null");
        }
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Amount must be strictly positive");
        }
        try {
            BigDecimal scaled = amount.setScale(2, RoundingMode.UNNECESSARY);
            return scaled.movePointRight(2).longValueExact();
        } catch (ArithmeticException e) {
            throw new IllegalArgumentException("Amount cannot have more than 2 decimal places: " + amount);
        }
    }

    public static long toPaise(BigDecimal amount) {
        return toCents(amount);
    }

    /**
     * Converts integer paise (or cents) back to a 2-decimal scale BigDecimal.
     */
    public static BigDecimal centsToBigDecimal(long cents) {
        return new BigDecimal(cents).movePointLeft(2).setScale(2, RoundingMode.HALF_EVEN);
    }

    public static BigDecimal paiseToBigDecimal(long paise) {
        return centsToBigDecimal(paise);
    }

    /**
     * EQUAL split: deterministic distribution of leftover paise to the first N userIds (sorted ascending).
     * Invariant: SUM(allocated) == totalCents.
     */
    public static Map<Long, Long> allocateEqual(long totalCents, List<Long> userIds) {
        if (totalCents <= 0) {
            throw new IllegalArgumentException("Total amount must be strictly positive");
        }
        if (userIds == null || userIds.isEmpty()) {
            throw new IllegalArgumentException("At least one participant is required for equal split");
        }

        // Deduplicate while preserving deterministic ascending sort order
        Set<Long> unique = new TreeSet<>(userIds);
        List<Long> sorted = new ArrayList<>(unique);
        int n = sorted.size();

        long base = totalCents / n;
        long remainder = totalCents % n;

        Map<Long, Long> res = new LinkedHashMap<>();
        for (int i = 0; i < n; i++) {
            long add = (i < remainder) ? 1L : 0L;
            res.put(sorted.get(i), base + add);
        }
        return res;
    }

    /**
     * PERCENT split: Largest remainder method (Hamilton-Hare method).
     * Invariant: SUM(allocated) == totalCents.
     */
    public static Map<Long, Long> allocatePercent(long totalCents, Map<Long, BigDecimal> percentMap) {
        if (totalCents <= 0) {
            throw new IllegalArgumentException("Total amount must be strictly positive");
        }
        if (percentMap == null || percentMap.isEmpty()) {
            throw new IllegalArgumentException("Percent map cannot be empty");
        }

        BigDecimal totalCentsBD = new BigDecimal(totalCents);
        BigDecimal sumPercents = BigDecimal.ZERO;

        for (Map.Entry<Long, BigDecimal> e : percentMap.entrySet()) {
            Long uid = e.getKey();
            if (uid == null) {
                throw new IllegalArgumentException("User ID cannot be null in percent shares");
            }
            BigDecimal percent = e.getValue();
            if (percent == null || percent.compareTo(BigDecimal.ZERO) < 0) {
                throw new IllegalArgumentException("Percent must be non-negative for user " + uid);
            }
            sumPercents = sumPercents.add(percent);
        }

        if (sumPercents.setScale(2, RoundingMode.HALF_EVEN).compareTo(new BigDecimal("100.00")) != 0) {
            throw new IllegalArgumentException("Percentages must sum to exactly 100.00. Current sum: " + sumPercents);
        }

        Map<Long, Long> floors = new LinkedHashMap<>();
        Map<Long, BigDecimal> fractions = new HashMap<>();
        long sumFloors = 0L;

        for (Map.Entry<Long, BigDecimal> e : percentMap.entrySet()) {
            Long uid = e.getKey();
            BigDecimal percent = e.getValue();
            BigDecimal exact = totalCentsBD.multiply(percent).divide(new BigDecimal(100), 10, RoundingMode.HALF_EVEN);
            long floor = exact.setScale(0, RoundingMode.DOWN).longValue();
            BigDecimal fraction = exact.subtract(new BigDecimal(floor));
            floors.put(uid, floor);
            fractions.put(uid, fraction);
            sumFloors += floor;
        }

        long remainder = totalCents - sumFloors;

        // Sort by fractional part descending, tie-break by userId ascending
        List<Long> users = new ArrayList<>(fractions.keySet());
        users.sort((a, b) -> {
            int cmp = fractions.get(b).compareTo(fractions.get(a));
            if (cmp != 0) return cmp;
            return a.compareTo(b);
        });

        Map<Long, Long> result = new LinkedHashMap<>();
        for (Long uid : users) {
            result.put(uid, floors.get(uid));
        }

        for (int i = 0; i < remainder; i++) {
            Long uid = users.get(i % users.size());
            result.put(uid, result.get(uid) + 1L);
        }

        return result;
    }

    /**
     * CUSTOM split: amountMap (userId -> BigDecimal amount).
     * Validates that all amounts are non-negative and sum equals totalCents.
     * Invariant: SUM(allocated) == totalCents.
     */
    public static Map<Long, Long> allocateCustom(long totalCents, Map<Long, BigDecimal> amountMap) {
        if (totalCents <= 0) {
            throw new IllegalArgumentException("Total amount must be strictly positive");
        }
        if (amountMap == null || amountMap.isEmpty()) {
            throw new IllegalArgumentException("Custom shares map cannot be empty");
        }

        Map<Long, Long> res = new LinkedHashMap<>();
        long sum = 0L;
        for (Map.Entry<Long, BigDecimal> e : amountMap.entrySet()) {
            Long uid = e.getKey();
            if (uid == null) {
                throw new IllegalArgumentException("User ID cannot be null in custom shares");
            }
            BigDecimal val = e.getValue();
            if (val == null) {
                throw new IllegalArgumentException("Amount cannot be null for user " + uid);
            }
            if (val.compareTo(BigDecimal.ZERO) < 0) {
                throw new IllegalArgumentException("Share amount cannot be negative for user " + uid);
            }
            long paise = toCents(val);
            res.put(uid, paise);
            sum += paise;
        }

        if (sum != totalCents) {
            throw new IllegalArgumentException(
                    "Custom shares do not sum to total amount (in paise/cents). expected=" + totalCents + " actual=" + sum);
        }
        return res;
    }
}
