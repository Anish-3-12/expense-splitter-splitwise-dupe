import React from "react";
import { Box, Typography, Button } from "@mui/material";

export default function EmptyState({ icon, title, description, actionText, actionLabel, onAction }) {
  const label = actionLabel || actionText;

  const renderIcon = () => {
    if (!icon) return null;
    if (React.isValidElement(icon)) return icon;
    if (typeof icon === "function" || typeof icon === "object") {
      return React.createElement(icon, { sx: { fontSize: 40 } });
    }
    return null;
  };

  return (
    <Box
      sx={{
        py: 8,
        px: 3,
        textAlign: "center",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        borderRadius: 3,
        border: "1px dashed #CBD5E1",
        backgroundColor: "#F8FAFC",
        my: 2,
      }}
    >
      {icon && (
        <Box
          sx={{
            mb: 2,
            p: 2,
            borderRadius: "50%",
            backgroundColor: "#FFFFFF",
            boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
            color: "text.secondary",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {renderIcon()}
        </Box>
      )}
      <Typography variant="h6" sx={{ fontWeight: 600, color: "text.primary", mb: 0.5 }}>
        {title}
      </Typography>
      {description && (
        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 450, mb: 3 }}>
          {description}
        </Typography>
      )}
      {label && onAction && (
        <Button variant="contained" color="primary" onClick={onAction}>
          {label}
        </Button>
      )}
    </Box>
  );
}
