import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  MenuItem,
  CircularProgress,
  Alert,
  Stack,
  LinearProgress,
  Chip,
  Paper,
} from "@mui/material";
import {
  TrendingUp as TrendingUpIcon,
  PieChart as PieChartIcon,
  WarningAmber as WarningIcon,
  AccountBalanceWallet as WalletIcon,
  Groups as GroupsIcon,
  ReceiptLong as ReceiptIcon,
} from "@mui/icons-material";
import api from "../api/axios";
import PageHeader from "../components/PageHeader";
import MetricCard from "../components/MetricCard";
import MonthlyBarChart from "../components/MonthlyBarChart";
import CategoryDonutChart from "../components/CategoryDonutChart";
import EmptyState from "../components/EmptyState";
import { formatINR } from "../utils/formatters";

export default function Analytics() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialGroupId = searchParams.get("groupId") || "";

  const [groups, setGroups] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState(initialGroupId);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchGroups();
  }, []);

  useEffect(() => {
    if (selectedGroupId) {
      fetchAnalytics(selectedGroupId);
    }
  }, [selectedGroupId]);

  const fetchGroups = async () => {
    try {
      const res = await api.get("/groups");
      const list = res.data || [];
      setGroups(list);
      if (!selectedGroupId && list.length > 0) {
        setSelectedGroupId(String(list[0].id));
      } else if (list.length === 0) {
        setLoading(false);
      }
    } catch (err) {
      console.error("Failed to load groups:", err);
      setLoading(false);
    }
  };

  const fetchAnalytics = async (gid) => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/groups/${gid}/analytics/overview`);
      setAnalytics(res.data);
    } catch (err) {
      console.error("Failed to load analytics:", err);
      setError(err?.response?.data?.message || "Failed to load group analytics.");
      setAnalytics(null);
    } finally {
      setLoading(false);
    }
  };

  const handleGroupChange = (e) => {
    const val = e.target.value;
    setSelectedGroupId(val);
    setSearchParams({ groupId: val });
  };

  const totalSpending = Number(analytics?.totalSpending ?? analytics?.totalExpenditure ?? 0);
  const expenseCount = analytics?.expenseCount || 0;
  const avgPerExpense = analytics?.averageExpense
    ? Number(analytics.averageExpense).toFixed(2)
    : (expenseCount > 0 ? (totalSpending / expenseCount).toFixed(2) : "0.00");
  const anomalies = analytics?.anomalies || [];
  const memberSpending = analytics?.memberSpending || [];
  const categoryData = analytics?.categoryBreakdown || [];
  const monthlyData = analytics?.monthlySpending ?? analytics?.monthlyTrends ?? [];

  return (
    <Box>
      <PageHeader
        title="Spending Intelligence & Analytics"
        subtitle="Track cash burn, category breakdowns, member share distributions, and AI anomaly detection."
        action={
          <TextField
            select
            size="small"
            value={selectedGroupId}
            onChange={handleGroupChange}
            sx={{ minWidth: 200, bgcolor: "background.paper" }}
          >
            {groups.map((g) => (
              <MenuItem key={g.id} value={String(g.id)}>
                {g.name}
              </MenuItem>
            ))}
          </TextField>
        }
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
          <CircularProgress />
        </Box>
      ) : !analytics ? (
        <EmptyState
          icon={TrendingUpIcon}
          title="No analytics available"
          description="Select a group with recorded expenses to view trends and anomaly detection."
        />
      ) : (
        <Stack spacing={3}>
          {/* Top Metric Cards */}
          <Grid container spacing={3} sx={{ width: "100%" }}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }} sx={{ display: "flex" }}>
              <MetricCard
                title="Total Group Spend"
                value={formatINR(totalSpending)}
                subtitle={`Across ${expenseCount} expenses`}
                icon={WalletIcon}
                color="primary"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }} sx={{ display: "flex" }}>
              <MetricCard
                title="Average Expense"
                value={formatINR(avgPerExpense)}
                subtitle="Per transaction"
                icon={ReceiptIcon}
                color="secondary"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }} sx={{ display: "flex" }}>
              <MetricCard
                title="Active Members"
                value={memberSpending.length}
                subtitle="Contributing to spend"
                icon={GroupsIcon}
                color="info"
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 3 }} sx={{ display: "flex" }}>
              <MetricCard
                title="Review Suggestions"
                value={anomalies.length}
                subtitle={anomalies.length > 0 ? "Requires review" : "Spending healthy"}
                icon={WarningIcon}
                color={anomalies.length > 0 ? "warning" : "success"}
              />
            </Grid>
          </Grid>

          {/* Charts Row */}
          <Grid container spacing={3} sx={{ width: "100%" }}>
            <Grid size={{ xs: 12, md: 7 }}>
              <MonthlyBarChart data={monthlyData} title="Monthly Spending Trajectory" />
            </Grid>
            <Grid size={{ xs: 12, md: 5 }}>
              <CategoryDonutChart data={categoryData} title="Spending by Category" />
            </Grid>
          </Grid>

          {/* Member Distribution & AI Anomaly Detection */}
          <Grid container spacing={3} sx={{ width: "100%" }}>
            {/* Member Contributions */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Card sx={{ height: "100%" }}>
                <CardContent sx={{ p: 3 }}>
                  <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                    Member Spending Breakdown
                  </Typography>
                  <Typography variant="body2" sx={{ color: "text.secondary", mb: 3 }}>
                    Share of total group expenses paid out-of-pocket by each member.
                  </Typography>

                  {memberSpending.length === 0 ? (
                    <Typography variant="body2" sx={{ color: "text.secondary", py: 2 }}>
                      No member spend recorded yet.
                    </Typography>
                  ) : (
                    <Stack spacing={2.5}>
                      {memberSpending.map((m) => {
                        const paid = Number(m.totalPaid || 0);
                        const pct = m.percentage != null
                          ? Number(m.percentage)
                          : (totalSpending > 0 ? (paid / totalSpending) * 100 : 0);
                        return (
                          <Box key={m.userId || m.userName}>
                            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                {m.userName || `Member #${m.userId}`}
                              </Typography>
                              <Typography variant="body2" sx={{ fontWeight: 700 }}>
                                ₹{paid.toFixed(2)} ({pct.toFixed(2)}%)
                              </Typography>
                            </Box>
                            <LinearProgress
                              variant="determinate"
                              value={Math.min(100, Math.max(0, pct))}
                              sx={{
                                height: 8,
                                borderRadius: 4,
                                bgcolor: "slate.100",
                                "& .MuiLinearProgress-bar": { borderRadius: 4, bgcolor: "primary.main" },
                              }}
                            />
                          </Box>
                        );
                      })}
                    </Stack>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* AI Anomaly Detection Feed */}
            <Grid size={{ xs: 12, md: 6 }}>
              <Card sx={{ height: "100%" }}>
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                    <WarningIcon sx={{ color: anomalies.length > 0 ? "warning.main" : "success.main" }} />
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>
                      AI Spending Review Suggestions
                    </Typography>
                    <Chip
                      size="small"
                      label={
                        analytics?.anomalyMethod === "ISOLATION_FOREST"
                          ? "Scikit-Learn Isolation Forest"
                          : analytics?.anomalyMethod === "STATISTICAL_IQR"
                          ? "Statistical IQR Baseline"
                          : (analytics?.expenseCount >= 10 ? "Scikit-Learn Isolation Forest" : "Statistical IQR Baseline")
                      }
                      color="secondary"
                      variant="outlined"
                      sx={{ ml: "auto", fontSize: "0.68rem" }}
                    />
                  </Box>
                  <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>
                    Flagged transactions with unusually high amounts or unusual spend patterns for human review.
                  </Typography>

                  {anomalies.length === 0 ? (
                    <Paper
                      elevation={0}
                      sx={{
                        p: 3,
                        textAlign: "center",
                        bgcolor: "emerald.50",
                        borderRadius: 2,
                        border: "1px solid",
                        borderColor: "emerald.200",
                      }}
                    >
                      <Typography variant="body2" sx={{ fontWeight: 600, color: "emerald.700" }}>
                        All transactions within normal statistical variance.
                      </Typography>
                      <Typography variant="caption" sx={{ color: "emerald.600" }}>
                        No review suggestions flagged for this group.
                      </Typography>
                    </Paper>
                  ) : (
                    <Stack spacing={1.5}>
                      {anomalies.map((anom) => (
                        <Paper
                          key={anom.expenseId}
                          variant="outlined"
                          sx={{
                            p: 2,
                            borderRadius: 2,
                            borderColor: "warning.main",
                            bgcolor: "warning.50",
                          }}
                        >
                          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                            <Box>
                              <Typography variant="subtitle2" sx={{ fontWeight: 700, color: "warning.dark" }}>
                                {anom.expenseNote || anom.description || `Expense #${anom.expenseId}`} — {formatINR(anom.amount)}
                              </Typography>
                              <Typography variant="caption" sx={{ color: "text.secondary", display: "block", mt: 0.5 }}>
                                Paid by {anom.payerName || "Group Member"} • Category: {anom.categoryName || "General"}
                              </Typography>
                            </Box>
                            <Chip
                              size="small"
                              label="Review Suggestion"
                              color="warning"
                              sx={{ fontWeight: 600, fontSize: "0.7rem", height: 22 }}
                            />
                          </Box>
                          <Typography variant="caption" sx={{ color: "text.secondary", display: "block", mt: 1 }}>
                            <strong>Reason:</strong> {anom.reason}
                          </Typography>
                        </Paper>
                      ))}
                    </Stack>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Stack>
      )}
    </Box>
  );
}
