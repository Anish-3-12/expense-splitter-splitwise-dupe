package com.example.expensesplitter.service;

import com.example.expensesplitter.client.AiServiceClient;
import com.example.expensesplitter.dto.ConfirmReceiptRequest;
import com.example.expensesplitter.dto.CreateExpenseRequest;
import com.example.expensesplitter.dto.ReceiptDto;
import com.example.expensesplitter.dto.ReceiptItemDto;
import com.example.expensesplitter.dto.ReviewReceiptRequest;
import com.example.expensesplitter.entity.*;
import com.example.expensesplitter.repository.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import java.io.File;
import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class ReceiptService {

    private static final Logger log = LoggerFactory.getLogger(ReceiptService.class);

    private final ReceiptRepository receiptRepository;
    private final ReceiptItemRepository receiptItemRepository;
    private final GroupRepository groupRepository;
    private final MembershipRepository membershipRepository;
    private final ExpenseRepository expenseRepository;
    private final ExpenseCategoryRepository categoryRepository;
    private final ExpenseService expenseService;
    private final AiServiceClient aiServiceClient;
    private final String receiptsStorageDir;

    public ReceiptService(
            ReceiptRepository receiptRepository,
            ReceiptItemRepository receiptItemRepository,
            GroupRepository groupRepository,
            MembershipRepository membershipRepository,
            ExpenseRepository expenseRepository,
            ExpenseCategoryRepository categoryRepository,
            ExpenseService expenseService,
            AiServiceClient aiServiceClient,
            @Value("${app.storage.receipts-dir:uploads/receipts}") String receiptsStorageDir
    ) {
        this.receiptRepository = receiptRepository;
        this.receiptItemRepository = receiptItemRepository;
        this.groupRepository = groupRepository;
        this.membershipRepository = membershipRepository;
        this.expenseRepository = expenseRepository;
        this.categoryRepository = categoryRepository;
        this.expenseService = expenseService;
        this.aiServiceClient = aiServiceClient;
        this.receiptsStorageDir = receiptsStorageDir;
    }

    private void validateGroupMembership(Group group, User user) {
        membershipRepository.findByGroupAndUser(group, user)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.FORBIDDEN, "Not a group member"));
    }

    // 1. Upload receipt image
    @Transactional
    public Receipt uploadReceipt(Long groupId, User user, MultipartFile file) {
        Group group = groupRepository.findById(groupId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Group not found"));
        validateGroupMembership(group, user);

        if (file.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "File is empty");
        }

        String mimeType = file.getContentType();
        if (mimeType == null || (!mimeType.startsWith("image/") && !mimeType.equals("application/pdf"))) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Only image files (JPG, PNG, WebP) or PDFs are supported");
        }

        // Create storage directory if missing
        Path groupDir = Paths.get(receiptsStorageDir, String.valueOf(groupId));
        try {
            Files.createDirectories(groupDir);
        } catch (IOException e) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Could not initialize file storage directory");
        }

        String originalFilename = file.getOriginalFilename() != null ? file.getOriginalFilename() : "receipt.jpg";
        // Clean original filename to prevent path traversal
        originalFilename = Paths.get(originalFilename).getFileName().toString();
        String extension = "";
        int dotIdx = originalFilename.lastIndexOf('.');
        if (dotIdx > 0) {
            extension = originalFilename.substring(dotIdx);
        }

        String uniqueFilename = UUID.randomUUID() + extension;
        Path targetPath = groupDir.resolve(uniqueFilename);

        try {
            Files.copy(file.getInputStream(), targetPath, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            log.error("Failed to save receipt file to disk: {}", e.getMessage());
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Failed to store uploaded receipt file");
        }

        Receipt receipt = new Receipt();
        receipt.setGroup(group);
        receipt.setUploadedBy(user);
        receipt.setFilePath(targetPath.toAbsolutePath().toString());
        receipt.setOriginalFilename(originalFilename);
        receipt.setFileSize(file.getSize());
        receipt.setMimeType(mimeType);
        receipt.setStatus(Receipt.Status.UPLOADED);
        receipt.setCurrency("INR");

        return receiptRepository.save(receipt);
    }

    // 2. Extract receipt data via AI microservice
    @Transactional
    public Receipt extractReceipt(Long groupId, Long receiptId, User user) {
        Group group = groupRepository.findById(groupId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Group not found"));
        validateGroupMembership(group, user);

        Receipt receipt = receiptRepository.findByIdAndGroupId(receiptId, groupId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Receipt not found"));

        if (receipt.getStatus() == Receipt.Status.CONFIRMED) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Receipt is already confirmed as an expense");
        }

        receipt.setStatus(Receipt.Status.PROCESSING);
        receiptRepository.save(receipt);

        Map<String, Object> aiResult = aiServiceClient.extractReceipt(receipt.getFilePath(), null, groupId);

        try {
            String merchant = (String) aiResult.getOrDefault("merchant", "Merchant");
            String date = (String) aiResult.get("receipt_date");
            String currency = (String) aiResult.getOrDefault("currency", "INR");
            String currencySymbol = (String) aiResult.getOrDefault("currency_symbol", "$");
            String validationStatus = (String) aiResult.getOrDefault("validation_status", "RECONCILED");
            String rawOcrText = (String) aiResult.get("raw_ocr_text");

            Object totalObj = aiResult.get("total");
            BigDecimal total = totalObj != null ? new BigDecimal(totalObj.toString()) : BigDecimal.ZERO;

            Object subtotalObj = aiResult.get("subtotal");
            BigDecimal subtotal = subtotalObj != null ? new BigDecimal(subtotalObj.toString()) : null;

            Object taxObj = aiResult.get("tax");
            BigDecimal tax = taxObj != null ? new BigDecimal(taxObj.toString()) : BigDecimal.ZERO;

            Object discObj = aiResult.get("discrepancy_amount");
            BigDecimal discrepancyAmount = discObj != null ? new BigDecimal(discObj.toString()) : BigDecimal.ZERO;

            receipt.setMerchantName(merchant);
            receipt.setReceiptDate(date);
            receipt.setCurrency(currency);
            receipt.setCurrencySymbol(currencySymbol);
            receipt.setValidationStatus(validationStatus);
            receipt.setDiscrepancyAmount(discrepancyAmount);
            receipt.setRawOcrText(rawOcrText);
            receipt.setTotalAmount(total);
            receipt.setSubtotal(subtotal);
            receipt.setTax(tax);
            receipt.setStatus(Receipt.Status.EXTRACTED);

            // Clean previous items if retrying
            receipt.getItems().clear();

            List<Map<String, Object>> itemsData = (List<Map<String, Object>>) aiResult.get("items");
            if (itemsData != null) {
                int line = 1;
                for (Map<String, Object> it : itemsData) {
                    ReceiptItem item = new ReceiptItem();
                    item.setLineNumber(line++);
                    item.setDescription((String) it.getOrDefault("description", "Item " + line));
                    Object q = it.get("quantity");
                    item.setQuantity(q != null ? new BigDecimal(q.toString()) : BigDecimal.ONE);
                    Object up = it.get("unit_price");
                    item.setUnitPrice(up != null ? new BigDecimal(up.toString()) : BigDecimal.ZERO);
                    Object lt = it.get("line_total");
                    item.setLineTotal(lt != null ? new BigDecimal(lt.toString()) : item.getUnitPrice());

                    Object isAmbig = it.get("is_ambiguous");
                    item.setIsAmbiguous(isAmbig != null && Boolean.parseBoolean(isAmbig.toString()));
                    item.setAmbiguityReason((String) it.get("ambiguity_reason"));

                    receipt.addItem(item);
                }
            }

            return receiptRepository.save(receipt);
        } catch (Exception e) {
            log.error("Failed to apply receipt extraction response: {}", e.getMessage());
            receipt.setStatus(Receipt.Status.FAILED);
            receipt.setErrorMessage("Extraction failed: " + e.getMessage());
            return receiptRepository.save(receipt);
        }
    }

    // 3. Review receipt data before confirmation
    @Transactional
    public Receipt reviewReceipt(Long groupId, Long receiptId, User user, ReviewReceiptRequest req) {
        Group group = groupRepository.findById(groupId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Group not found"));
        validateGroupMembership(group, user);

        Receipt receipt = receiptRepository.findByIdAndGroupId(receiptId, groupId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Receipt not found"));

        if (receipt.getStatus() == Receipt.Status.CONFIRMED) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Receipt already confirmed");
        }

        if (req.getMerchantName() != null) receipt.setMerchantName(req.getMerchantName());
        if (req.getReceiptDate() != null) receipt.setReceiptDate(req.getReceiptDate());
        if (req.getCurrency() != null && !req.getCurrency().trim().equalsIgnoreCase(receipt.getCurrency())) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST,
                    "Cannot modify extracted receipt currency from '" + receipt.getCurrency() + "' to '" + req.getCurrency() + "'. Original document currency is immutable.");
        }
        if (req.getTotalAmount() != null) receipt.setTotalAmount(req.getTotalAmount());
        if (req.getSubtotal() != null) receipt.setSubtotal(req.getSubtotal());
        if (req.getTax() != null) receipt.setTax(req.getTax());

        if (req.getItems() != null) {
            receipt.getItems().clear();
            int line = 1;
            for (ReviewReceiptRequest.ItemUpdate iu : req.getItems()) {
                ReceiptItem item = new ReceiptItem();
                item.setLineNumber(line++);
                item.setDescription(iu.getDescription() != null ? iu.getDescription() : "Item " + line);
                item.setQuantity(iu.getQuantity() != null ? iu.getQuantity() : BigDecimal.ONE);
                item.setUnitPrice(iu.getUnitPrice() != null ? iu.getUnitPrice() : BigDecimal.ZERO);
                item.setLineTotal(iu.getLineTotal() != null ? iu.getLineTotal() : item.getUnitPrice());
                receipt.addItem(item);
            }

            // Integer minor-unit (paise / cents) financial invariants:
            // Invariant 1: sum(line_items) == subtotal
            // Invariant 2: subtotal + tax == total
            long sumItemsMinor = receipt.getItems().stream()
                    .map(it -> it.getLineTotal().multiply(BigDecimal.valueOf(100)).setScale(0, java.math.RoundingMode.HALF_UP).longValue())
                    .reduce(0L, Long::sum);

            Long subtotalMinor = receipt.getSubtotal() != null ?
                    receipt.getSubtotal().multiply(BigDecimal.valueOf(100)).setScale(0, java.math.RoundingMode.HALF_UP).longValue() : null;
            long taxMinor = receipt.getTax() != null ?
                    receipt.getTax().multiply(BigDecimal.valueOf(100)).setScale(0, java.math.RoundingMode.HALF_UP).longValue() : 0L;
            Long totalMinor = receipt.getTotalAmount() != null ?
                    receipt.getTotalAmount().multiply(BigDecimal.valueOf(100)).setScale(0, java.math.RoundingMode.HALF_UP).longValue() : null;

            boolean inv1Passed = (subtotalMinor != null && sumItemsMinor == subtotalMinor);
            boolean inv2Passed = (subtotalMinor != null && totalMinor != null && (subtotalMinor + taxMinor) == totalMinor);
            boolean hasAmbiguity = receipt.getItems().stream().anyMatch(it -> Boolean.TRUE.equals(it.getIsAmbiguous()));

            if (inv1Passed && inv2Passed && !hasAmbiguity) {
                receipt.setValidationStatus("RECONCILED");
                receipt.setDiscrepancyAmount(BigDecimal.ZERO);
            } else {
                receipt.setValidationStatus("DISCREPANCY_DETECTED");
                long diff1 = subtotalMinor != null ? Math.abs(sumItemsMinor - subtotalMinor) : 0L;
                long diff2 = (subtotalMinor != null && totalMinor != null) ? Math.abs((subtotalMinor + taxMinor) - totalMinor) : 0L;
                long totalDiff = diff1 + diff2;
                receipt.setDiscrepancyAmount(BigDecimal.valueOf(totalDiff, 2));
            }
        }

        return receiptRepository.save(receipt);
    }

    // 4. Confirm receipt -> creates exactly one Expense record using Java financial engine
    @Transactional
    public Expense confirmReceipt(Long groupId, Long receiptId, User user, ConfirmReceiptRequest req) {
        Group group = groupRepository.findById(groupId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Group not found"));
        validateGroupMembership(group, user);

        Receipt receipt = receiptRepository.findByIdAndGroupIdForUpdate(receiptId, groupId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Receipt not found"));

        // Idempotency: repeated confirmation is rejected with HTTP 409 Conflict
        if (receipt.getStatus() == Receipt.Status.CONFIRMED) {
            String expMsg = receipt.getExpense() != null ? " with expense id: " + receipt.getExpense().getId() : "";
            log.warn("Receipt {} has already been confirmed{}", receiptId, expMsg);
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Receipt has already been confirmed" + expMsg);
        }

        // Restrict foreign currency receipts from contaminating the INR-only financial ledger
        if (receipt.getCurrency() != null && !"INR".equalsIgnoreCase(receipt.getCurrency().trim())) {
            throw new ResponseStatusException(HttpStatus.UNPROCESSABLE_ENTITY,
                    "Cannot confirm receipt in foreign currency '" + receipt.getCurrency() + "'. The expense ledger only supports INR (₹). Foreign currency receipts cannot be posted directly into the ledger.");
        }

        BigDecimal amount = receipt.getTotalAmount();
        if (amount == null || amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Receipt has an invalid total amount. Please review before confirming.");
        }

        CreateExpenseRequest expReq = new CreateExpenseRequest();
        expReq.setAmount(amount);
        expReq.setPayerId(req.getPayerId());
        expReq.setCurrency(receipt.getCurrency());
        expReq.setSplitType(req.getSplitType() != null ? req.getSplitType() : "EQUAL");
        expReq.setCategoryId(req.getCategoryId());
        String defaultNote = (receipt.getMerchantName() != null ? receipt.getMerchantName() : "Receipt Expense");
        expReq.setNote(req.getNote() != null && !req.getNote().isBlank() ? req.getNote() : defaultNote);
        expReq.setShares(req.getShares());

        Expense savedExpense = expenseService.createExpense(groupId, user, expReq);

        // Copy receipt items into expense line items
        for (ReceiptItem ri : receipt.getItems()) {
            ExpenseItem ei = new ExpenseItem();
            ei.setDescription(ri.getDescription());
            ei.setQuantity(ri.getQuantity());
            ei.setUnitPrice(ri.getUnitPrice());
            ei.setLineTotal(ri.getLineTotal());
            savedExpense.addItem(ei);
        }
        expenseRepository.save(savedExpense);

        receipt.setExpense(savedExpense);
        receipt.setStatus(Receipt.Status.CONFIRMED);
        receiptRepository.save(receipt);

        return savedExpense;
    }

    public List<ReceiptDto> listReceipts(Long groupId, User user) {
        Group group = groupRepository.findById(groupId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Group not found"));
        validateGroupMembership(group, user);

        return receiptRepository.findByGroupIdOrderByCreatedAtDesc(groupId).stream()
                .map(this::toDto)
                .collect(Collectors.toList());
    }

    public ReceiptDto getReceipt(Long groupId, Long receiptId, User user) {
        Group group = groupRepository.findById(groupId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Group not found"));
        validateGroupMembership(group, user);

        Receipt receipt = receiptRepository.findByIdAndGroupId(receiptId, groupId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Receipt not found"));
        return toDto(receipt);
    }

    public ReceiptDto toDto(Receipt r) {
        ReceiptDto dto = new ReceiptDto();
        dto.setId(r.getId());
        dto.setGroupId(r.getGroup().getId());
        dto.setUploadedById(r.getUploadedBy().getId());
        dto.setUploadedByName(r.getUploadedBy().getName());
        dto.setOriginalFilename(r.getOriginalFilename());
        dto.setFileSize(r.getFileSize());
        dto.setMimeType(r.getMimeType());
        dto.setStatus(r.getStatus().name());
        dto.setTotalAmount(r.getTotalAmount());
        dto.setSubtotal(r.getSubtotal());
        dto.setTax(r.getTax());
        dto.setCurrency(r.getCurrency());
        dto.setCurrencySymbol(r.getCurrencySymbol());
        dto.setValidationStatus(r.getValidationStatus());
        dto.setDiscrepancyAmount(r.getDiscrepancyAmount());
        dto.setRawOcrText(r.getRawOcrText());
        dto.setMerchantName(r.getMerchantName());
        dto.setReceiptDate(r.getReceiptDate());
        if (r.getExpense() != null) {
            dto.setExpenseId(r.getExpense().getId());
        }
        dto.setErrorMessage(r.getErrorMessage());
        dto.setCreatedAt(r.getCreatedAt());

        List<ReceiptItemDto> itemDtos = r.getItems().stream()
                .map(it -> new ReceiptItemDto(
                        it.getId(),
                        it.getLineNumber(),
                        it.getDescription(),
                        it.getQuantity(),
                        it.getUnitPrice(),
                        it.getLineTotal(),
                        it.getConfidence(),
                        it.getIsAmbiguous(),
                        it.getAmbiguityReason()
                ))
                .collect(Collectors.toList());
        dto.setItems(itemDtos);
        return dto;
    }
}
