import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#0F172A", // Deep Navy / Slate 900
      light: "#334155",
      dark: "#020617",
      contrastText: "#FFFFFF",
    },
    secondary: {
      main: "#6366F1", // Indigo 500 (AI accent)
      light: "#818CF8",
      dark: "#4338CA",
      contrastText: "#FFFFFF",
    },
    success: {
      main: "#10B981", // Emerald 500 (Credits / Succeeded)
      light: "#34D399",
      dark: "#059669",
      contrastText: "#FFFFFF",
    },
    error: {
      main: "#EF4444", // Rose 500 (Debts / Errors)
      light: "#F87171",
      dark: "#DC2626",
      contrastText: "#FFFFFF",
    },
    warning: {
      main: "#F59E0B", // Amber 500 (Review required)
      light: "#FBBF24",
      dark: "#D97706",
      contrastText: "#FFFFFF",
    },
    info: {
      main: "#3B82F6", // Blue 500
      light: "#60A5FA",
      dark: "#2563EB",
    },
    background: {
      default: "#F8FAFC", // Clean light slate
      paper: "#FFFFFF",
    },
    text: {
      primary: "#0F172A",
      secondary: "#64748B", // Slate 500
      disabled: "#94A3B8",
    },
    divider: "#E2E8F0",
  },
  typography: {
    fontFamily: [
      "Inter",
      "-apple-system",
      "BlinkMacSystemFont",
      '"Segoe UI"',
      "Roboto",
      '"Helvetica Neue"',
      "Arial",
      "sans-serif",
    ].join(","),
    h4: {
      fontWeight: 700,
      letterSpacing: "-0.02em",
      color: "#0F172A",
    },
    h5: {
      fontWeight: 600,
      letterSpacing: "-0.01em",
      color: "#0F172A",
    },
    h6: {
      fontWeight: 600,
      letterSpacing: "-0.01em",
      color: "#0F172A",
    },
    subtitle1: {
      fontWeight: 500,
      color: "#64748B",
    },
    subtitle2: {
      fontWeight: 500,
      color: "#64748B",
    },
    button: {
      textTransform: "none",
      fontWeight: 600,
      letterSpacing: "0.01em",
    },
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          boxShadow: "none",
          padding: "8px 16px",
          "&:hover": {
            boxShadow: "0 2px 4px rgba(15, 23, 42, 0.08)",
          },
        },
        containedPrimary: {
          backgroundColor: "#0F172A",
          "&:hover": {
            backgroundColor: "#1E293B",
          },
        },
        containedSecondary: {
          backgroundColor: "#6366F1",
          "&:hover": {
            backgroundColor: "#4F46E5",
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)",
          border: "1px solid #E2E8F0",
          backgroundColor: "#FFFFFF",
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
        },
      },
    },
    MuiTextField: {
      defaultProps: {
        size: "small",
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          backgroundColor: "#FFFFFF",
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          fontWeight: 500,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderColor: "#F1F5F9",
          padding: "12px 16px",
        },
        head: {
          fontWeight: 600,
          color: "#475569",
          backgroundColor: "#F8FAFC",
        },
      },
    },
  },
});

export default theme;
