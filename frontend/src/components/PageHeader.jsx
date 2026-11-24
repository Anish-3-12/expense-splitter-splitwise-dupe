import React from "react";
import { Box, Typography, Button } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useNavigate } from "react-router-dom";

export default function PageHeader({ title, subtitle, backUrl, actions, action }) {
  const navigate = useNavigate();
  const actionContent = action || actions;

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: { xs: "column", sm: "row" },
        justifyContent: "space-between",
        alignItems: { xs: "flex-start", sm: "center" },
        gap: 2,
        mb: 3,
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
        {backUrl && (
          <Button
            variant="outlined"
            size="small"
            onClick={() => navigate(backUrl)}
            sx={{ minWidth: 36, width: 36, height: 36, p: 0, borderRadius: "50%" }}
          >
            <ArrowBackIcon fontSize="small" />
          </Button>
        )}
        <Box>
          <Typography variant="h5" component="h1" sx={{ fontWeight: 700 }}>
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {subtitle}
            </Typography>
          )}
        </Box>
      </Box>

      {actionContent && (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, flexWrap: "wrap" }}>
          {actionContent}
        </Box>
      )}
    </Box>
  );
}
