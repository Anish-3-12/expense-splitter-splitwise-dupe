package com.example.expensesplitter.controller;

import com.example.expensesplitter.dto.ConfirmReceiptRequest;
import com.example.expensesplitter.dto.ExpenseDto;
import com.example.expensesplitter.dto.ReceiptDto;
import com.example.expensesplitter.dto.ReviewReceiptRequest;
import com.example.expensesplitter.entity.Expense;
import com.example.expensesplitter.entity.Receipt;
import com.example.expensesplitter.entity.User;
import com.example.expensesplitter.security.CurrentUser;
import com.example.expensesplitter.service.ReceiptService;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/api/groups/{groupId}/receipts")
public class ReceiptController {

    private final ReceiptService receiptService;

    public ReceiptController(ReceiptService receiptService) {
        this.receiptService = receiptService;
    }

    @PostMapping(value = {"", "/upload"}, consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<ReceiptDto> uploadReceipt(
            @PathVariable("groupId") Long groupId,
            @RequestParam("file") MultipartFile file,
            @CurrentUser User currentUser
    ) {
        Receipt receipt = receiptService.uploadReceipt(groupId, currentUser, file);
        return ResponseEntity.ok(receiptService.toDto(receipt));
    }

    @GetMapping
    public ResponseEntity<List<ReceiptDto>> listReceipts(
            @PathVariable("groupId") Long groupId,
            @CurrentUser User currentUser
    ) {
        List<ReceiptDto> list = receiptService.listReceipts(groupId, currentUser);
        return ResponseEntity.ok(list);
    }

    @GetMapping("/{receiptId}")
    public ResponseEntity<ReceiptDto> getReceipt(
            @PathVariable("groupId") Long groupId,
            @PathVariable("receiptId") Long receiptId,
            @CurrentUser User currentUser
    ) {
        ReceiptDto dto = receiptService.getReceipt(groupId, receiptId, currentUser);
        return ResponseEntity.ok(dto);
    }

    @PostMapping("/{receiptId}/extract")
    public ResponseEntity<ReceiptDto> extractReceipt(
            @PathVariable("groupId") Long groupId,
            @PathVariable("receiptId") Long receiptId,
            @CurrentUser User currentUser
    ) {
        Receipt extracted = receiptService.extractReceipt(groupId, receiptId, currentUser);
        return ResponseEntity.ok(receiptService.toDto(extracted));
    }

    @PutMapping("/{receiptId}/review")
    public ResponseEntity<ReceiptDto> reviewReceipt(
            @PathVariable("groupId") Long groupId,
            @PathVariable("receiptId") Long receiptId,
            @Valid @RequestBody ReviewReceiptRequest req,
            @CurrentUser User currentUser
    ) {
        Receipt reviewed = receiptService.reviewReceipt(groupId, receiptId, currentUser, req);
        return ResponseEntity.ok(receiptService.toDto(reviewed));
    }

    @PostMapping("/{receiptId}/confirm")
    public ResponseEntity<ExpenseDto> confirmReceipt(
            @PathVariable("groupId") Long groupId,
            @PathVariable("receiptId") Long receiptId,
            @Valid @RequestBody ConfirmReceiptRequest req,
            @CurrentUser User currentUser
    ) {
        Expense expense = receiptService.confirmReceipt(groupId, receiptId, currentUser, req);

        ExpenseDto dto = new ExpenseDto();
        dto.setId(expense.getId());
        dto.setGroupId(expense.getGroup().getId());
        dto.setCreatedById(expense.getCreatedBy().getId());
        dto.setPayerId(expense.getPayer().getId());
        dto.setAmount(expense.getAmount());
        dto.setCurrency(expense.getCurrency());
        dto.setSplitType(expense.getSplitType());
        dto.setNote(expense.getNote());
        if (expense.getCategory() != null) {
            dto.setCategoryId(expense.getCategory().getId());
            dto.setCategoryName(expense.getCategory().getName());
            dto.setCategoryIcon(expense.getCategory().getIcon());
        }
        dto.setCreatedAt(expense.getCreatedAt());

        return ResponseEntity.ok(dto);
    }
}
