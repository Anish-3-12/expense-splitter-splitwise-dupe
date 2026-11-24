import React from "react";
import { Chip, Box, Typography } from "@mui/material";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";

export default function BalanceIndicator({ amount, currency = "INR", showDetails = false }) {
  const num = Number(amount || 0);

  if (Math.abs(num) < 0.01) {
    return (
      <Chip
        icon={<CheckCircleOutlineIcon fontSize="small" />}
        label="Settled Up"
        size="small"
        sx={{
          backgroundColor: "#F1F5F9",
          color: "#475569",
          fontWeight: 600,
        }}
      />
    );
  }

  const isPositive = num > 0;
  const formatted = Math.abs(num).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return (
    <Box sx={{ display: "inline-flex", alignItems: "center", gap: 0.5 }}>
      <Chip
        icon={isPositive ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />}
        label={isPositive ? `+₹${formatted}` : `-₹${formatted}`}
        size="small"
        sx={{
          backgroundColor: isPositive ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
          color: isPositive ? "#059669" : "#DC2626",
          fontWeight: 700,
          border: `1px solid ${isPositive ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)"}`,
        }}
      />
      {showDetails && (
        <Typography variant="caption" sx={{ color: isPositive ? "success.dark" : "error.dark", fontWeight: 500 }}>
          {isPositive ? "owes you" : "you owe"}
        </Typography>
      )}
    </Box>
  );
}
