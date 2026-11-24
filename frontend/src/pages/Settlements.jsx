import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  TextField,
  MenuItem,
  Grid,
  Paper,
  Stack,
  Breadcrumbs,
  Link as MuiLink,
  Divider,
  InputAdornment,
} from "@mui/material";
import {
  ArrowBack as ArrowBackIcon,
  AccountBalanceWallet as WalletIcon,
  CheckCircle as CheckCircleIcon,
  History as HistoryIcon,
} from "@mui/icons-material";
import api from "../api/axios";
import PageHeader from "../components/PageHeader";
import EmptyState from "../components/EmptyState";
import { formatINR } from "../utils/formatters";

export default function Settlements() {
  const { id: groupId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [members, setMembers] = useState([]);
  const [settlements, setSettlements] = useState([]);
  const [error, setError] = useState(null);

  // Form
  const [fromUserId, setFromUserId] = useState("");
  const [toUserId, setToUserId] = useState("");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(null);
  const [submitError, setSubmitError] = useState(null);

  useEffect(() => {
    fetchAll();
  }, [groupId]);

  const fetchAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const [groupRes, settleRes] = await Promise.all([
        api.get(`/groups/${groupId}`),
        api.get(`/groups/${groupId}/settlements`).catch(() => ({ data: [] })),
      ]);

      const fetchedMembers = (groupRes.data?.members || []).map((m) => ({
        id: m.userId || m.id,
        name: m.name || m.userName || m.fullName || m.email,
        email: m.email || "",
      }));

      setMembers(fetchedMembers);
      setSettlements(Array.isArray(settleRes.data) ? settleRes.data : []);
    } catch (err) {
      console.error(err);
      setError("Failed to load settlements data.");
    } finally {
      setLoading(false);
    }
  };

  const handleRecord = async (e) => {
    e.preventDefault();
    setSubmitError(null);
    setSubmitSuccess(null);

    if (!fromUserId || !toUserId || !amount || Number(amount) <= 0) {
      setSubmitError("Please fill in valid payer, recipient, and amount.");
      return;
    }

    if (fromUserId === toUserId) {
      setSubmitError("Payer and recipient cannot be the same member.");
      return;
    }

    try {
      setSubmitting(true);
      await api.post(`/groups/${groupId}/settlements`, {
        fromUserId: Number(fromUserId),
        toUserId: Number(toUserId),
        amount: Number(amount),
        currency: "INR",
        note: note.trim() || undefined,
      });

      setSubmitSuccess("Settlement recorded successfully!");
      setAmount("");
      setNote("");
      fetchAll();
    } catch (err) {
      console.error("Settlement error:", err);
      setSubmitError(err?.response?.data?.message || "Failed to record settlement.");
    } finally {
      setSubmitting(false);
    }
  };

  const memberName = (id) => {
    const m = members.find((mem) => mem.id === id);
    return m ? m.name : `Member #${id}`;
  };

  return (
    <Box sx={{ maxWidth: 960, mx: "auto" }}>
      <Breadcrumbs sx={{ mb: 2 }}>
        <MuiLink
          component="button"
          underline="hover"
          color="inherit"
          onClick={() => navigate(`/groups/${groupId}`)}
          sx={{ display: "flex", alignItems: "center", gap: 0.5, cursor: "pointer" }}
        >
          <ArrowBackIcon fontSize="small" /> Back to Group
        </MuiLink>
        <Typography color="text.primary">Settlements</Typography>
      </Breadcrumbs>

      <PageHeader
        title="Group Settlements"
        subtitle="Record direct peer-to-peer payments to settle debts and review historical transfers."
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3} sx={{ width: "100%" }}>
        {/* Record Settlement Card */}
        <Grid size={{ xs: 12, md: 5 }}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                Record Direct Settlement
              </Typography>
              <Typography variant="body2" sx={{ color: "text.secondary", mb: 2.5 }}>
                Mark cash or UPI payments made outside the platform to adjust balances.
              </Typography>

              {submitError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {submitError}
                </Alert>
              )}
              {submitSuccess && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  {submitSuccess}
                </Alert>
              )}

              <form onSubmit={handleRecord}>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="caption" sx={{ fontWeight: 600, mb: 0.5, display: "block" }}>
                      Who Paid? (Debtor)
                    </Typography>
                    <TextField
                      select
                      fullWidth
                      size="small"
                      value={fromUserId}
                      onChange={(e) => setFromUserId(e.target.value)}
                      required
                    >
                      {members.map((m) => (
                        <MenuItem key={m.id} value={String(m.id)} disabled={String(m.id) === toUserId}>
                          {m.name} {String(m.id) === toUserId ? "(Selected Recipient)" : ""}
                        </MenuItem>
                      ))}
                    </TextField>
                  </Box>

                  <Box>
                    <Typography variant="caption" sx={{ fontWeight: 600, mb: 0.5, display: "block" }}>
                      Who Received? (Creditor)
                    </Typography>
                    <TextField
                      select
                      fullWidth
                      size="small"
                      value={toUserId}
                      onChange={(e) => setToUserId(e.target.value)}
                      required
                    >
                      {members.map((m) => (
                        <MenuItem key={m.id} value={String(m.id)} disabled={String(m.id) === fromUserId}>
                          {m.name} {String(m.id) === fromUserId ? "(Selected Payer)" : ""}
                        </MenuItem>
                      ))}
                    </TextField>
                  </Box>

                  <Box>
                    <Typography variant="caption" sx={{ fontWeight: 600, mb: 0.5, display: "block" }}>
                      Amount (₹)
                    </Typography>
                    <TextField
                      fullWidth
                      size="small"
                      type="number"
                      placeholder="0.00"
                      inputProps={{ step: "0.01", min: "0.01" }}
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      InputProps={{
                        startAdornment: <InputAdornment position="start">₹</InputAdornment>,
                      }}
                      required
                    />
                  </Box>

                  <Box>
                    <Typography variant="caption" sx={{ fontWeight: 600, mb: 0.5, display: "block" }}>
                      Note (Optional)
                    </Typography>
                    <TextField
                      fullWidth
                      size="small"
                      placeholder="e.g. Paid via Google Pay"
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                    />
                  </Box>

                  <Button
                    type="submit"
                    variant="contained"
                    disabled={submitting || !fromUserId || !toUserId || fromUserId === toUserId || !amount || Number(amount) <= 0}
                    startIcon={submitting ? <CircularProgress size={18} color="inherit" /> : <WalletIcon />}
                    sx={{ mt: 1, py: 1 }}
                  >
                    {submitting ? "Recording..." : "Record Payment"}
                  </Button>
                </Stack>
              </form>
            </CardContent>
          </Card>
        </Grid>

        {/* Settlement History */}
        <Grid size={{ xs: 12, md: 7 }}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 700, mb: 1 }}>
                Settlement History
              </Typography>
              <Typography variant="body2" sx={{ color: "text.secondary", mb: 2.5 }}>
                Chronological list of all settled balances in this group.
              </Typography>

              {loading ? (
                <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : settlements.length === 0 ? (
                <EmptyState
                  icon={HistoryIcon}
                  title="No settlements recorded yet"
                  description="When members pay each other back, records will appear here."
                />
              ) : (
                <Stack spacing={1.5}>
                  {settlements.map((s) => {
                    const payer = s.fromUserName || memberName(s.fromUserId);
                    const payee = s.toUserName || memberName(s.toUserId);
                    const amt = Number(s.amount || 0);

                    return (
                      <Paper
                        key={s.id}
                        variant="outlined"
                        sx={{
                          p: 2,
                          borderRadius: 2,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                        }}
                      >
                        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                          <Box
                            sx={{
                              width: 36,
                              height: 36,
                              borderRadius: 2,
                              bgcolor: "emerald.50",
                              color: "emerald.600",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                            }}
                          >
                            <CheckCircleIcon fontSize="small" />
                          </Box>
                          <Box>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              <strong>{payer}</strong> paid <strong>{payee}</strong>
                            </Typography>
                            <Typography variant="caption" sx={{ color: "text.secondary" }}>
                              {s.note ? `${s.note} • ` : ""}
                              {s.createdAt ? new Date(s.createdAt).toLocaleDateString() : ""}
                            </Typography>
                          </Box>
                        </Box>

                        <Typography variant="subtitle1" sx={{ fontWeight: 700, color: "emerald.700" }}>
                          {formatINR(amt)}
                        </Typography>
                      </Paper>
                    );
                  })}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
