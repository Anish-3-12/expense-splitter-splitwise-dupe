package com.example.expensesplitter.controller;

import com.example.expensesplitter.client.AiServiceClient;
import com.example.expensesplitter.dto.InterpretSplitRequest;
import com.example.expensesplitter.dto.InterpretSplitResponseDto;
import com.example.expensesplitter.entity.Group;
import com.example.expensesplitter.entity.Membership;
import com.example.expensesplitter.entity.User;
import com.example.expensesplitter.repository.GroupRepository;
import com.example.expensesplitter.repository.MembershipRepository;
import com.example.expensesplitter.security.CurrentUser;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping
public class AiSplitController {

    private final GroupRepository groupRepository;
    private final MembershipRepository membershipRepository;
    private final AiServiceClient aiServiceClient;

    public AiSplitController(
            GroupRepository groupRepository,
            MembershipRepository membershipRepository,
            AiServiceClient aiServiceClient
    ) {
        this.groupRepository = groupRepository;
        this.membershipRepository = membershipRepository;
        this.aiServiceClient = aiServiceClient;
    }

    private void validateGroupMembership(Group group, User user) {
        membershipRepository.findByGroupAndUser(group, user)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.FORBIDDEN, "Not a group member"));
    }

    @PostMapping({"/api/groups/{groupId}/ai/interpret-split", "/api/ai/split/interpret"})
    public ResponseEntity<InterpretSplitResponseDto> interpretSplit(
            @PathVariable(value = "groupId", required = false) Long groupId,
            @Valid @RequestBody InterpretSplitRequest req,
            @CurrentUser User currentUser
    ) {
        List<Membership> memberships;
        if (groupId != null) {
            Group group = groupRepository.findById(groupId)
                    .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Group not found"));
            validateGroupMembership(group, currentUser);
            memberships = membershipRepository.findByGroup_Id(groupId);
        } else {
            // Find user's active groups
            List<Membership> userMemberships = membershipRepository.findByUser(currentUser);
            if (!userMemberships.isEmpty()) {
                Long gId = userMemberships.get(0).getGroup().getId();
                memberships = membershipRepository.findByGroup_Id(gId);
            } else {
                memberships = Collections.emptyList();
            }
        }
        List<Map<String, Object>> membersData = memberships.stream().map(m -> {
            Map<String, Object> map = new HashMap<>();
            map.put("id", m.getUser().getId());
            map.put("name", m.getUser().getName());
            map.put("email", m.getUser().getEmail());
            return map;
        }).collect(Collectors.toList());

        List<Map<String, Object>> itemsData = new ArrayList<>();
        if (req.getItems() != null) {
            for (InterpretSplitRequest.ItemDraft it : req.getItems()) {
                Map<String, Object> im = new HashMap<>();
                im.put("id", it.getId());
                im.put("description", it.getDescription());
                im.put("amount", it.getAmount() != null ? it.getAmount().doubleValue() : 0.0);
                itemsData.add(im);
            }
        }

        Long payerId = req.getPayerId() != null ? req.getPayerId() : currentUser.getId();

        Map<String, Object> aiResult = aiServiceClient.interpretSplit(
                req.getInstruction(),
                membersData,
                req.getTotalAmount(),
                itemsData,
                payerId
        );

        InterpretSplitResponseDto resp = new InterpretSplitResponseDto();
        resp.setOriginalInstruction((String) aiResult.getOrDefault("original_instruction", req.getInstruction()));
        resp.setDescription((String) aiResult.get("description"));
        Object totalAmtObj = aiResult.get("total_amount");
        if (totalAmtObj != null) {
            try {
                resp.setTotalAmount(new BigDecimal(totalAmtObj.toString()));
            } catch (Exception ignored) {}
        }
        Object pIdObj = aiResult.get("payer_id");
        if (pIdObj != null) {
            try {
                resp.setPayerId(Long.valueOf(pIdObj.toString()));
            } catch (Exception ignored) {}
        }
        resp.setSplitType((String) aiResult.getOrDefault("split_type", "EQUAL"));
        resp.setExplanation((String) aiResult.get("explanation"));
        resp.setClarificationRequired(Boolean.TRUE.equals(aiResult.get("clarification_required")));
        resp.setClarificationQuestion((String) aiResult.get("clarification_question"));
        Object confObj = aiResult.get("confidence");
        resp.setConfidence(confObj != null ? Double.valueOf(confObj.toString()) : 1.0);

        List<String> unres = (List<String>) aiResult.get("unresolved_references");
        resp.setUnresolvedReferences(unres != null ? unres : Collections.emptyList());

        Set<Long> validUserIds = memberships.stream().map(m -> m.getUser().getId()).collect(Collectors.toSet());
        Map<Long, String> nameLookup = memberships.stream().collect(Collectors.toMap(m -> m.getUser().getId(), m -> m.getUser().getName()));

        List<InterpretSplitResponseDto.ItemAllocationDto> allocList = new ArrayList<>();
        List<Map<String, Object>> rawAllocs = (List<Map<String, Object>>) aiResult.get("allocations");
        if (rawAllocs != null) {
            for (Map<String, Object> raw : rawAllocs) {
                InterpretSplitResponseDto.ItemAllocationDto ad = new InterpretSplitResponseDto.ItemAllocationDto();
                ad.setItemId(raw.get("item_id") != null ? raw.get("item_id").toString() : null);
                ad.setItemDescription((String) raw.get("item_description"));
                ad.setSplitType((String) raw.getOrDefault("split_type", "EQUAL"));

                List<Object> pids = (List<Object>) raw.get("participant_ids");
                List<Long> sanitizedPids = new ArrayList<>();
                if (pids != null) {
                    for (Object pid : pids) {
                        Long uid = Long.valueOf(pid.toString());
                        if (validUserIds.contains(uid)) {
                            sanitizedPids.add(uid);
                        }
                    }
                }
                ad.setParticipantIds(sanitizedPids);
                allocList.add(ad);
            }
        }
        resp.setAllocations(allocList);

        // Build participant allocations preview
        List<InterpretSplitResponseDto.ParticipantAllocationDto> partList = new ArrayList<>();
        List<Map<String, Object>> rawPartAllocs = (List<Map<String, Object>>) aiResult.get("participant_allocations");
        if (rawPartAllocs != null) {
            for (Map<String, Object> rp : rawPartAllocs) {
                Long uid = Long.valueOf(rp.get("user_id").toString());
                if (validUserIds.contains(uid)) {
                    InterpretSplitResponseDto.ParticipantAllocationDto pad = new InterpretSplitResponseDto.ParticipantAllocationDto();
                    pad.setUserId(uid);
                    pad.setUserName(nameLookup.getOrDefault(uid, "User " + uid));
                    Object sa = rp.get("share_amount");
                    if (sa != null) pad.setShareAmount(new BigDecimal(sa.toString()));
                    Object p = rp.get("percent");
                    if (p != null) pad.setPercent(new BigDecimal(p.toString()));
                    partList.add(pad);
                }
            }
        }
        resp.setParticipantAllocations(partList);

        return ResponseEntity.ok(resp);
    }
}
