import React, { useState } from "react";
import { Box, Typography, Grid } from "@mui/material";

const CATEGORY_COLORS = [
  "#6366F1", // Indigo
  "#10B981", // Emerald
  "#F59E0B", // Amber
  "#3B82F6", // Blue
  "#EC4899", // Pink
  "#8B5CF6", // Purple
  "#14B8A6", // Teal
  "#F97316", // Orange
  "#64748B", // Slate
];

export default function CategoryDonutChart({ data = [], size = 180 }) {
  const [hoveredIdx, setHoveredIdx] = useState(null);

  if (!data || data.length === 0) {
    return (
      <Box sx={{ py: 4, textAlign: "center" }}>
        <Typography variant="body2" color="text.secondary">
          No category spending data yet.
        </Typography>
      </Box>
    );
  }

  const total = data.reduce((acc, it) => acc + Number(it.totalAmount || 0), 0);
  if (total <= 0) {
    return (
      <Box sx={{ py: 4, textAlign: "center" }}>
        <Typography variant="body2" color="text.secondary">
          No expenses recorded.
        </Typography>
      </Box>
    );
  }

  const radius = size / 2;
  const strokeWidth = 24;
  const innerRadius = radius - strokeWidth;
  const circumference = 2 * Math.PI * innerRadius;

  let accumulatedPercent = 0;

  const slices = data.map((item, idx) => {
    const amount = Number(item.totalAmount || 0);
    const percent = total > 0 ? amount / total : 0;
    const strokeDasharray = `${percent * circumference} ${circumference}`;
    const strokeDashoffset = -(accumulatedPercent * circumference);
    accumulatedPercent += percent;
    const color = CATEGORY_COLORS[idx % CATEGORY_COLORS.length];

    return {
      ...item,
      amount,
      percent: (percent * 100).toFixed(1),
      strokeDasharray,
      strokeDashoffset,
      color,
      index: idx,
    };
  });

  const activeSlice = hoveredIdx !== null ? slices[hoveredIdx] : null;

  return (
    <Box sx={{ display: "flex", flexDirection: { xs: "column", md: "row" }, alignItems: "center", gap: 3 }}>
      {/* Donut Graphic */}
      <Box sx={{ position: "relative", width: size, height: size, flexShrink: 0 }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {slices.map((s, idx) => (
            <circle
              key={idx}
              cx={radius}
              cy={radius}
              r={innerRadius}
              fill="transparent"
              stroke={s.color}
              strokeWidth={hoveredIdx === idx ? strokeWidth + 4 : strokeWidth}
              strokeDasharray={s.strokeDasharray}
              strokeDashoffset={s.strokeDashoffset}
              strokeLinecap="round"
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
              style={{
                cursor: "pointer",
                transition: "all 0.2s ease",
                transformOrigin: "center",
                transform: "rotate(-90deg)",
              }}
            />
          ))}
        </svg>

        {/* Center label */}
        <Box
          sx={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            pointerEvents: "none",
          }}
        >
          <Typography variant="caption" sx={{ color: "text.secondary", fontWeight: 600, fontSize: "0.7rem" }}>
            {activeSlice ? activeSlice.category : "TOTAL"}
          </Typography>
          <Typography variant="body1" sx={{ fontWeight: 700, color: "text.primary" }}>
            ₹{(activeSlice ? activeSlice.amount : total).toLocaleString("en-IN", { maximumFractionDigits: 0 })}
          </Typography>
          {activeSlice && (
            <Typography variant="caption" sx={{ color: "primary.main", fontWeight: 600 }}>
              {activeSlice.percent}%
            </Typography>
          )}
        </Box>
      </Box>

      {/* Legend list */}
      <Box sx={{ flexGrow: 1, width: "100%" }}>
        <Grid container spacing={1}>
          {slices.map((s, idx) => (
            <Grid item xs={6} sm={4} md={6} key={idx}>
              <Box
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                  p: 0.5,
                  borderRadius: 1,
                  cursor: "pointer",
                  backgroundColor: hoveredIdx === idx ? "rgba(99, 102, 241, 0.08)" : "transparent",
                  transition: "background-color 0.2s ease",
                }}
              >
                <Box
                  sx={{
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    backgroundColor: s.color,
                    flexShrink: 0,
                  }}
                />
                <Box sx={{ overflow: "hidden" }}>
                  <Typography variant="body2" sx={{ fontWeight: 600, fontSize: "0.8rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {s.category}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    ₹{s.amount.toLocaleString("en-IN")} ({s.percent}%)
                  </Typography>
                </Box>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Box>
  );
}
