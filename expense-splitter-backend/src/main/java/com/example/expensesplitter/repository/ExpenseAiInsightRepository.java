package com.example.expensesplitter.repository;

import com.example.expensesplitter.entity.ExpenseAiInsight;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ExpenseAiInsightRepository extends JpaRepository<ExpenseAiInsight, Long> {
    List<ExpenseAiInsight> findByGroupIdOrderByCreatedAtDesc(Long groupId);
}
