import React, { useEffect, useState, useContext } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  MenuItem,
  CircularProgress,
  Alert,
  Checkbox,
  Grid,
  Tabs,
  Tab,
  Stack,
  Breadcrumbs,
  Link as MuiLink,
  Divider,
  InputAdornment,
  Chip,
  Paper,
} from "@mui/material";
import {
  ArrowBack as ArrowBackIcon,
  AutoAwesome as AutoAwesomeIcon,
  ReceiptLong as ReceiptIcon,
  Check as CheckIcon,
  HelpOutline as HelpOutlineIcon,
  CameraAlt as CameraAltIcon,
} from "@mui/icons-material";
import api from "../api/axios";
import { AuthContext } from "../context/AuthContext";
import PageHeader from "../components/PageHeader";
import { formatINR } from "../utils/formatters";

export default function AddExpense() {
  const { id: groupId } = useParams();
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [members, setMembers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [error, setError] = useState(null);

  // Form Fields
  const [note, setNote] = useState("");
  const [amount, setAmount] = useState("");
  const [payerId, setPayerId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [splitType, setSplitType] = useState("EQUAL"); // EQUAL, PERCENT, CUSTOM

  // Participants State: { [userId]: { checked: boolean, percent: string, amount: string } }
  const [participantsState, setParticipantsState] = useState({});

  // AI Natural Language Split State
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiInterpreting, setAiInterpreting] = useState(false);
  const [aiResult, setAiResult] = useState(null);
  const [aiError, setAiError] = useState("");

  useEffect(() => {
    loadInitialData();
  }, [groupId]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [groupRes, catRes] = await Promise.all([
        api.get(`/groups/${groupId}`),
        api.get("/categories").catch(() => ({ data: [] })),
      ]);

      const fetchedMembers = (groupRes.data?.members || []).map((m) => ({
        id: m.userId || m.id,
        name: m.name || m.userName || m.fullName || m.email,
        email: m.email || "",
      }));

      setMembers(fetchedMembers);
      setCategories(catRes.data || []);

      const initParts = {};
      fetchedMembers.forEach((m) => {
        initParts[String(m.id)] = { checked: true, percent: "", amount: "" };
      });
      setParticipantsState(initParts);

      // Default payer to logged in user if part of group, else first member
      const myMember = fetchedMembers.find((m) => m.id === user?.id || m.email === user?.email);
      if (myMember) {
        setPayerId(String(myMember.id));
      } else if (fetchedMembers.length > 0) {
        setPayerId(String(fetchedMembers[0].id));
      }
    } catch (err) {
      console.error("Failed to load initial data:", err);
      setError("Failed to load group details or categories.");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleChecked = (uid) => {
    setParticipantsState((prev) => ({
      ...prev,
      [uid]: {
        ...(prev[uid] || { percent: "", amount: "" }),
        checked: !(prev[uid]?.checked ?? false),
      },
    }));
  };

  const handleSetPercent = (uid, val) => {
    setParticipantsState((prev) => ({
      ...prev,
      [uid]: { ...(prev[uid] || {}), percent: val },
    }));
  };

  const handleSetAmount = (uid, val) => {
    setParticipantsState((prev) => ({
      ...prev,
      [uid]: { ...(prev[uid] || {}), amount: val },
    }));
  };

  // Interpret natural language with Ollama
  const handleInterpretAi = async () => {
    if (!aiPrompt.trim()) return;
    try {
      setAiInterpreting(true);
      setAiError("");
      setAiResult(null);

      const payload = {
        instruction: aiPrompt.trim(),
        totalAmount: amount ? Number(amount) : undefined,
        payerId: payerId ? Number(payerId) : undefined,
      };

      const res = await api.post(`/groups/${groupId}/ai/interpret-split`, payload);
      const data = res.data;
      setAiResult(data);

      // Auto-apply fields if present
      if (data.description) setNote(String(data.description));
      if (data.totalAmount) setAmount(String(data.totalAmount));
      if (data.payerId) setPayerId(String(data.payerId));

      // Apply participant allocations
      const pAllocs = data.participantAllocations || data.shares;
      if (pAllocs && Array.isArray(pAllocs) && pAllocs.length > 0) {
        setParticipantsState((prev) => {
          const updated = { ...prev };
          // Uncheck all first
          Object.keys(updated).forEach((k) => {
            updated[k] = { ...updated[k], checked: false, percent: "", amount: "" };
          });

          pAllocs.forEach((s) => {
            const uidStr = String(s.userId || s.id);
            if (updated[uidStr]) {
              const hasPercent = s.percent !== undefined && s.percent !== null && Number(s.percent) > 0;
              const hasAmount = s.shareAmount !== undefined && s.shareAmount !== null && Number(s.shareAmount) > 0;
              const isIncluded = hasPercent || hasAmount;
              updated[uidStr] = {
                checked: isIncluded,
                percent: (s.percent !== undefined && s.percent !== null) ? String(s.percent) : "",
                amount: (s.shareAmount !== undefined && s.shareAmount !== null) ? String(s.shareAmount) : "",
              };
            }
          });
          return updated;
        });

        // Set split type
        if (data.splitType) {
          setSplitType(data.splitType);
        } else if (pAllocs.some((s) => s.percent !== undefined && Number(s.percent) > 0)) {
          setSplitType("PERCENT");
        } else if (pAllocs.some((s) => s.shareAmount !== undefined && Number(s.shareAmount) > 0)) {
          setSplitType("CUSTOM");
        } else {
          setSplitType("EQUAL");
        }
      }
    } catch (err) {
      console.error("AI interpretation error:", err);
      setAiError(err?.response?.data?.message || "AI was unable to interpret prompt. Try rephrasing.");
    } finally {
      setAiInterpreting(false);
    }
  };

  // Form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const numAmount = Number(amount);
    if (!note.trim()) {
      setError("Please enter a description for the expense.");
      return;
    }
    if (!amount || isNaN(numAmount) || numAmount <= 0) {
      setError("Please enter a valid amount greater than 0.");
      return;
    }
    if (!payerId) {
      setError("Please select who paid for this expense.");
      return;
    }

    const checkedParticipants = Object.entries(participantsState)
      .filter(([, v]) => v.checked)
      .map(([uid, v]) => ({
        userId: Number(uid),
        percent: v.percent,
        amount: v.amount,
      }));

    if (checkedParticipants.length === 0) {
      setError("Select at least one participant to split with.");
      return;
    }

    if (splitType === "PERCENT") {
      const sumPercent = checkedParticipants.reduce((acc, p) => acc + (Number(p.percent) || 0), 0);
      if (Math.abs(sumPercent - 100) > 0.05) {
        setError(`Percentages must sum to 100%. Currently sums to ${sumPercent.toFixed(2)}%.`);
        return;
      }
    } else if (splitType === "CUSTOM") {
      const sumAmt = checkedParticipants.reduce((acc, p) => acc + (Number(p.amount) || 0), 0);
      if (Math.abs(sumAmt - numAmount) > 0.05) {
        setError(`Individual shares must sum to total ₹${numAmount.toFixed(2)}. Currently sums to ₹${sumAmt.toFixed(2)}.`);
        return;
      }
    }

    const shares = checkedParticipants.map((p) => {
      const s = { userId: p.userId };
      if (splitType === "PERCENT") s.percent = Number(p.percent || 0);
      if (splitType === "CUSTOM") s.amount = Number(p.amount || 0);
      return s;
    });

    const payload = {
      amount: numAmount,
      payerId: Number(payerId),
      splitType,
      currency: "INR",
      note: note.trim(),
      categoryId: categoryId ? Number(categoryId) : undefined,
      shares: shares.length > 0 ? shares : undefined,
    };

    try {
      setSubmitting(true);
      await api.post(`/groups/${groupId}/expenses`, payload);
      navigate(`/groups/${groupId}`);
    } catch (err) {
      console.error("Failed to create expense:", err);
      setError(err?.response?.data?.message || err?.response?.data || "Failed to create expense.");
    } finally {
      setSubmitting(false);
    }
  };

  const checkedCount = Object.values(participantsState).filter((v) => v.checked).length;
  const equalSharePerPerson =
    checkedCount > 0 && amount && Number(amount) > 0
      ? (Number(amount) / checkedCount).toFixed(2)
      : "0.00";

  return (
    <Box sx={{ maxWidth: 840, mx: "auto" }}>
      {/* Breadcrumbs */}
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
        <Typography color="text.primary">Add Expense</Typography>
      </Breadcrumbs>

      <PageHeader
        title="Add an Expense"
        subtitle="Record a bill, dinner, or travel expense with equal, custom, or AI-powered natural language splitting."
        action={
          <Button
            variant="outlined"
            startIcon={<CameraAltIcon />}
            onClick={() => navigate(`/receipt-scanner?groupId=${groupId}`)}
          >
            Scan Physical Receipt
          </Button>
        }
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* AI Natural Language Section */}
      <Card
        sx={{
          mb: 3,
          background: "linear-gradient(135deg, rgba(99, 102, 241, 0.04) 0%, rgba(16, 185, 129, 0.04) 100%)",
          border: "1px solid",
          borderColor: "primary.200",
        }}
      >
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
            <AutoAwesomeIcon sx={{ color: "primary.main", fontSize: 20 }} />
            <Typography variant="subtitle1" sx={{ fontWeight: 700, color: "primary.900" }}>
              Split with AI Natural Language (Ollama Local)
            </Typography>
            <Chip size="small" label="Local LLM" color="primary" sx={{ height: 20, fontSize: "0.7rem", ml: "auto" }} />
          </Box>
          <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>
            Describe who paid and how the expense should be allocated in everyday English.
          </Typography>

          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} alignItems="flex-start">
            <TextField
              fullWidth
              size="small"
              multiline
              rows={2}
              placeholder='e.g., "Dinner was ₹1500. Alice paid. Bob had 2 extra beers so add ₹400 to his share and split the rest with Charlie."'
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              disabled={aiInterpreting}
            />
            <Button
              variant="contained"
              sx={{ whiteSpace: "nowrap", px: 3, height: { sm: 56 } }}
              startIcon={aiInterpreting ? <CircularProgress size={16} color="inherit" /> : <AutoAwesomeIcon />}
              onClick={handleInterpretAi}
              disabled={aiInterpreting || !aiPrompt.trim()}
            >
              {aiInterpreting ? "Thinking..." : "Interpret & Fill"}
            </Button>
          </Stack>

          {aiError && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              {aiError}
            </Alert>
          )}

          {aiResult && aiResult.clarificationRequired ? (
            <Alert severity="warning" sx={{ mt: 2 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                {aiResult.clarificationQuestion || "Clarification Required"}
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                {aiResult.explanation}
              </Typography>
            </Alert>
          ) : aiResult ? (
            <Paper elevation={0} sx={{ mt: 2, p: 2, bgcolor: "background.paper", border: "1px solid", borderColor: "divider", borderRadius: 2 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <CheckIcon sx={{ color: "success.main", fontSize: 18 }} />
                <Typography variant="body2" sx={{ fontWeight: 600, color: "success.dark" }}>
                  AI parsed your expense successfully! Form filled below.
                </Typography>
                <Chip
                  size="small"
                  label={`Confidence: ${((aiResult.confidence || 1) * 100).toFixed(0)}%`}
                  variant="outlined"
                  sx={{ ml: "auto", fontSize: "0.7rem", height: 20 }}
                />
              </Box>
              <Typography variant="caption" sx={{ color: "text.secondary" }}>
                <strong>Explanation:</strong> {aiResult.explanation}
              </Typography>
            </Paper>
          ) : null}
        </CardContent>
      </Card>

      {/* Main Expense Form */}
      <Card>
        <CardContent sx={{ p: 4 }}>
          {loading ? (
            <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <form onSubmit={handleSubmit}>
              <Stack spacing={3}>
                <Grid container spacing={2} sx={{ width: "100%" }}>
                  <Grid size={{ xs: 12, sm: 8 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Description
                    </Typography>
                    <TextField
                      fullWidth
                      placeholder="e.g. Grocery run, Dinner at Toit, Uber ride"
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      required
                    />
                  </Grid>

                  <Grid size={{ xs: 12, sm: 4 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Amount (₹)
                    </Typography>
                    <TextField
                      fullWidth
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
                  </Grid>

                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Paid By
                    </Typography>
                    <TextField
                      select
                      fullWidth
                      value={payerId}
                      onChange={(e) => setPayerId(e.target.value)}
                      required
                    >
                      {members.map((m) => (
                        <MenuItem key={m.id} value={String(m.id)}>
                          {m.name} {m.id === user?.id && "(You)"}
                        </MenuItem>
                      ))}
                    </TextField>
                  </Grid>

                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                      Category
                    </Typography>
                    <TextField
                      select
                      fullWidth
                      value={categoryId}
                      onChange={(e) => setCategoryId(e.target.value)}
                    >
                      <MenuItem value="">Auto-Detect / General</MenuItem>
                      {categories.map((c) => (
                        <MenuItem key={c.id} value={String(c.id)}>
                          {c.name}
                        </MenuItem>
                      ))}
                    </TextField>
                  </Grid>
                </Grid>

                <Divider sx={{ my: 1 }} />

                {/* Split Mode Selector */}
                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
                    Split Method
                  </Typography>
                  <Tabs
                    value={splitType}
                    onChange={(e, val) => setSplitType(val)}
                    sx={{
                      bgcolor: "slate.100",
                      borderRadius: 2,
                      p: 0.5,
                      minHeight: 40,
                      "& .MuiTabs-indicator": { display: "none" },
                    }}
                  >
                    <Tab
                      value="EQUAL"
                      label="Split Equally"
                      sx={{
                        borderRadius: 1.5,
                        minHeight: 36,
                        py: 0.5,
                        textTransform: "none",
                        fontWeight: 600,
                        "&.Mui-selected": { bgcolor: "background.paper", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" },
                      }}
                    />
                    <Tab
                      value="PERCENT"
                      label="By Percentage (%)"
                      sx={{
                        borderRadius: 1.5,
                        minHeight: 36,
                        py: 0.5,
                        textTransform: "none",
                        fontWeight: 600,
                        "&.Mui-selected": { bgcolor: "background.paper", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" },
                      }}
                    />
                    <Tab
                      value="CUSTOM"
                      label="Exact Amounts (₹)"
                      sx={{
                        borderRadius: 1.5,
                        minHeight: 36,
                        py: 0.5,
                        textTransform: "none",
                        fontWeight: 600,
                        "&.Mui-selected": { bgcolor: "background.paper", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" },
                      }}
                    />
                  </Tabs>
                </Box>

                {/* Participants list */}
                <Box>
                  <Typography variant="caption" sx={{ color: "text.secondary", display: "block", mb: 1.5 }}>
                    {splitType === "EQUAL" && `Split equally among selected (${checkedCount} people: ₹${equalSharePerPerson} each)`}
                    {splitType === "PERCENT" && "Specify the percentage for each person (must total 100%)."}
                    {splitType === "CUSTOM" && `Specify exact amount per person (must total ₹${amount || "0.00"}).`}
                  </Typography>

                  <Stack spacing={1.5}>
                    {members.map((m) => {
                      const uid = String(m.id);
                      const pState = participantsState[uid] || { checked: false, percent: "", amount: "" };

                      return (
                        <Paper
                          key={m.id}
                          variant="outlined"
                          sx={{
                            p: 1.5,
                            borderRadius: 2,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            bgcolor: pState.checked ? "background.paper" : "slate.50",
                            opacity: pState.checked ? 1 : 0.6,
                          }}
                        >
                          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                            <Checkbox
                              checked={pState.checked}
                              onChange={() => handleToggleChecked(uid)}
                              color="primary"
                            />
                            <Box>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                {m.name} {m.id === user?.id && "(You)"}
                              </Typography>
                              <Typography variant="caption" sx={{ color: "text.secondary" }}>
                                {m.email}
                              </Typography>
                            </Box>
                          </Box>

                          {pState.checked && (
                            <Box sx={{ minWidth: 140, textAlign: "right" }}>
                              {splitType === "EQUAL" && (
                                <Typography variant="body2" sx={{ fontWeight: 600, color: "slate.700" }}>
                                  ₹{equalSharePerPerson}
                                </Typography>
                              )}
                              {splitType === "PERCENT" && (
                                <TextField
                                  size="small"
                                  type="number"
                                  placeholder="0"
                                  value={pState.percent}
                                  onChange={(e) => handleSetPercent(uid, e.target.value)}
                                  InputProps={{ endAdornment: <InputAdornment position="end">%</InputAdornment> }}
                                  sx={{ width: 110 }}
                                />
                              )}
                              {splitType === "CUSTOM" && (
                                <TextField
                                  size="small"
                                  type="number"
                                  placeholder="0.00"
                                  value={pState.amount}
                                  onChange={(e) => handleSetAmount(uid, e.target.value)}
                                  InputProps={{ startAdornment: <InputAdornment position="start">₹</InputAdornment> }}
                                  sx={{ width: 130 }}
                                />
                              )}
                            </Box>
                          )}
                        </Paper>
                      );
                    })}
                  </Stack>
                </Box>

                <Box sx={{ display: "flex", gap: 2, justifyContent: "flex-end", pt: 2 }}>
                  <Button variant="outlined" color="inherit" onClick={() => navigate(`/groups/${groupId}`)} disabled={submitting}>
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    disabled={submitting}
                    startIcon={submitting ? <CircularProgress size={18} color="inherit" /> : <ReceiptIcon />}
                    sx={{ px: 3 }}
                  >
                    {submitting ? "Saving..." : "Save Expense"}
                  </Button>
                </Box>
              </Stack>
            </form>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
