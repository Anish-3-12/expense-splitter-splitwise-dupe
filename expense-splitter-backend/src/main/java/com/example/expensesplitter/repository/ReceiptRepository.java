package com.example.expensesplitter.repository;

import com.example.expensesplitter.entity.Receipt;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ReceiptRepository extends JpaRepository<Receipt, Long> {
    List<Receipt> findByGroupIdOrderByCreatedAtDesc(Long groupId);
    Optional<Receipt> findByIdAndGroupId(Long id, Long groupId);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT r FROM Receipt r WHERE r.id = :id AND r.group.id = :groupId")
    Optional<Receipt> findByIdAndGroupIdForUpdate(@Param("id") Long id, @Param("groupId") Long groupId);
}
