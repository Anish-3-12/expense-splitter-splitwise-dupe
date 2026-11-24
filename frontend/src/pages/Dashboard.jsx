import React, { useEffect, useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import {
  Grid,
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  CircularProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Divider,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import GroupsIcon from "@mui/icons-material/Groups";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import AccountBalanceWalletIcon from "@mui/icons-material/AccountBalanceWallet";
import RestaurantIcon from "@mui/icons-material/Restaurant";
import DirectionsCarIcon from "@mui/icons-material/DirectionsCar";
import ShoppingBagIcon from "@mui/icons-material/ShoppingBag";
import CategoryIcon from "@mui/icons-material/Category";
import api from "../api/axios";
import { AuthContext } from "../context/AuthContext";
import MetricCard from "../components/MetricCard";
import PageHeader from "../components/PageHeader";
import EmptyState from "../components/EmptyState";
import CategoryDonutChart from "../components/CategoryDonutChart";
import { formatINR } from "../utils/formatters";

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await api.get("/users/me/dashboard");
      setDashboardData(resp.data);
    } catch (err) {
      console.error("Dashboard fetch error:", err);
      setError("Failed to load dashboard metrics. Backend may be offline.");
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (name) => {
    const n = (name || "").toLowerCase();
    if (n.includes("food") || n.includes("dining")) return <RestaurantIcon fontSize="small" />;
    if (n.includes("transport")) return <DirectionsCarIcon fontSize="small" />;
    if (n.includes("shopping")) return <ShoppingBagIcon fontSize="small" />;
    return <CategoryIcon fontSize="small" />;
  };

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: 400 }}>
        <CircularProgress size={40} thickness={4} />
      </Box>
    );
  }

  const totalSpent = Number(dashboardData?.totalSpent || 0);
  const owedToUser = Number(dashboardData?.totalOwedToUser || 0);
  const userOwes = Number(dashboardData?.totalUserOwes || 0);
  const netBalance = Number(dashboardData?.netTotalBalance || 0);
  const recentGroups = dashboardData?.recentGroups || [];
  const recentExpenses = dashboardData?.recentExpenses || [];

  return (
    <Box>
      <PageHeader
        title={`Welcome back, ${user?.name || "Friend"}`}
        subtitle="Here is your intelligent financial breakdown across all expense groups."
      />

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {/* KPI Metric Cards */}
      <Grid container spacing={2.5} sx={{ mb: 4, width: "100%" }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }} sx={{ display: "flex" }}>
          <MetricCard
            title="Total Paid"
            value={formatINR(totalSpent)}
            subtitle="Lifetime expenses paid by you"
            icon={<AccountBalanceWalletIcon />}
            color="#0F172A"
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }} sx={{ display: "flex" }}>
          <MetricCard
            title="You Are Owed"
            value={formatINR(owedToUser)}
            subtitle="Others owe you in total"
            icon={<ArrowUpwardIcon />}
            color="#059669"
            bgTint="rgba(16, 185, 129, 0.1)"
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }} sx={{ display: "flex" }}>
          <MetricCard
            title="You Owe"
            value={formatINR(userOwes)}
            subtitle="Your pending debts to others"
            icon={<ArrowDownwardIcon />}
            color="#DC2626"
            bgTint="rgba(239, 68, 68, 0.1)"
          />
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }} sx={{ display: "flex" }}>
          <MetricCard
            title="Net Balance"
            value={`${netBalance >= 0 ? "+" : "-"}${formatINR(Math.abs(netBalance))}`}
            subtitle={netBalance >= 0 ? "Overall net positive" : "Overall net negative"}
            icon={<TrendingUpIcon />}
            color={netBalance >= 0 ? "#059669" : "#DC2626"}
            bgTint={netBalance >= 0 ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)"}
          />
        </Grid>
      </Grid>

      {/* Main Grid: Groups & Recent Activity */}
      <Grid container spacing={3} sx={{ width: "100%" }}>
        {/* Left Column: Groups */}
        <Grid size={{ xs: 12, md: 7 }}>
          <Card sx={{ height: "100%" }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  My Expense Groups
                </Typography>
                <Button size="small" onClick={() => navigate("/groups")}>
                  View All ({dashboardData?.totalGroupsCount || 0})
                </Button>
              </Box>

              {recentGroups.length === 0 ? (
                <EmptyState
                  icon={<GroupsIcon fontSize="large" />}
                  title="No groups found"
                  description="Create a group to start splitting bills and scanning receipts with friends."
                  actionText="Create First Group"
                  onAction={() => navigate("/groups/create")}
                />
              ) : (
                <List disablePadding>
                  {recentGroups.map((g, idx) => (
                    <React.Fragment key={g.id}>
                      <ListItem
                        sx={{
                          py: 1.5,
                          px: 2,
                          borderRadius: 2,
                          "&:hover": { backgroundColor: "#F8FAFC" },
                          cursor: "pointer",
                        }}
                        onClick={() => navigate(`/groups/${g.id}`)}
                      >
                        <ListItemIcon>
                          <Avatar sx={{ bgcolor: "#0F172A", width: 40, height: 40, fontWeight: 700 }}>
                            {g.name.charAt(0).toUpperCase()}
                          </Avatar>
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Typography variant="subtitle1" sx={{ fontWeight: 600, color: "text.primary" }}>
                              {g.name}
                            </Typography>
                          }
                          secondary="Active Split Group"
                        />
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/groups/${g.id}`);
                          }}
                        >
                          Open
                        </Button>
                      </ListItem>
                      {idx < recentGroups.length - 1 && <Divider sx={{ my: 0.5 }} />}
                    </React.Fragment>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Right Column: Recent Activity & Quick Actions */}
        <Grid size={{ xs: 12, md: 5 }}>
          <Card sx={{ height: "100%" }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                Recent Transactions
              </Typography>

              {recentExpenses.length === 0 ? (
                <Box sx={{ py: 6, textAlign: "center" }}>
                  <Typography variant="body2" color="text.secondary">
                    No transactions recorded yet.
                  </Typography>
                </Box>
              ) : (
                <List disablePadding>
                  {recentExpenses.slice(0, 5).map((exp, idx) => (
                    <React.Fragment key={exp.id}>
                      <ListItem sx={{ py: 1.25, px: 0, display: "flex", alignItems: "center" }}>
                        <ListItemIcon sx={{ minWidth: 38 }}>
                          <Avatar sx={{ bgcolor: "rgba(99, 102, 241, 0.1)", color: "#6366F1", width: 32, height: 32 }}>
                            {getCategoryIcon(exp.categoryName)}
                          </Avatar>
                        </ListItemIcon>
                        <ListItemText
                          sx={{ mr: 2, minWidth: 0 }}
                          primary={
                            <Typography variant="body2" sx={{ fontWeight: 600, wordBreak: "break-word" }}>
                              {exp.note || "Expense"}
                            </Typography>
                          }
                          secondary={exp.categoryName || "Uncategorized"}
                        />
                        <Box sx={{ textAlign: "right", flexShrink: 0, ml: "auto" }}>
                          <Typography variant="body2" sx={{ fontWeight: 700 }}>
                            {formatINR(exp.amount)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {exp.splitType}
                          </Typography>
                        </Box>
                      </ListItem>
                      {idx < 4 && <Divider sx={{ my: 0.5 }} />}
                    </React.Fragment>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
