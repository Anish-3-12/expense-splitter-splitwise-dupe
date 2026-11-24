import React, { useEffect, useState, useContext } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Avatar,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Stack,
  Breadcrumbs,
  Link as MuiLink,
  Divider,
  Paper,
  Tooltip,
} from "@mui/material";
import {
  ArrowBack as ArrowBackIcon,
  Add as AddIcon,
  ReceiptLong as ReceiptIcon,
  CameraAlt as CameraAltIcon,
  AccountBalanceWallet as WalletIcon,
  PersonAdd as PersonAddIcon,
  Insights as InsightsIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Category as CategoryIcon,
} from "@mui/icons-material";
import api from "../api/axios";
import { AuthContext } from "../context/AuthContext";
import PageHeader from "../components/PageHeader";
import BalanceIndicator from "../components/BalanceIndicator";
import EmptyState from "../components/EmptyState";
import StatusBadge from "../components/StatusBadge";
import { formatINR } from "../utils/formatters";

export default function GroupDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);

  const [tab, setTab] = useState(0);
  const [group, setGroup] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [balances, setBalances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Add Member
  const [openAddMember, setOpenAddMember] = useState(false);
  const [memberEmail, setMemberEmail] = useState("");
  const [addingMember, setAddingMember] = useState(false);
  const [memberError, setMemberError] = useState("");

  // Settlement Dialog
  const [openSettle, setOpenSettle] = useState(false);
  const [fromUserId, setFromUserId] = useState("");
  const [toUserId, setToUserId] = useState("");
  const [settleAmount, setSettleAmount] = useState("");
  const [settling, setSettling] = useState(false);
  const [settleError, setSettleError] = useState("");

  const fetchAll = async () => {
    try {
      setLoading(true);
      setError(null);

      const [groupRes, expRes, balRes] = await Promise.all([
        api.get(`/groups/${id}`),
        api.get(`/groups/${id}/expenses`).catch(() => ({ data: [] })),
        api.get(`/groups/${id}/balances`).catch(() => ({ data: [] })),
      ]);

      setGroup(groupRes.data);
      setExpenses(Array.isArray(expRes.data) ? expRes.data : []);
      setBalances(Array.isArray(balRes.data) ? balRes.data : []);
    } catch (err) {
      console.error("Failed to load group:", err);
      setError(err?.response?.data?.message || "Failed to load group details.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
  }, [id]);

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!memberEmail.trim()) return;
    try {
      setAddingMember(true);
      setMemberError("");
      await api.post(`/groups/${id}/members`, { email: memberEmail.trim(), role: "MEMBER" });
      setMemberEmail("");
      setOpenAddMember(false);
      fetchAll();
    } catch (err) {
      console.error("Add member error:", err);
      setMemberError(err?.response?.data?.message || "Failed to add member. Check email address.");
    } finally {
      setAddingMember(false);
    }
  };

  const handleRecordSettlement = async (e) => {
    e.preventDefault();
    if (!fromUserId || !toUserId || !settleAmount || Number(settleAmount) <= 0) {
      setSettleError("Please specify payer, recipient, and a positive amount.");
      return;
    }
    if (fromUserId === toUserId) {
      setSettleError("Payer and recipient must be different members.");
      return;
    }

    try {
      setSettling(true);
      setSettleError("");
      await api.post(`/groups/${id}/settlements`, {
        fromUserId: Number(fromUserId),
        toUserId: Number(toUserId),
        amount: Number(settleAmount),
      });
      setOpenSettle(false);
      setFromUserId("");
      setToUserId("");
      setSettleAmount("");
      fetchAll();
    } catch (err) {
      console.error("Settlement error:", err);
      setSettleError(err?.response?.data?.message || "Failed to record settlement.");
    } finally {
      setSettling(false);
    }
  };

  const openQuickSettle = (debtorId, creditorId, amount) => {
    setFromUserId(debtorId ? String(debtorId) : "");
    setToUserId(creditorId ? String(creditorId) : "");
    setSettleAmount(amount ? String(Math.abs(amount).toFixed(2)) : "");
    setSettleError("");
    setOpenSettle(true);
  };

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 10 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !group) {
    return (
      <Box sx={{ maxWidth: 600, mx: "auto", py: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || "Group not found"}
        </Alert>
        <Button variant="outlined" startIcon={<ArrowBackIcon />} onClick={() => navigate("/groups")}>
          Back to Groups
        </Button>
      </Box>
    );
  }

  const members = group.members || [];
  const totalGroupExpense = expenses.reduce((acc, curr) => acc + (Number(curr.amount) || 0), 0);

  // Current user's balance in this group
  const myBalanceObj = balances.find((b) => b.userId === user?.id || b.email === user?.email);
  const myNetBalance = myBalanceObj ? Number(myBalanceObj.netBalance || 0) : 0;

  return (
    <Box>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <MuiLink
          component="button"
          underline="hover"
          color="inherit"
          onClick={() => navigate("/groups")}
          sx={{ display: "flex", alignItems: "center", gap: 0.5, cursor: "pointer" }}
        >
          <ArrowBackIcon fontSize="small" /> Groups
        </MuiLink>
        <Typography color="text.primary">{group.name}</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box
        sx={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 2,
          mb: 3,
        }}
      >
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 0.5 }}>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
              {group.name}
            </Typography>
            <Chip
              size="small"
              label={`${members.length} members`}
              sx={{ fontWeight: 600, bgcolor: "slate.100" }}
            />
          </Box>
          <Typography variant="body2" sx={{ color: "text.secondary" }}>
            Total Group Spending: <strong>₹{totalGroupExpense.toFixed(2)}</strong> • Created{" "}
            {group.createdAt ? new Date(group.createdAt).toLocaleDateString() : "recently"}
          </Typography>
        </Box>

        <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap" }}>
          <Button
            variant="outlined"
            startIcon={<CameraAltIcon />}
            onClick={() => navigate(`/receipt-scanner?groupId=${id}`)}
          >
            Scan Receipt
          </Button>
          <Button
            variant="outlined"
            startIcon={<WalletIcon />}
            onClick={() => {
              setFromUserId("");
              setToUserId("");
              setSettleAmount("");
              setOpenSettle(true);
            }}
          >
            Settle Up
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate(`/groups/${id}/add-expense`)}
          >
            Add Expense
          </Button>
        </Box>
      </Box>

      {/* Group Net Status Card */}
      <Card sx={{ mb: 3, bgcolor: "background.paper", border: "1px solid", borderColor: "divider" }}>
        <CardContent sx={{ p: 2.5 }}>
          <Grid container spacing={2} alignItems="center" sx={{ width: "100%" }}>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Typography variant="caption" sx={{ color: "text.secondary", textTransform: "uppercase", fontWeight: 600 }}>
                Your Balance in this Group
              </Typography>
              <Box sx={{ mt: 0.5 }}>
                <BalanceIndicator amount={myNetBalance} size="large" />
              </Box>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }}>
              <Typography variant="caption" sx={{ color: "text.secondary", textTransform: "uppercase", fontWeight: 600 }}>
                Total Recorded Expenses
              </Typography>
              <Typography variant="h6" sx={{ fontWeight: 700, mt: 0.5 }}>
                {formatINR(totalGroupExpense)} ({expenses.length} bills)
              </Typography>
            </Grid>
            <Grid size={{ xs: 12, sm: 4 }} sx={{ textAlign: { sm: "right" } }}>
              <Button
                variant="text"
                size="small"
                startIcon={<InsightsIcon />}
                onClick={() => navigate(`/analytics?groupId=${id}`)}
              >
                View Deep Insights & Trends
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 3 }}>
        <Tabs value={tab} onChange={(e, val) => setTab(val)}>
          <Tab label={`Expenses (${expenses.length})`} />
          <Tab label={`Balances (${balances.length})`} />
          <Tab label={`Members (${members.length})`} />
        </Tabs>
      </Box>

      {/* Tab 0: Expenses */}
      {tab === 0 && (
        <Box>
          {expenses.length === 0 ? (
            <EmptyState
              icon={ReceiptIcon}
              title="No expenses logged yet"
              description="Add the first expense or scan a physical receipt with AI to split costs."
              actionLabel="Add Expense"
              onAction={() => navigate(`/groups/${id}/add-expense`)}
            />
          ) : (
            <Stack spacing={1.5}>
              {expenses.map((exp) => {
                const expAmount = Number(exp.amount || 0);
                const payerName = exp.payerName || members.find((m) => (m.userId || m.id) === exp.payerId)?.name || `User #${exp.payerId}`;
                const category = exp.categoryName || "General";
                return (
                  <Paper
                    key={exp.id}
                    elevation={0}
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      border: "1px solid",
                      borderColor: "divider",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      transition: "all 0.15s ease",
                      "&:hover": { borderColor: "primary.main", bgcolor: "slate.50" },
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", gap: 2, minWidth: 0, flexGrow: 1, mr: 2 }}>
                      <Box
                        sx={{
                          width: 44,
                          height: 44,
                          flexShrink: 0,
                          borderRadius: 2,
                          bgcolor: "emerald.50",
                          color: "emerald.600",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                        }}
                      >
                        <ReceiptIcon fontSize="small" />
                      </Box>
                      <Box sx={{ minWidth: 0 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600, wordBreak: "break-word" }}>
                          {exp.description || exp.note || `Expense #${exp.id}`}
                        </Typography>
                        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.25, flexWrap: "wrap" }}>
                          <Chip
                            size="small"
                            label={category}
                            icon={<CategoryIcon sx={{ fontSize: 13 }} />}
                            sx={{ height: 20, fontSize: "0.7rem", bgcolor: "slate.100", flexShrink: 0 }}
                          />
                          <Typography variant="caption" sx={{ color: "text.secondary", whiteSpace: "nowrap" }}>
                            Paid by <strong>{payerName}</strong> • {exp.splitType || "EQUAL"} split
                          </Typography>
                        </Box>
                      </Box>
                    </Box>

                    <Box sx={{ textAlign: "right", flexShrink: 0, ml: "auto" }}>
                      <Typography variant="h6" sx={{ fontWeight: 700 }}>
                        {formatINR(expAmount)}
                      </Typography>
                      <Typography variant="caption" sx={{ color: "text.secondary", whiteSpace: "nowrap" }}>
                        {exp.createdAt ? new Date(exp.createdAt).toLocaleDateString() : ""}
                      </Typography>
                    </Box>
                  </Paper>
                );
              })}
            </Stack>
          )}
        </Box>
      )}

      {/* Tab 1: Balances */}
      {tab === 1 && (
        <Box>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              Group Net Balances
            </Typography>
            <Button
              variant="outlined"
              size="small"
              startIcon={<WalletIcon />}
              onClick={() => {
                setFromUserId("");
                setToUserId("");
                setSettleAmount("");
                setOpenSettle(true);
              }}
            >
              Record Settlement
            </Button>
          </Box>

          <Grid container spacing={2} sx={{ width: "100%" }}>
            {balances.map((b) => {
              const net = Number(b.netBalance || b.balance || 0);
              const name = b.name || b.userName || `User #${b.userId}`;
              const isCurrentUser = b.userId === user?.id || b.email === user?.email;

              return (
                <Grid size={{ xs: 12, sm: 6, md: 4 }} key={b.userId || name}>
                  <Card sx={{ border: "1px solid", borderColor: isCurrentUser ? "primary.main" : "divider" }}>
                    <CardContent sx={{ p: 2.5 }}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1.5 }}>
                        <Avatar sx={{ width: 36, height: 36, bgcolor: "slate.200", color: "slate.800" }}>
                          {name.charAt(0).toUpperCase()}
                        </Avatar>
                        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, noWrap: true }}>
                            {name} {isCurrentUser && "(You)"}
                          </Typography>
                          <Typography variant="caption" sx={{ color: "text.secondary", noWrap: true }}>
                            {b.email || `Member ID: ${b.userId}`}
                          </Typography>
                        </Box>
                      </Box>

                      <Divider sx={{ my: 1.5 }} />

                      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <Typography variant="caption" sx={{ color: "text.secondary" }}>
                          Status
                        </Typography>
                        <BalanceIndicator amount={net} />
                      </Box>

                      {net < 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Button
                            fullWidth
                            size="small"
                            variant="outlined"
                            color="warning"
                            onClick={() => openQuickSettle(b.userId, null, Math.abs(net))}
                          >
                            Record Settle Up (₹{Math.abs(net).toFixed(2)})
                          </Button>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </Box>
      )}

      {/* Tab 2: Members */}
      {tab === 2 && (
        <Box>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              Group Members ({members.length})
            </Typography>
            <Button
              variant="contained"
              size="small"
              startIcon={<PersonAddIcon />}
              onClick={() => setOpenAddMember(true)}
            >
              Add Member
            </Button>
          </Box>

          <Grid container spacing={2} sx={{ width: "100%" }}>
            {members.map((m) => {
              const displayName = m.name || m.userName || m.user?.name || `User #${m.id || m.userId}`;
              const email = m.email || m.user?.email || "";
              const isOwner = group.ownerId && (group.ownerId === m.id || group.ownerId === m.userId);

              return (
                <Grid size={{ xs: 12, sm: 6, md: 4 }} key={m.id || m.userId || email}>
                  <Card sx={{ border: "1px solid", borderColor: "divider" }}>
                    <CardContent sx={{ p: 2 }}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                        <Avatar sx={{ bgcolor: "primary.50", color: "primary.main", fontWeight: 600 }}>
                          {displayName.charAt(0).toUpperCase()}
                        </Avatar>
                        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, noWrap: true }}>
                            {displayName}
                          </Typography>
                          <Typography variant="caption" sx={{ color: "text.secondary", noWrap: true }}>
                            {email}
                          </Typography>
                        </Box>
                        {isOwner && (
                          <Chip size="small" label="Admin" color="primary" variant="outlined" sx={{ height: 22, fontSize: "0.68rem" }} />
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </Box>
      )}

      {/* Add Member Dialog */}
      <Dialog open={openAddMember} onClose={() => setOpenAddMember(false)} maxWidth="xs" fullWidth>
        <form onSubmit={handleAddMember}>
          <DialogTitle sx={{ fontWeight: 700 }}>Add Member to Group</DialogTitle>
          <DialogContent>
            {memberError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {memberError}
              </Alert>
            )}
            <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>
              Enter the registered email of the person you want to invite.
            </Typography>
            <TextField
              autoFocus
              fullWidth
              label="User Email"
              placeholder="friend@example.com"
              type="email"
              value={memberEmail}
              onChange={(e) => setMemberEmail(e.target.value)}
              required
              margin="dense"
            />
          </DialogContent>
          <DialogActions sx={{ p: 2.5, pt: 0 }}>
            <Button onClick={() => setOpenAddMember(false)} color="inherit" disabled={addingMember}>
              Cancel
            </Button>
            <Button type="submit" variant="contained" disabled={addingMember || !memberEmail.trim()}>
              {addingMember ? <CircularProgress size={20} /> : "Add Member"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Record Settlement Dialog */}
      <Dialog open={openSettle} onClose={() => setOpenSettle(false)} maxWidth="xs" fullWidth>
        <form onSubmit={handleRecordSettlement}>
          <DialogTitle sx={{ fontWeight: 700 }}>Record Settlement</DialogTitle>
          <DialogContent>
            {settleError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {settleError}
              </Alert>
            )}
            <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>
              Record a direct payment made between two members to balance debts.
            </Typography>

            <Stack spacing={2} sx={{ mt: 1 }}>
              <TextField
                select
                fullWidth
                label="Payer (Who paid / Settler)"
                value={fromUserId}
                onChange={(e) => setFromUserId(e.target.value)}
                required
              >
                {members.map((m) => {
                  const mId = m.userId || m.id;
                  const mName = m.name || m.userName || m.email || `User #${mId}`;
                  return (
                    <MenuItem key={mId} value={String(mId)}>
                      {mName}
                    </MenuItem>
                  );
                })}
              </TextField>

              <TextField
                select
                fullWidth
                label="Recipient (Who received)"
                value={toUserId}
                onChange={(e) => setToUserId(e.target.value)}
                required
              >
                {members.map((m) => {
                  const mId = m.userId || m.id;
                  const mName = m.name || m.userName || m.email || `User #${mId}`;
                  return (
                    <MenuItem key={mId} value={String(mId)}>
                      {mName}
                    </MenuItem>
                  );
                })}
              </TextField>

              <TextField
                fullWidth
                label="Amount (₹)"
                placeholder="0.00"
                type="number"
                inputProps={{ step: "0.01", min: "0.01" }}
                value={settleAmount}
                onChange={(e) => setSettleAmount(e.target.value)}
                required
              />
            </Stack>
          </DialogContent>
          <DialogActions sx={{ p: 2.5, pt: 0 }}>
            <Button onClick={() => setOpenSettle(false)} color="inherit" disabled={settling}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={settling || !fromUserId || !toUserId || fromUserId === toUserId || !settleAmount || Number(settleAmount) <= 0}
            >
              {settling ? <CircularProgress size={20} /> : "Record Settlement"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}
