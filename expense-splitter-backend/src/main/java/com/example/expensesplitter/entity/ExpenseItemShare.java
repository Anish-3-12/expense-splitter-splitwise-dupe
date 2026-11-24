package com.example.expensesplitter.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import org.hibernate.annotations.CreationTimestamp;

@Entity
@Table(name = "expense_item_shares")
public class ExpenseItemShare {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @JsonIgnore
    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "expense_item_id")
    private ExpenseItem expenseItem;

    @ManyToOne(optional = false, fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    @Column(name = "share_amount", precision = 19, scale = 2, nullable = false)
    private BigDecimal shareAmount;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private Instant createdAt;

    public ExpenseItemShare() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public ExpenseItem getExpenseItem() { return expenseItem; }
    public void setExpenseItem(ExpenseItem expenseItem) { this.expenseItem = expenseItem; }

    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }

    public BigDecimal getShareAmount() { return shareAmount; }
    public void setShareAmount(BigDecimal shareAmount) { this.shareAmount = shareAmount; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
