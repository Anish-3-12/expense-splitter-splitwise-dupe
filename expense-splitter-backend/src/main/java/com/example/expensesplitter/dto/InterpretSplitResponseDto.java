package com.example.expensesplitter.dto;

import java.math.BigDecimal;
import java.util.List;

public class InterpretSplitResponseDto {
    private String originalInstruction;
    private String description;
    private BigDecimal totalAmount;
    private Long payerId;
    private String splitType;
    private String explanation;
    private List<ItemAllocationDto> allocations;
    private List<ParticipantAllocationDto> participantAllocations;
    private List<String> unresolvedReferences;
    private boolean clarificationRequired;
    private String clarificationQuestion;
    private Double confidence;

    public static class ItemAllocationDto {
        private String itemId;
        private String itemDescription;
        private List<Long> participantIds;
        private String splitType;

        public String getItemId() { return itemId; }
        public void setItemId(String itemId) { this.itemId = itemId; }
        public String getItemDescription() { return itemDescription; }
        public void setItemDescription(String itemDescription) { this.itemDescription = itemDescription; }
        public List<Long> getParticipantIds() { return participantIds; }
        public void setParticipantIds(List<Long> participantIds) { this.participantIds = participantIds; }
        public String getSplitType() { return splitType; }
        public void setSplitType(String splitType) { this.splitType = splitType; }
    }

    public static class ParticipantAllocationDto {
        private Long userId;
        private String userName;
        private BigDecimal shareAmount;
        private BigDecimal percent;

        public Long getUserId() { return userId; }
        public void setUserId(Long userId) { this.userId = userId; }
        public String getUserName() { return userName; }
        public void setUserName(String userName) { this.userName = userName; }
        public BigDecimal getShareAmount() { return shareAmount; }
        public void setShareAmount(BigDecimal shareAmount) { this.shareAmount = shareAmount; }
        public BigDecimal getPercent() { return percent; }
        public void setPercent(BigDecimal percent) { this.percent = percent; }
    }

    public String getOriginalInstruction() { return originalInstruction; }
    public void setOriginalInstruction(String originalInstruction) { this.originalInstruction = originalInstruction; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public BigDecimal getTotalAmount() { return totalAmount; }
    public void setTotalAmount(BigDecimal totalAmount) { this.totalAmount = totalAmount; }
    public Long getPayerId() { return payerId; }
    public void setPayerId(Long payerId) { this.payerId = payerId; }
    public String getSplitType() { return splitType; }
    public void setSplitType(String splitType) { this.splitType = splitType; }
    public String getExplanation() { return explanation; }
    public void setExplanation(String explanation) { this.explanation = explanation; }
    public List<ItemAllocationDto> getAllocations() { return allocations; }
    public void setAllocations(List<ItemAllocationDto> allocations) { this.allocations = allocations; }
    public List<ParticipantAllocationDto> getParticipantAllocations() { return participantAllocations; }
    public void setParticipantAllocations(List<ParticipantAllocationDto> participantAllocations) { this.participantAllocations = participantAllocations; }
    public List<String> getUnresolvedReferences() { return unresolvedReferences; }
    public void setUnresolvedReferences(List<String> unresolvedReferences) { this.unresolvedReferences = unresolvedReferences; }
    public boolean isClarificationRequired() { return clarificationRequired; }
    public void setClarificationRequired(boolean clarificationRequired) { this.clarificationRequired = clarificationRequired; }
    public String getClarificationQuestion() { return clarificationQuestion; }
    public void setClarificationQuestion(String clarificationQuestion) { this.clarificationQuestion = clarificationQuestion; }
    public Double getConfidence() { return confidence; }
    public void setConfidence(Double confidence) { this.confidence = confidence; }
}
