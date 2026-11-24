import React, { useState } from "react";
import { Box, Typography } from "@mui/material";

export default function MonthlyBarChart({ data = [], height = 220 }) {
  const [hoveredIdx, setHoveredIdx] = useState(null);

  if (!data || data.length === 0) {
    return (
      <Box sx={{ height, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Typography variant="body2" color="text.secondary">
          No monthly spending records yet.
        </Typography>
      </Box>
    );
  }

  const values = data.map((d) => Number(d.amount || 0));
  const maxVal = Math.max(...values, 100);
  const chartHeight = height - 50; // reserve space for labels
  const barWidth = 36;
  const gap = 24;
  const totalWidth = Math.max(data.length * (barWidth + gap) + 40, 300);

  return (
    <Box sx={{ width: "100%", overflowX: "auto" }}>
      <svg width="100%" height={height} viewBox={`0 0 ${totalWidth} ${height}`} style={{ minWidth: totalWidth }}>
        {/* Background gridlines */}
        {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
          const y = chartHeight - pct * (chartHeight - 20) + 10;
          return (
            <g key={idx}>
              <line x1="20" y1={y} x2={totalWidth - 20} y2={y} stroke="#F1F5F9" strokeWidth="1" strokeDasharray="4 4" />
              <text x="20" y={y - 4} fill="#94A3B8" fontSize="10" fontFamily="sans-serif">
                ₹{(maxVal * pct).toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* Bars */}
        {data.map((item, i) => {
          const val = Number(item.amount || 0);
          const barH = Math.max((val / maxVal) * (chartHeight - 20), 4);
          const x = 50 + i * (barWidth + gap);
          const y = chartHeight - barH + 10;
          const isHovered = hoveredIdx === i;

          return (
            <g
              key={i}
              onMouseEnter={() => setHoveredIdx(i)}
              onMouseLeave={() => setHoveredIdx(null)}
              style={{ cursor: "pointer" }}
            >
              {/* Bar Rect */}
              <rect
                x={x}
                y={y}
                width={barWidth}
                height={barH}
                rx="6"
                fill={isHovered ? "#4F46E5" : "#6366F1"}
                opacity={isHovered ? 1 : 0.85}
                style={{ transition: "all 0.2s ease" }}
              />

              {/* Month label */}
              <text
                x={x + barWidth / 2}
                y={chartHeight + 30}
                textAnchor="middle"
                fill={isHovered ? "#0F172A" : "#64748B"}
                fontSize="11"
                fontWeight={isHovered ? 600 : 500}
                fontFamily="sans-serif"
              >
                {item.month || `M${i + 1}`}
              </text>

              {/* Hover Value Tooltip */}
              {isHovered && (
                <g>
                  <rect
                    x={x + barWidth / 2 - 40}
                    y={Math.max(y - 28, 4)}
                    width="80"
                    height="22"
                    rx="4"
                    fill="#0F172A"
                  />
                  <text
                    x={x + barWidth / 2}
                    y={Math.max(y - 13, 19)}
                    textAnchor="middle"
                    fill="#FFFFFF"
                    fontSize="10"
                    fontWeight="bold"
                    fontFamily="sans-serif"
                  >
                    ₹{val.toLocaleString("en-IN")}
                  </text>
                </g>
              )}
            </g>
          );
        })}
      </svg>
    </Box>
  );
}
