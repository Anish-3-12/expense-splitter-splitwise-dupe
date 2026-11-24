import React from "react";
import { Chip } from "@mui/material";

export default function StatusBadge({ status }) {
  if (!status) return null;

  const normalized = status.toUpperCase();

  const configs = {
    CONFIRMED: { label: "Confirmed", bg: "rgba(16, 185, 129, 0.12)", color: "#059669" },
    EXTRACTED: { label: "AI Extracted", bg: "rgba(99, 102, 241, 0.12)", color: "#4F46E5" },
    PROCESSING: { label: "Processing...", bg: "rgba(59, 130, 246, 0.12)", color: "#2563EB" },
    UPLOADED: { label: "Uploaded", bg: "rgba(148, 163, 184, 0.15)", color: "#475569" },
    FAILED: { label: "Failed", bg: "rgba(239, 68, 68, 0.12)", color: "#DC2626" },
    NORMAL: { label: "Normal Pattern", bg: "rgba(16, 185, 129, 0.12)", color: "#059669" },
    UNUSUAL: { label: "Unusual Expense", bg: "rgba(245, 158, 11, 0.15)", color: "#D97706" },
    REQUIRES_REVIEW: { label: "Requires Review", bg: "rgba(239, 68, 68, 0.15)", color: "#DC2626" },
    INSUFFICIENT_DATA: { label: "Insufficient Data", bg: "rgba(148, 163, 184, 0.15)", color: "#64748B" },
  };

  const cfg = configs[normalized] || { label: status, bg: "#F1F5F9", color: "#475569" };

  return (
    <Chip
      size="small"
      label={cfg.label}
      sx={{
        backgroundColor: cfg.bg,
        color: cfg.color,
        fontWeight: 600,
        fontSize: "0.75rem",
        borderRadius: "6px",
      }}
    />
  );
}
