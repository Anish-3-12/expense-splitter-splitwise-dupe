package com.example.expensesplitter.repository;

import com.example.expensesplitter.entity.ReceiptItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ReceiptItemRepository extends JpaRepository<ReceiptItem, Long> {
    List<ReceiptItem> findByReceiptIdOrderByLineNumberAsc(Long receiptId);
    void deleteByReceiptId(Long receiptId);
}
