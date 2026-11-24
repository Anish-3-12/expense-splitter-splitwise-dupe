package com.example.expensesplitter.controller;

import com.example.expensesplitter.dto.GroupAnalyticsDto;
import com.example.expensesplitter.dto.UserDashboardDto;
import com.example.expensesplitter.entity.User;
import com.example.expensesplitter.security.CurrentUser;
import com.example.expensesplitter.service.AnalyticsService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class AnalyticsController {

    private final AnalyticsService analyticsService;

    public AnalyticsController(AnalyticsService analyticsService) {
        this.analyticsService = analyticsService;
    }

    @GetMapping("/groups/{groupId}/analytics/overview")
    public ResponseEntity<GroupAnalyticsDto> getGroupAnalytics(
            @PathVariable("groupId") Long groupId,
            @CurrentUser User currentUser
    ) {
        GroupAnalyticsDto dto = analyticsService.getGroupAnalytics(groupId, currentUser);
        return ResponseEntity.ok(dto);
    }

    @GetMapping("/users/me/dashboard")
    public ResponseEntity<UserDashboardDto> getUserDashboard(
            @CurrentUser User currentUser
    ) {
        UserDashboardDto dto = analyticsService.getUserDashboard(currentUser);
        return ResponseEntity.ok(dto);
    }
}
