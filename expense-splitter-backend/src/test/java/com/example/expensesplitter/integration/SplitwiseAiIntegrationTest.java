package com.example.expensesplitter.integration;

import com.example.expensesplitter.dto.ConfirmReceiptRequest;
import com.example.expensesplitter.dto.ReviewReceiptRequest;
import com.example.expensesplitter.entity.Receipt;
import com.example.expensesplitter.repository.ReceiptRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@AutoConfigureTestDatabase
public class SplitwiseAiIntegrationTest {

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;
    @Autowired ReceiptRepository receiptRepository;

    private String registerAndLogin(String name, String email, String password) throws Exception {
        mvc.perform(post("/api/auth/register").contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of("name", name, "email", email, "password", password))))
                .andExpect(status().isOk());

        var loginResp = mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of("email", email, "password", password))))
                .andExpect(status().isOk())
                .andReturn();

        return "Bearer " + mapper.readTree(loginResp.getResponse().getContentAsString()).get("token").asText();
    }

    @Test
    void testGroupLevelAuthorization_NonMemberForbidden() throws Exception {
        String aliceToken = registerAndLogin("Alice Auth", "alice.auth@test.com", "pass123");
        String eveToken = registerAndLogin("Eve Intruder", "eve.intruder@test.com", "pass123");

        // Alice creates group
        var groupResp = mvc.perform(post("/api/groups").header("Authorization", aliceToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of("name", "Alice Private Group"))))
                .andExpect(status().isOk())
                .andReturn();
        Long groupId = mapper.readTree(groupResp.getResponse().getContentAsString()).get("id").asLong();

        // Eve (non-member) attempts to view group details -> should be forbidden or not found
        mvc.perform(get("/api/groups/" + groupId).header("Authorization", eveToken))
                .andExpect(status().isForbidden());

        // Eve attempts to add expense to Alice's group -> should be forbidden
        mvc.perform(post("/api/groups/" + groupId + "/expenses").header("Authorization", eveToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of("amount", 50.0, "payerId", 2, "splitType", "EQUAL"))))
                .andExpect(status().isForbidden());
    }

    @Test
    void testSettlementRecordingAndBalanceInvariant() throws Exception {
        String userAToken = registerAndLogin("Settler A", "settler.a@test.com", "pass123");
        registerAndLogin("Settler B", "settler.b@test.com", "pass123");

        // User A creates group
        var gResp = mvc.perform(post("/api/groups").header("Authorization", userAToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of("name", "Settlement Circle"))))
                .andExpect(status().isOk()).andReturn();
        Long groupId = mapper.readTree(gResp.getResponse().getContentAsString()).get("id").asLong();

        // Add B to group
        mvc.perform(post("/api/groups/" + groupId + "/members").header("Authorization", userAToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of("email", "settler.b@test.com", "role", "MEMBER"))))
                .andExpect(status().isOk());

        // Get members to retrieve exact user IDs
        var membersResp = mvc.perform(get("/api/groups/" + groupId).header("Authorization", userAToken))
                .andExpect(status().isOk()).andReturn();
        var members = mapper.readTree(membersResp.getResponse().getContentAsString()).get("members");
        Long idA = members.get(0).get("userId").asLong();
        Long idB = members.get(1).get("userId").asLong();

        // A creates an expense of ₹200 split equally (₹100 each)
        mvc.perform(post("/api/groups/" + groupId + "/expenses").header("Authorization", userAToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of(
                        "amount", 200.0,
                        "payerId", idA,
                        "splitType", "EQUAL",
                        "note", "Groceries"
                ))))
                .andExpect(status().isOk());

        // Check balances: A should have +100, B should have -100
        var balResp1 = mvc.perform(get("/api/groups/" + groupId + "/balances").header("Authorization", userAToken))
                .andExpect(status().isOk()).andReturn();
        var balNodes1 = mapper.readTree(balResp1.getResponse().getContentAsString());
        double sum1 = 0.0;
        for (var n : balNodes1) {
            sum1 += n.get("netBalance").asDouble();
        }
        assertThat(Math.abs(sum1)).isLessThan(0.01);

        // B records settlement of ₹100 to A (from B to A)
        mvc.perform(post("/api/groups/" + groupId + "/settlements").header("Authorization", userAToken)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of(
                        "fromUserId", idB,
                        "toUserId", idA,
                        "amount", 100.0,
                        "note", "Paid via UPI"
                ))))
                .andExpect(status().isOk());

        // Check balances after settlement: both should now be 0.00
        var balResp2 = mvc.perform(get("/api/groups/" + groupId + "/balances").header("Authorization", userAToken))
                .andExpect(status().isOk()).andReturn();
        var balNodes2 = mapper.readTree(balResp2.getResponse().getContentAsString());
        double sum2 = 0.0;
        for (var n : balNodes2) {
            double bal = n.get("netBalance").asDouble();
            assertThat(Math.abs(bal)).isLessThan(0.01);
            sum2 += bal;
        }
        assertThat(Math.abs(sum2)).isLessThan(0.01);
    }

    @Test
    void testReceiptUploadReviewAndIdempotentConfirmation() throws Exception {
        String token = registerAndLogin("Receipt Owner", "receipt.owner@test.com", "pass123");

        // Create group
        var gResp = mvc.perform(post("/api/groups").header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of("name", "Receipt Group"))))
                .andExpect(status().isOk()).andReturn();
        Long groupId = mapper.readTree(gResp.getResponse().getContentAsString()).get("id").asLong();

        // 1. Upload receipt
        MockMultipartFile file = new MockMultipartFile(
                "file", "bill.jpg", "image/jpeg", "fake receipt image bytes".getBytes()
        );
        var uploadResp = mvc.perform(multipart("/api/groups/" + groupId + "/receipts")
                .file(file)
                .header("Authorization", token))
                .andExpect(status().isOk())
                .andReturn();
        Long receiptId = mapper.readTree(uploadResp.getResponse().getContentAsString()).get("id").asLong();
        assertThat(receiptId).isNotNull();

        // 2. Review receipt line items
        ReviewReceiptRequest reviewReq = new ReviewReceiptRequest();
        reviewReq.setMerchantName("Toit Brewpub");
        reviewReq.setReceiptDate("2026-11-18");
        reviewReq.setSubtotal(new BigDecimal("1500.00"));
        reviewReq.setTax(BigDecimal.ZERO);
        reviewReq.setTotalAmount(new BigDecimal("1500.00"));
        reviewReq.setCurrency("INR");

        ReviewReceiptRequest.ItemUpdate item1 = new ReviewReceiptRequest.ItemUpdate();
        item1.setDescription("Craft Beer");
        item1.setQuantity(new BigDecimal("2"));
        item1.setUnitPrice(new BigDecimal("400.00"));
        item1.setLineTotal(new BigDecimal("800.00"));

        ReviewReceiptRequest.ItemUpdate item2 = new ReviewReceiptRequest.ItemUpdate();
        item2.setDescription("Nachos");
        item2.setQuantity(new BigDecimal("1"));
        item2.setUnitPrice(new BigDecimal("700.00"));
        item2.setLineTotal(new BigDecimal("700.00"));

        reviewReq.setItems(List.of(item1, item2));

        mvc.perform(put("/api/groups/" + groupId + "/receipts/" + receiptId + "/review")
                .header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(reviewReq)))
                .andExpect(status().isOk());

        // 3. Confirm receipt -> creates expense
        var ownerProfile = mvc.perform(get("/api/auth/me").header("Authorization", token))
                .andExpect(status().isOk()).andReturn();
        Long ownerUserId = mapper.readTree(ownerProfile.getResponse().getContentAsString()).get("id").asLong();

        ConfirmReceiptRequest confirmReq = new ConfirmReceiptRequest();
        confirmReq.setPayerId(ownerUserId);
        confirmReq.setSplitType("EQUAL");
        confirmReq.setNote("Toit Dinner");

        var confirmResp1 = mvc.perform(post("/api/groups/" + groupId + "/receipts/" + receiptId + "/confirm")
                .header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(confirmReq)))
                .andExpect(status().isOk())
                .andReturn();
        Long expenseId1 = mapper.readTree(confirmResp1.getResponse().getContentAsString()).get("id").asLong();
        assertThat(expenseId1).isNotNull();

        // 4. Confirm receipt AGAIN (Idempotency check) -> must reject duplicate confirmation with HTTP 409 CONFLICT!
        mvc.perform(post("/api/groups/" + groupId + "/receipts/" + receiptId + "/confirm")
                .header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(confirmReq)))
                .andExpect(status().isConflict());
    }

    @Test
    void testConcurrentReceiptConfirmation() throws Exception {
        String token = registerAndLogin("Concurrent User", "concurrent.user@test.com", "pass123");

        var groupResp = mvc.perform(post("/api/groups").header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of("name", "Concurrency Group", "description", "Testing concurrency"))))
                .andExpect(status().isOk()).andReturn();
        Long groupId = mapper.readTree(groupResp.getResponse().getContentAsString()).get("id").asLong();

        MockMultipartFile file = new MockMultipartFile(
                "file", "bill_concurrent.jpg", "image/jpeg", "concurrent receipt bytes".getBytes()
        );
        var uploadResp = mvc.perform(multipart("/api/groups/" + groupId + "/receipts")
                .file(file)
                .header("Authorization", token))
                .andExpect(status().isOk())
                .andReturn();
        Long receiptId = mapper.readTree(uploadResp.getResponse().getContentAsString()).get("id").asLong();

        ReviewReceiptRequest reviewReq = new ReviewReceiptRequest();
        reviewReq.setMerchantName("Concurrency Cafe");
        reviewReq.setSubtotal(new BigDecimal("500.00"));
        reviewReq.setTax(BigDecimal.ZERO);
        reviewReq.setTotalAmount(new BigDecimal("500.00"));
        reviewReq.setCurrency("INR");
        mvc.perform(put("/api/groups/" + groupId + "/receipts/" + receiptId + "/review")
                .header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(reviewReq)))
                .andExpect(status().isOk());

        var ownerProfile = mvc.perform(get("/api/auth/me").header("Authorization", token))
                .andExpect(status().isOk()).andReturn();
        Long ownerUserId = mapper.readTree(ownerProfile.getResponse().getContentAsString()).get("id").asLong();

        ConfirmReceiptRequest confirmReq = new ConfirmReceiptRequest();
        confirmReq.setPayerId(ownerUserId);
        confirmReq.setSplitType("EQUAL");
        confirmReq.setNote("Concurrent Confirmation Test");
        String jsonPayload = mapper.writeValueAsString(confirmReq);

        int threadCount = 4;
        ExecutorService executor = Executors.newFixedThreadPool(threadCount);
        CountDownLatch startLatch = new CountDownLatch(1);
        CountDownLatch doneLatch = new CountDownLatch(threadCount);

        AtomicInteger successCount = new AtomicInteger(0);
        AtomicInteger conflictCount = new AtomicInteger(0);

        for (int i = 0; i < threadCount; i++) {
            executor.submit(() -> {
                try {
                    startLatch.await();
                    var res = mvc.perform(post("/api/groups/" + groupId + "/receipts/" + receiptId + "/confirm")
                            .header("Authorization", token)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(jsonPayload))
                            .andReturn();
                    int status = res.getResponse().getStatus();
                    if (status == 200) {
                        successCount.incrementAndGet();
                    } else if (status == 409) {
                        conflictCount.incrementAndGet();
                    }
                } catch (Exception e) {
                    // unexpected error
                } finally {
                    doneLatch.countDown();
                }
            });
        }

        startLatch.countDown();
        doneLatch.await(10, TimeUnit.SECONDS);
        executor.shutdown();

        // Invariant: Exactly 1 confirmation succeeds with 200, remaining threads receive 409 Conflict
        assertThat(successCount.get()).isEqualTo(1);
        assertThat(conflictCount.get()).isEqualTo(threadCount - 1);
    }

    @Test
    void testAnalyticsAndCategoriesEndpoints() throws Exception {
        String token = registerAndLogin("Analytics User", "analytics.user@test.com", "pass123");

        // Categories list
        var catResp = mvc.perform(get("/api/categories").header("Authorization", token))
                .andExpect(status().isOk())
                .andReturn();
        var catArr = mapper.readTree(catResp.getResponse().getContentAsString());
        assertThat(catArr.isArray()).isTrue();

        // User Dashboard
        var dashResp = mvc.perform(get("/api/users/me/dashboard").header("Authorization", token))
                .andExpect(status().isOk())
                .andReturn();
        var dashObj = mapper.readTree(dashResp.getResponse().getContentAsString());
        assertThat(dashObj.has("totalSpent")).isTrue();
        assertThat(dashObj.has("netTotalBalance")).isTrue();
    }

    @Test
    void testExpenseCreation_RejectsForeignCurrency() throws Exception {
        String token = registerAndLogin("Foreign Exp User", "foreign.exp@test.com", "pass123");

        var gResp = mvc.perform(post("/api/groups").header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of("name", "Currency Test Group"))))
                .andExpect(status().isOk()).andReturn();
        Long groupId = mapper.readTree(gResp.getResponse().getContentAsString()).get("id").asLong();

        var meResp = mvc.perform(get("/api/auth/me").header("Authorization", token))
                .andExpect(status().isOk()).andReturn();
        Long userId = mapper.readTree(meResp.getResponse().getContentAsString()).get("id").asLong();

        // 1. Attempting expense creation with USD -> 400 BAD REQUEST
        mvc.perform(post("/api/groups/" + groupId + "/expenses").header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of(
                        "amount", 100.0,
                        "currency", "USD",
                        "payerId", userId,
                        "splitType", "EQUAL"
                ))))
                .andExpect(status().isBadRequest());

        // 2. Attempting expense creation with EUR -> 400 BAD REQUEST
        mvc.perform(post("/api/groups/" + groupId + "/expenses").header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of(
                        "amount", 85.0,
                        "currency", "EUR",
                        "payerId", userId,
                        "splitType", "EQUAL"
                ))))
                .andExpect(status().isBadRequest());

        // 3. Expense creation with INR -> 200 OK
        mvc.perform(post("/api/groups/" + groupId + "/expenses").header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of(
                        "amount", 500.0,
                        "currency", "INR",
                        "payerId", userId,
                        "splitType", "EQUAL",
                        "note", "Valid INR Expense"
                ))))
                .andExpect(status().isOk());
    }

    @Test
    void testSettlementCreation_RejectsForeignCurrency() throws Exception {
        String token = registerAndLogin("Settlement Curr User", "settle.curr@test.com", "pass123");

        var gResp = mvc.perform(post("/api/groups").header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of("name", "Settlement Curr Group"))))
                .andExpect(status().isOk()).andReturn();
        Long groupId = mapper.readTree(gResp.getResponse().getContentAsString()).get("id").asLong();

        var meResp = mvc.perform(get("/api/auth/me").header("Authorization", token))
                .andExpect(status().isOk()).andReturn();
        Long userId = mapper.readTree(meResp.getResponse().getContentAsString()).get("id").asLong();

        // Attempting settlement in USD -> 400 BAD REQUEST
        mvc.perform(post("/api/groups/" + groupId + "/settlements").header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of(
                        "fromUserId", userId,
                        "toUserId", userId,
                        "amount", 50.0,
                        "currency", "USD"
                ))))
                .andExpect(status().isBadRequest());
    }

    @Test
    void testForeignReceiptConfirmation_RejectedWith422_AndNoLedgerContamination() throws Exception {
        String token = registerAndLogin("Foreign Receipt User", "foreign.receipt@test.com", "pass123");

        var gResp = mvc.perform(post("/api/groups").header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(Map.of("name", "Foreign Receipt Group"))))
                .andExpect(status().isOk()).andReturn();
        Long groupId = mapper.readTree(gResp.getResponse().getContentAsString()).get("id").asLong();

        var meResp = mvc.perform(get("/api/auth/me").header("Authorization", token))
                .andExpect(status().isOk()).andReturn();
        Long userId = mapper.readTree(meResp.getResponse().getContentAsString()).get("id").asLong();

        // 1. Upload mock receipt
        MockMultipartFile file = new MockMultipartFile(
                "file", "foreign_receipt.jpg", "image/jpeg", "usd receipt bytes".getBytes()
        );
        var uploadResp = mvc.perform(multipart("/api/groups/" + groupId + "/receipts")
                .file(file)
                .header("Authorization", token))
                .andExpect(status().isOk())
                .andReturn();
        Long receiptId = mapper.readTree(uploadResp.getResponse().getContentAsString()).get("id").asLong();

        // 2. Set receipt as extracted with USD currency directly in repository
        Receipt receipt = receiptRepository.findById(receiptId).orElseThrow();
        receipt.setCurrency("USD");
        receipt.setTotalAmount(new BigDecimal("28.11"));
        receipt.setSubtotal(new BigDecimal("25.97"));
        receipt.setTax(new BigDecimal("2.14"));
        receipt.setMerchantName("Safeway Supermarket");
        receipt.setStatus(Receipt.Status.EXTRACTED);
        receiptRepository.save(receipt);

        // 3. Attempt to review changing currency to INR -> 400 BAD REQUEST (Original currency is immutable)
        ReviewReceiptRequest reviewReq = new ReviewReceiptRequest();
        reviewReq.setCurrency("INR");
        reviewReq.setTotalAmount(new BigDecimal("28.11"));
        mvc.perform(put("/api/groups/" + groupId + "/receipts/" + receiptId + "/review")
                .header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(reviewReq)))
                .andExpect(status().isBadRequest());

        // 4. Attempt to confirm foreign currency receipt -> 422 UNPROCESSABLE_ENTITY
        ConfirmReceiptRequest confirmReq = new ConfirmReceiptRequest();
        confirmReq.setPayerId(userId);
        confirmReq.setSplitType("EQUAL");
        confirmReq.setNote("Foreign USD Receipt Confirmation Attempt");

        mvc.perform(post("/api/groups/" + groupId + "/receipts/" + receiptId + "/confirm")
                .header("Authorization", token)
                .contentType(MediaType.APPLICATION_JSON)
                .content(mapper.writeValueAsString(confirmReq)))
                .andExpect(status().isUnprocessableEntity());

        // 5. Invariant: Ledger is unpolluted. Expenses list for group is empty, balances remain zero.
        var expListResp = mvc.perform(get("/api/groups/" + groupId + "/expenses").header("Authorization", token))
                .andExpect(status().isOk()).andReturn();
        var expNodes = mapper.readTree(expListResp.getResponse().getContentAsString());
        assertThat(expNodes.size()).isEqualTo(0);

        var balResp = mvc.perform(get("/api/groups/" + groupId + "/balances").header("Authorization", token))
                .andExpect(status().isOk()).andReturn();
        var balNodes = mapper.readTree(balResp.getResponse().getContentAsString());
        for (var b : balNodes) {
            assertThat(b.get("netBalance").asDouble()).isEqualTo(0.0);
        }
    }
}
