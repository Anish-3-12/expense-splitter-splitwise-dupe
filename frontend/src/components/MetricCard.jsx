import React from "react";
import { Card, CardContent, Typography, Box } from "@mui/material";

export default function MetricCard({ title, value, subtitle, icon, color = "primary.main", bgTint }) {
  const renderIcon = () => {
    if (!icon) return null;
    if (React.isValidElement(icon)) return icon;
    if (typeof icon === "function" || typeof icon === "object") {
      return React.createElement(icon, { fontSize: "small" });
    }
    return null;
  };

  return (
    <Card sx={{ height: "100%", width: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
      <CardContent sx={{ p: 2.5, "&:last-child": { pb: 2.5 } }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 1.5 }}>
          <Typography variant="body2" sx={{ fontWeight: 600, color: "text.secondary", textTransform: "uppercase", fontSize: "0.75rem", letterSpacing: "0.05em" }}>
            {title}
          </Typography>
          {icon && (
            <Box
              sx={{
                p: 1,
                borderRadius: 2,
                backgroundColor: bgTint || "rgba(15, 23, 42, 0.05)",
                color: color,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {renderIcon()}
            </Box>
          )}
        </Box>
        <Typography variant="h4" sx={{ fontWeight: 700, color: color }}>
          {value}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}
