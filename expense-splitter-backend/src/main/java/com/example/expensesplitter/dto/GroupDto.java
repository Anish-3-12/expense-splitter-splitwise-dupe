package com.example.expensesplitter.dto;

public class GroupDto {
    private Long id;
    private String name;
    private Long ownerId;
    private Integer memberCount;

    public GroupDto() {}

    public GroupDto(Long id, String name, Long ownerId) {
        this.id = id;
        this.name = name;
        this.ownerId = ownerId;
    }

    public GroupDto(Long id, String name, Long ownerId, Integer memberCount) {
        this.id = id;
        this.name = name;
        this.ownerId = ownerId;
        this.memberCount = memberCount;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public Long getOwnerId() { return ownerId; }
    public void setOwnerId(Long ownerId) { this.ownerId = ownerId; }

    public Integer getMemberCount() { return memberCount; }
    public void setMemberCount(Integer memberCount) { this.memberCount = memberCount; }
}
