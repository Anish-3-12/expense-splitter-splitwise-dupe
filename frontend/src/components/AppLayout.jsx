import React, { useState } from "react";
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Button,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import AddIcon from "@mui/icons-material/Add";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import Sidebar from "./Sidebar";
import { useNavigate } from "react-router-dom";

export default function AppLayout({ children }) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  return (
    <Box sx={{ display: "flex", minHeight: "100vh", backgroundColor: "background.default" }}>
      {/* Desktop Sidebar */}
      {!isMobile && (
        <Box sx={{ width: 260, flexShrink: 0, position: "sticky", top: 0, height: "100vh" }}>
          <Sidebar />
        </Box>
      )}

      {/* Mobile Drawer */}
      {isMobile && (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            "& .MuiDrawer-paper": { boxSizing: "border-box", width: 260 },
          }}
        >
          <Sidebar onItemClick={() => setMobileOpen(false)} />
        </Drawer>
      )}

      {/* Main Content Area */}
      <Box sx={{ flexGrow: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* Top Navbar */}
        <AppBar
          position="sticky"
          elevation={0}
          sx={{
            backgroundColor: "#FFFFFF",
            borderBottom: "1px solid #E2E8F0",
            color: "text.primary",
          }}
        >
          <Toolbar sx={{ justifyContent: "space-between", px: { xs: 2, sm: 3 } }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              {isMobile && (
                <IconButton
                  color="inherit"
                  edge="start"
                  onClick={handleDrawerToggle}
                  sx={{ mr: 1 }}
                >
                  <MenuIcon />
                </IconButton>
              )}
              <Typography variant="h6" sx={{ fontWeight: 700, fontSize: { xs: "1rem", sm: "1.125rem" } }}>
                Splitwise AI
              </Typography>
            </Box>

            {/* Quick Actions */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
              <Button
                variant="outlined"
                color="secondary"
                size="small"
                startIcon={<ReceiptLongIcon />}
                onClick={() => navigate("/receipt-scanner")}
                sx={{ display: { xs: "none", sm: "inline-flex" } }}
              >
                Scan Receipt
              </Button>
              <Button
                variant="contained"
                color="primary"
                size="small"
                startIcon={<AddIcon />}
                onClick={() => navigate("/groups/create")}
              >
                New Group
              </Button>
            </Box>
          </Toolbar>
        </AppBar>

        {/* Page Content Body */}
        <Box component="main" sx={{ flexGrow: 1, p: { xs: 2, sm: 3, md: 4 }, maxWidth: 1280, width: "100%", mx: "auto" }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
}
