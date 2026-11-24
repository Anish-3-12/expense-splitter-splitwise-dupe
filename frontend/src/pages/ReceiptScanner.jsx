import React, { useState, useEffect, useContext } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  TextField,
  MenuItem,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Stack,
  Breadcrumbs,
  Link as MuiLink,
  Divider,
  Collapse,
  Tooltip,
} from "@mui/material";
import {
  CloudUpload as CloudUploadIcon,
  AutoAwesome as AutoAwesomeIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  ArrowBack as ArrowBackIcon,
  ReceiptLong as ReceiptIcon,
  WarningAmber as WarningIcon,
  Subject as SubjectIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from "@mui/icons-material";
import api from "../api/axios";
import { AuthContext } from "../context/AuthContext";
import PageHeader from "../components/PageHeader";

export default function ReceiptScanner() {
  const [searchParams] = useSearchParams();
  const initialGroupId = searchParams.get("groupId") || "";
  const navigate = useNavigate();
  const { user } = useContext(AuthContext);

  const [groups, setGroups] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState(initialGroupId);
  const [groupMembers, setGroupMembers] = useState([]);
  const [categories, setCategories] = useState([]);

  // Upload & Extraction State
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [stage, setStage] = useState("IDLE"); // IDLE, UPLOADING, EXTRACTING, REVIEW, CONFIRMING, DONE
  const [error, setError] = useState(null);

  // Extracted Receipt Details
  const [receiptId, setReceiptId] = useState(null);
  const [merchant, setMerchant] = useState("");
  const [receiptDate, setReceiptDate] = useState("");
  const [totalAmount, setTotalAmount] = useState("");
  const [subtotal, setSubtotal] = useState("0");
  const [taxAmount, setTaxAmount] = useState("0");
  const [currency, setCurrency] = useState("USD");
  const [currencySymbol, setCurrencySymbol] = useState("$");
  const [validationStatus, setValidationStatus] = useState("RECONCILED");
  const [discrepancyAmount, setDiscrepancyAmount] = useState(0);
  const [warnings, setWarnings] = useState([]);
  const [rawOcrText, setRawOcrText] = useState("");
  const [showRawOcr, setShowRawOcr] = useState(false);
  const [showReceiptImage, setShowReceiptImage] = useState(false);
  const [items, setItems] = useState([]);

  // Confirmation Details
  const [payerId, setPayerId] = useState("");
  const [splitType, setSplitType] = useState("EQUAL");
  const [categoryId, setCategoryId] = useState("");

  useEffect(() => {
    loadGroupsAndCategories();
  }, []);

  useEffect(() => {
    if (selectedGroupId) {
      loadGroupMembers(selectedGroupId);
    }
  }, [selectedGroupId]);

  const loadGroupsAndCategories = async () => {
    try {
      const [gRes, cRes] = await Promise.all([
        api.get("/groups"),
        api.get("/categories").catch(() => ({ data: [] })),
      ]);
      setGroups(gRes.data || []);
      setCategories(cRes.data || []);

      if (!selectedGroupId && gRes.data?.length > 0) {
        setSelectedGroupId(String(gRes.data[0].id));
      }
    } catch (err) {
      console.error("Failed to load initial data:", err);
      setError("Failed to load your groups.");
    }
  };

  const loadGroupMembers = async (gid) => {
    try {
      const res = await api.get(`/groups/${gid}`);
      const members = (res.data?.members || []).map((m) => ({
        id: m.userId || m.id,
        name: m.name || m.userName || m.email,
      }));
      setGroupMembers(members);
      if (members.length > 0) {
        const me = members.find((m) => m.id === user?.id);
        setPayerId(String(me ? me.id : members[0].id));
      }
    } catch (err) {
      console.error("Failed to load members:", err);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
    }
  };

  const handleScanReceipt = async () => {
    if (!selectedFile) {
      setError("Please select a receipt image file to scan.");
      return;
    }
    if (!selectedGroupId) {
      setError("Please select an expense group.");
      return;
    }

    try {
      setError(null);
      setStage("UPLOADING");

      // 1. Upload receipt
      const formData = new FormData();
      formData.append("file", selectedFile);

      const uploadRes = await api.post(`/groups/${selectedGroupId}/receipts`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const uploadedReceipt = uploadRes.data;
      setReceiptId(uploadedReceipt.id);

      // 2. Extract with AI OCR
      setStage("EXTRACTING");
      const extractRes = await api.post(
        `/groups/${selectedGroupId}/receipts/${uploadedReceipt.id}/extract`
      );

      const data = extractRes.data;
      setMerchant(data.merchantName || "Receipt Expense");
      setReceiptDate(data.receiptDate || new Date().toISOString().split("T")[0]);
      setTotalAmount(String(data.totalAmount || "0.00"));
      setSubtotal(data.subtotal != null ? String(data.subtotal) : "");
      setTaxAmount(data.tax != null ? String(data.tax) : "0.00");

      const detectedCurr = data.currency || "USD";
      setCurrency(detectedCurr);
      const symbolMap = { USD: "$", INR: "₹", EUR: "€", GBP: "£" };
      setCurrencySymbol(data.currencySymbol || symbolMap[detectedCurr] || "$");

      setValidationStatus(data.validationStatus || "RECONCILED");
      setDiscrepancyAmount(Number(data.discrepancyAmount) || 0);
      setWarnings(data.warnings || []);
      setRawOcrText(data.rawOcrText || "");

      if (data.items && Array.isArray(data.items)) {
        setItems(
          data.items.map((it, idx) => ({
            id: it.id || idx + 1,
            description: it.description || "Item",
            quantity: Number(it.quantity) || 1,
            unitPrice: Number(it.unitPrice) || 0,
            lineTotal: Number(it.lineTotal ?? it.totalPrice) || 0,
            isAmbiguous: Boolean(it.isAmbiguous),
            ambiguityReason: it.ambiguityReason || null,
          }))
        );
      } else {
        setItems([]);
      }

      setStage("REVIEW");
    } catch (err) {
      console.error("Receipt scan failed:", err);
      setError(
        err?.response?.data?.message ||
          "Receipt processing failed. Make sure AI service and Ollama are reachable."
      );
      setStage("IDLE");
    }
  };

  const handleItemChange = (index, field, value) => {
    setItems((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: value };
      if (field === "quantity" || field === "unitPrice") {
        const qty = Number(field === "quantity" ? value : copy[index].quantity) || 1;
        const up = Number(field === "unitPrice" ? value : copy[index].unitPrice) || 0;
        copy[index].lineTotal = Number((qty * up).toFixed(2));
      } else if (field === "lineTotal") {
        const lt = Number(value) || 0;
        const qty = Number(copy[index].quantity) || 1;
        if (qty > 0) {
          copy[index].unitPrice = Number((lt / qty).toFixed(2));
        }
      }
      return copy;
    });
  };

  const handleAddItem = () => {
    setItems((prev) => [
      ...prev,
      { id: Date.now(), description: "New Item", quantity: 1, unitPrice: 0, lineTotal: 0, isAmbiguous: false },
    ]);
  };

  const handleDeleteItem = (index) => {
    setItems((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleConfirmAndPost = async () => {
    if (!receiptId) return;
    if (!payerId) {
      setError("Please select who paid for the receipt.");
      return;
    }
    const numTotal = Number(totalAmount);
    if (!numTotal || numTotal <= 0) {
      setError("Total amount must be greater than 0.");
      return;
    }

    try {
      setStage("CONFIRMING");
      setError(null);

      // Save reviewed items first
      await api.put(`/groups/${selectedGroupId}/receipts/${receiptId}/review`, {
        merchantName: merchant.trim(),
        receiptDate: receiptDate,
        totalAmount: numTotal,
        subtotal: subtotal !== "" ? Number(subtotal) : null,
        tax: Number(taxAmount) || 0,
        currency: currency,
        items: items.map((it) => ({
          description: it.description,
          quantity: Number(it.quantity) || 1,
          unitPrice: Number(it.unitPrice) || 0,
          lineTotal: Number(it.lineTotal) || 0,
        })),
      });

      // Confirm into expense
      await api.post(`/groups/${selectedGroupId}/receipts/${receiptId}/confirm`, {
        payerId: Number(payerId),
        splitType: splitType,
        categoryId: categoryId ? Number(categoryId) : undefined,
        note: `${merchant || "Receipt"} (${items.length} items)`,
      });

      setStage("DONE");
      setTimeout(() => {
        navigate(`/groups/${selectedGroupId}`);
      }, 1200);
    } catch (err) {
      console.error("Confirmation error:", err);
      if (err?.response?.status === 409) {
        setError("Conflict (HTTP 409): This receipt has already been confirmed into an expense. Repeated confirmation is rejected.");
      } else {
        setError(err?.response?.data?.message || "Failed to confirm receipt expense.");
      }
      setStage("REVIEW");
    }
  };

  return (
    <Box sx={{ maxWidth: 960, mx: "auto" }}>
      <Breadcrumbs sx={{ mb: 2 }}>
        <MuiLink
          component="button"
          underline="hover"
          color="inherit"
          onClick={() => navigate(selectedGroupId ? `/groups/${selectedGroupId}` : "/groups")}
          sx={{ display: "flex", alignItems: "center", gap: 0.5, cursor: "pointer" }}
        >
          <ArrowBackIcon fontSize="small" /> Back to Group
        </MuiLink>
        <Typography color="text.primary">AI Receipt Scanner</Typography>
      </Breadcrumbs>

      <PageHeader
        title="AI Receipt Intelligence"
        subtitle="Upload a grocery, dinner, or shopping receipt. OpenCV & Ollama extract merchant, line items, and totals automatically."
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Target Group Selector */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ p: 2.5 }}>
          <Grid container spacing={2} alignItems="center" sx={{ width: "100%" }}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                Select Group to Bill
              </Typography>
              <TextField
                select
                fullWidth
                size="small"
                value={selectedGroupId}
                onChange={(e) => setSelectedGroupId(e.target.value)}
                disabled={stage !== "IDLE" && stage !== "REVIEW"}
              >
                {groups.map((g) => (
                  <MenuItem key={g.id} value={String(g.id)}>
                    {g.name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                Target group has <strong>{groupMembers.length} members</strong> eligible for equal or custom splitting.
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Upload Zone / Extraction Progress */}
      {stage === "IDLE" || stage === "UPLOADING" || stage === "EXTRACTING" ? (
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: 4, textAlign: "center" }}>
            {stage === "IDLE" && (
              <Box>
                <input
                  accept="image/jpeg,image/png,image/webp,image/jpg"
                  style={{ display: "none" }}
                  id="receipt-file-input"
                  type="file"
                  onChange={handleFileChange}
                />
                <label htmlFor="receipt-file-input">
                  <Box
                    sx={{
                      p: 5,
                      border: "2px dashed",
                      borderColor: previewUrl ? "primary.main" : "slate.300",
                      borderRadius: 3,
                      bgcolor: "slate.50",
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                      "&:hover": { borderColor: "primary.main", bgcolor: "primary.50" },
                    }}
                  >
                    <CloudUploadIcon sx={{ fontSize: 48, color: "primary.main", mb: 1 }} />
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                      {selectedFile ? selectedFile.name : "Click to select or drag receipt image"}
                    </Typography>
                    <Typography variant="caption" sx={{ color: "text.secondary", display: "block" }}>
                      Supports JPG, PNG, WEBP receipts up to 10MB
                    </Typography>

                    {previewUrl && (
                      <Box sx={{ mt: 3, maxHeight: 200, overflow: "hidden", display: "inline-block" }}>
                        <img
                          src={previewUrl}
                          alt="Receipt Preview"
                          style={{ maxHeight: 200, borderRadius: 8, boxShadow: "0 4px 12px rgba(0,0,0,0.1)" }}
                        />
                      </Box>
                    )}
                  </Box>
                </label>

                <Box sx={{ mt: 3, display: "flex", justifyContent: "center" }}>
                  <Button
                    variant="contained"
                    size="large"
                    startIcon={<AutoAwesomeIcon />}
                    onClick={handleScanReceipt}
                    disabled={!selectedFile || !selectedGroupId}
                    sx={{ px: 4, py: 1.2 }}
                  >
                    Start AI Extraction
                  </Button>
                </Box>
              </Box>
            )}

            {(stage === "UPLOADING" || stage === "EXTRACTING") && (
              <Box sx={{ py: 6 }}>
                <CircularProgress size={48} sx={{ mb: 2 }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  {stage === "UPLOADING"
                    ? "Uploading receipt image..."
                    : "Analyzing receipt with OpenCV & Ollama OCR..."}
                </Typography>
                <Typography variant="body2" sx={{ color: "text.secondary", mt: 1, maxWidth: 500, mx: "auto" }}>
                  We are segmenting image regions, performing local optical character recognition, and parsing line items using your locally loaded Qwen model.
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      ) : null}

      {/* Review & Edit Extracted Line Items */}
      {(stage === "REVIEW" || stage === "CONFIRMING" || stage === "DONE") && (
        <Stack spacing={3}>
          {stage === "DONE" && (
            <Alert icon={<CheckCircleIcon fontSize="inherit" />} severity="success">
              Receipt verified and converted into group expense! Redirecting to group...
            </Alert>
          )}

          <Card>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  Extracted Receipt Details
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Chip
                    icon={<AutoAwesomeIcon sx={{ fontSize: 14 }} />}
                    label="AI Extracted"
                    color="primary"
                    variant="outlined"
                    size="small"
                  />
                  <Chip
                    label={`Currency: ${currency} (${currencySymbol})`}
                    variant="filled"
                    color="default"
                    size="small"
                  />
                  {previewUrl && (
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => setShowReceiptImage(!showReceiptImage)}
                      sx={{ textTransform: "none", fontSize: "0.75rem", height: 24, px: 1 }}
                    >
                      {showReceiptImage ? "Hide Image" : "View Receipt"}
                    </Button>
                  )}
                </Stack>
              </Box>

              {previewUrl && showReceiptImage && (
                <Box sx={{ mb: 2.5, textAlign: "center", bgcolor: "slate.50", p: 1.5, borderRadius: 2, border: "1px solid", borderColor: "divider" }}>
                  <img
                    src={previewUrl}
                    alt="Receipt Image"
                    style={{ maxHeight: 320, maxWidth: "100%", borderRadius: 6, objectFit: "contain" }}
                  />
                </Box>
              )}

              {/* Financial Invariant Validations */}
              {(() => {
                const sumItemsMinor = Math.round(items.reduce((acc, it) => acc + (Number(it.lineTotal) || 0), 0) * 100);
                const subtotalMinor = subtotal !== "" ? Math.round(Number(subtotal) * 100) : null;
                const taxMinor = Math.round((Number(taxAmount) || 0) * 100);
                const totalMinor = totalAmount !== "" ? Math.round(Number(totalAmount) * 100) : null;

                const inv1Passed = subtotalMinor !== null && sumItemsMinor === subtotalMinor;
                const inv2Passed = subtotalMinor !== null && totalMinor !== null && (subtotalMinor + taxMinor === totalMinor);
                const isReconciled = inv1Passed && inv2Passed;

                if (!isReconciled || validationStatus === "DISCREPANCY_DETECTED") {
                  return (
                    <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 2.5 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                        Financial Invariant Discrepancy Detected
                      </Typography>
                      {!inv1Passed && (
                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                          • <strong>Invariant 1 (Line Items vs Subtotal) Failed:</strong> Sum of item line totals ({currencySymbol}{(sumItemsMinor/100).toFixed(2)}) does not match receipt subtotal ({currencySymbol}{subtotalMinor !== null ? (subtotalMinor/100).toFixed(2) : "Missing"}).
                        </Typography>
                      )}
                      {!inv2Passed && (
                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                          • <strong>Invariant 2 (Subtotal + Tax vs Total) Failed:</strong> Subtotal ({currencySymbol}{subtotalMinor !== null ? (subtotalMinor/100).toFixed(2) : "Missing"}) + Tax ({currencySymbol}{(taxMinor/100).toFixed(2)}) = {currencySymbol}{subtotalMinor !== null ? ((subtotalMinor + taxMinor)/100).toFixed(2) : "Unknown"}, which does not match Final Total ({currencySymbol}{totalMinor !== null ? (totalMinor/100).toFixed(2) : "Missing"}).
                        </Typography>
                      )}
                      <Typography variant="caption" sx={{ display: "block", mt: 1, color: "text.secondary" }}>
                        Please correct the line item prices, subtotal, tax, or total above before confirming.
                      </Typography>
                    </Alert>
                  );
                } else {
                  return (
                    <Alert severity="success" icon={<CheckCircleIcon />} sx={{ mb: 2.5 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        Receipt Fully Reconciled: Sum of line items ({currencySymbol}{(sumItemsMinor/100).toFixed(2)}) equals Subtotal, and Subtotal + Tax ({currencySymbol}{(taxMinor/100).toFixed(2)}) equals Final Total ({currencySymbol}{(totalMinor/100).toFixed(2)}).
                      </Typography>
                    </Alert>
                  );
                }
              })()}

              {currency !== "INR" && (
                <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                    Foreign Currency Ledger Restriction ({currency})
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 0.5 }}>
                    The group expense ledger operates strictly in Indian Rupees (INR / ₹). To maintain mathematical integrity across shared balances and settlements, foreign currency receipts ({currency}) cannot be posted directly into the ledger. Original OCR items, quantities, and monetary totals remain fully preserved for your records.
                  </Typography>
                </Alert>
              )}

              <Grid container spacing={2} sx={{ mb: 3, width: "100%" }}>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <Typography variant="caption" sx={{ fontWeight: 600 }}>
                    Merchant Name
                  </Typography>
                  <TextField
                    fullWidth
                    size="small"
                    value={merchant}
                    onChange={(e) => setMerchant(e.target.value)}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <Typography variant="caption" sx={{ fontWeight: 600 }}>
                    Receipt Date
                  </Typography>
                  <TextField
                    fullWidth
                    size="small"
                    type="date"
                    value={receiptDate}
                    onChange={(e) => setReceiptDate(e.target.value)}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <Typography variant="caption" sx={{ fontWeight: 600 }}>
                    Currency
                  </Typography>
                  <TextField
                    select
                    fullWidth
                    size="small"
                    value={currency}
                    disabled
                    helperText="Document currency detected by OCR"
                  >
                    <MenuItem value="USD">USD ($)</MenuItem>
                    <MenuItem value="INR">INR (₹)</MenuItem>
                    <MenuItem value="EUR">EUR (€)</MenuItem>
                    <MenuItem value="GBP">GBP (£)</MenuItem>
                  </TextField>
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <Typography variant="caption" sx={{ fontWeight: 600 }}>
                    Subtotal ({currencySymbol})
                  </Typography>
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    placeholder="Pre-tax subtotal"
                    value={subtotal}
                    onChange={(e) => setSubtotal(e.target.value)}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <Typography variant="caption" sx={{ fontWeight: 600 }}>
                    Tax Amount ({currencySymbol})
                  </Typography>
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    value={taxAmount}
                    onChange={(e) => setTaxAmount(e.target.value)}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <Typography variant="caption" sx={{ fontWeight: 600 }}>
                    Total Amount ({currencySymbol})
                  </Typography>
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    value={totalAmount}
                    onChange={(e) => setTotalAmount(e.target.value)}
                  />
                </Grid>
              </Grid>

              {/* Raw OCR Text Collapsible Viewer */}
              {rawOcrText && (
                <Box sx={{ mb: 2 }}>
                  <Button
                    size="small"
                    variant="text"
                    startIcon={<SubjectIcon />}
                    endIcon={showRawOcr ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    onClick={() => setShowRawOcr(!showRawOcr)}
                    sx={{ textTransform: "none", color: "text.secondary", fontSize: "0.8rem" }}
                  >
                    {showRawOcr ? "Hide Raw OCR Text" : "View Raw OCR Text"}
                  </Button>
                  <Collapse in={showRawOcr}>
                    <Paper variant="outlined" sx={{ p: 2, mt: 1, bgcolor: "grey.50", maxHeight: 200, overflow: "auto" }}>
                      <Typography variant="caption" component="pre" sx={{ fontFamily: "monospace", whiteSpace: "pre-wrap", m: 0 }}>
                        {rawOcrText}
                      </Typography>
                    </Paper>
                  </Collapse>
                </Box>
              )}

              <Divider sx={{ my: 2 }} />

              {/* Line items table */}
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1.5 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>
                  Itemized Line Items ({items.length})
                </Typography>
                <Button size="small" startIcon={<AddIcon />} onClick={handleAddItem}>
                  Add Item
                </Button>
              </Box>

              <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
                <Table size="small">
                  <TableHead sx={{ bgcolor: "slate.50" }}>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Item Description</TableCell>
                      <TableCell sx={{ fontWeight: 600, width: 80 }}>Qty</TableCell>
                      <TableCell sx={{ fontWeight: 600, width: 130 }}>Unit Price ({currencySymbol})</TableCell>
                      <TableCell sx={{ fontWeight: 600, width: 130 }}>Line Total ({currencySymbol})</TableCell>
                      <TableCell sx={{ width: 50 }}></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {items.map((item, idx) => (
                      <TableRow key={item.id || idx}>
                        <TableCell>
                          <TextField
                            size="small"
                            fullWidth
                            variant="standard"
                            value={item.description}
                            onChange={(e) => handleItemChange(idx, "description", e.target.value)}
                          />
                          {item.isAmbiguous && (
                            <Tooltip title={item.ambiguityReason || "Ambiguous row price vs unit price interpretation"}>
                              <Chip
                                size="small"
                                color="warning"
                                variant="outlined"
                                label={item.ambiguityReason ? item.ambiguityReason.substring(0, 45) + "..." : "Ambiguous"}
                                sx={{ height: 20, fontSize: "0.68rem", mt: 0.5 }}
                              />
                            </Tooltip>
                          )}
                        </TableCell>
                        <TableCell>
                          <TextField
                            size="small"
                            type="number"
                            variant="standard"
                            value={item.quantity}
                            onChange={(e) => handleItemChange(idx, "quantity", e.target.value)}
                          />
                        </TableCell>
                        <TableCell>
                          <TextField
                            size="small"
                            type="number"
                            variant="standard"
                            value={item.unitPrice}
                            onChange={(e) => handleItemChange(idx, "unitPrice", e.target.value)}
                          />
                        </TableCell>
                        <TableCell>
                          <TextField
                            size="small"
                            type="number"
                            variant="standard"
                            value={item.lineTotal}
                            onChange={(e) => handleItemChange(idx, "lineTotal", e.target.value)}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <IconButton size="small" color="error" onClick={() => handleDeleteItem(idx)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              <Divider sx={{ my: 2 }} />

              {/* Payer and Allocation Selection */}
              <Grid container spacing={2} sx={{ width: "100%" }}>
                <Grid size={{ xs: 12, sm: 4 }}>
                  <Typography variant="caption" sx={{ fontWeight: 600 }}>
                    Who Paid?
                  </Typography>
                  <TextField
                    select
                    fullWidth
                    size="small"
                    value={payerId}
                    onChange={(e) => setPayerId(e.target.value)}
                  >
                    {groupMembers.map((m) => (
                      <MenuItem key={m.id} value={String(m.id)}>
                        {m.name} {m.id === user?.id && "(You)"}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>

                <Grid size={{ xs: 12, sm: 4 }}>
                  <Typography variant="caption" sx={{ fontWeight: 600 }}>
                    Split Mode
                  </Typography>
                  <TextField
                    select
                    fullWidth
                    size="small"
                    value={splitType}
                    onChange={(e) => setSplitType(e.target.value)}
                  >
                    <MenuItem value="EQUAL">Split Equally Among All Members</MenuItem>
                  </TextField>
                </Grid>

                <Grid size={{ xs: 12, sm: 4 }}>
                  <Typography variant="caption" sx={{ fontWeight: 600 }}>
                    Category
                  </Typography>
                  <TextField
                    select
                    fullWidth
                    size="small"
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

              <Box sx={{ mt: 4, display: "flex", gap: 2, justifyContent: "flex-end" }}>
                <Button variant="outlined" color="inherit" onClick={() => setStage("IDLE")}>
                  Rescan New Image
                </Button>
                <Button
                  variant="contained"
                  color={currency !== "INR" ? "inherit" : "primary"}
                  startIcon={stage === "CONFIRMING" ? <CircularProgress size={18} color="inherit" /> : <ReceiptIcon />}
                  onClick={handleConfirmAndPost}
                  disabled={stage === "CONFIRMING" || stage === "DONE" || currency !== "INR"}
                  sx={{ px: 3 }}
                >
                  {stage === "CONFIRMING"
                    ? "Confirming..."
                    : currency !== "INR"
                    ? `Posting Restricted (${currency} Ledger Mismatch)`
                    : "Confirm & Post Expense"}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Stack>
      )}
    </Box>
  );
}
