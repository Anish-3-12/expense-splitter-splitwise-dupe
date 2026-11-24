import React, { useContext } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Box,
  Typography,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Avatar,
  Chip,
} from "@mui/material";
import DashboardOutlinedIcon from "@mui/icons-material/DashboardOutlined";
import GroupsOutlinedIcon from "@mui/icons-material/GroupsOutlined";
import ReceiptLongOutlinedIcon from "@mui/icons-material/ReceiptLongOutlined";
import AutoAwesomeOutlinedIcon from "@mui/icons-material/AutoAwesomeOutlined";
import InsightsOutlinedIcon from "@mui/icons-material/InsightsOutlined";
import LogoutOutlinedIcon from "@mui/icons-material/LogoutOutlined";
import { AuthContext } from "../context/AuthContext";

export default function Sidebar({ onItemClick }) {
  const location = useLocation();
  const { user, logout } = useContext(AuthContext);

  const navItems = [
    { label: "Overview", path: "/dashboard", icon: <DashboardOutlinedIcon /> },
    { label: "My Groups", path: "/groups", icon: <GroupsOutlinedIcon /> },
    { label: "Receipt Scanner", path: "/receipt-scanner", icon: <ReceiptLongOutlinedIcon />, isAi: true },
    { label: "Analytics & Insights", path: "/analytics", icon: <InsightsOutlinedIcon /> },
  ];

  return (
    <Box
      sx={{
        width: 260,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "#0F172A", // Deep Navy / Slate 900
        color: "#F8FAFC",
      }}
    >
      {/* Brand Header */}
      <Box sx={{ p: 3, display: "flex", alignItems: "center", gap: 1.5 }}>
        <Box
          sx={{
            width: 36,
            height: 36,
            borderRadius: 2,
            backgroundColor: "#6366F1",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#FFFFFF",
            boxShadow: "0 0 16px rgba(99, 102, 241, 0.4)",
          }}
        >
          <AutoAwesomeOutlinedIcon fontSize="small" />
        </Box>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 700, letterSpacing: "-0.02em", color: "#FFFFFF", lineHeight: 1.2 }}>
            Splitwise AI
          </Typography>
          <Typography variant="caption" sx={{ color: "#94A3B8", fontSize: "0.7rem", letterSpacing: "0.04em" }}>
            FINANCIAL INTELLIGENCE
          </Typography>
        </Box>
      </Box>

      <Divider sx={{ borderColor: "rgba(255, 255, 255, 0.08)" }} />

      {/* Navigation List */}
      <Box sx={{ flexGrow: 1, py: 2, px: 1.5 }}>
        <List component="nav" disablePadding>
          {navItems.map((item) => {
            const isActive =
              location.pathname === item.path ||
              (item.path === "/dashboard" && location.pathname === "/");

            return (
              <ListItemButton
                key={item.path}
                component={Link}
                to={item.path}
                onClick={onItemClick}
                sx={{
                  borderRadius: 2,
                  mb: 0.5,
                  py: 1,
                  px: 1.5,
                  backgroundColor: isActive ? "rgba(99, 102, 241, 0.18)" : "transparent",
                  color: isActive ? "#FFFFFF" : "#94A3B8",
                  "&:hover": {
                    backgroundColor: isActive ? "rgba(99, 102, 241, 0.25)" : "rgba(255, 255, 255, 0.05)",
                    color: "#FFFFFF",
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    color: isActive ? "#818CF8" : "#94A3B8",
                    minWidth: 38,
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: "0.875rem",
                    fontWeight: isActive ? 600 : 500,
                  }}
                />
                {item.isAi && (
                  <Chip
                    label="AI"
                    size="small"
                    sx={{
                      height: 18,
                      fontSize: "0.65rem",
                      fontWeight: 700,
                      backgroundColor: "#6366F1",
                      color: "#FFFFFF",
                    }}
                  />
                )}
              </ListItemButton>
            );
          })}
        </List>
      </Box>

      {/* User Profile / Logout Footer */}
      <Box sx={{ p: 2, borderTop: "1px solid rgba(255, 255, 255, 0.08)" }}>
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, overflow: "hidden" }}>
            <Avatar
              sx={{
                width: 34,
                height: 34,
                bgcolor: "#6366F1",
                fontSize: "0.875rem",
                fontWeight: 600,
              }}
            >
              {user?.name ? user.name.charAt(0).toUpperCase() : "U"}
            </Avatar>
            <Box sx={{ overflow: "hidden" }}>
              <Typography variant="body2" sx={{ fontWeight: 600, color: "#FFFFFF", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                {user?.name || "User"}
              </Typography>
              <Typography variant="caption" sx={{ color: "#94A3B8", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap", display: "block" }}>
                {user?.email || ""}
              </Typography>
            </Box>
          </Box>
        </Box>

        <ListItemButton
          onClick={logout}
          sx={{
            borderRadius: 1.5,
            py: 0.75,
            px: 1,
            color: "#EF4444",
            "&:hover": { backgroundColor: "rgba(239, 68, 68, 0.1)" },
          }}
        >
          <ListItemIcon sx={{ color: "#EF4444", minWidth: 32 }}>
            <LogoutOutlinedIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText
            primary="Sign out"
            primaryTypographyProps={{ fontSize: "0.8rem", fontWeight: 600 }}
          />
        </ListItemButton>
      </Box>
    </Box>
  );
}
