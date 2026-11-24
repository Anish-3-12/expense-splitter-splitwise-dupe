import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Stack,
  Breadcrumbs,
  Link as MuiLink,
} from "@mui/material";
import { ArrowBack as ArrowBackIcon, GroupAdd as GroupAddIcon } from "@mui/icons-material";
import api from "../api/axios";
import PageHeader from "../components/PageHeader";

export default function CreateGroup() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please provide a group name.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await api.post("/groups", { name: name.trim() });
      if (res.data?.id) {
        navigate(`/groups/${res.data.id}`);
      } else {
        navigate("/groups");
      }
    } catch (err) {
      console.error("Failed to create group:", err);
      setError(err?.response?.data?.message || err?.response?.data || "Failed to create group.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 640, mx: "auto" }}>
      <Breadcrumbs sx={{ mb: 2 }}>
        <MuiLink
          component="button"
          underline="hover"
          color="inherit"
          onClick={() => navigate("/groups")}
          sx={{ display: "flex", alignItems: "center", gap: 0.5, cursor: "pointer" }}
        >
          <ArrowBackIcon fontSize="small" /> Back to Groups
        </MuiLink>
        <Typography color="text.primary">New Group</Typography>
      </Breadcrumbs>

      <PageHeader
        title="Create a New Group"
        subtitle="Start tracking shared living expenses, trips, dinner bills, or project costs."
      />

      <Card>
        <CardContent sx={{ p: 4 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <Stack spacing={3}>
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                  Group Name
                </Typography>
                <TextField
                  fullWidth
                  placeholder="e.g. Goa Trip 2026, Apartment 302, Weekly Dinners"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoFocus
                  required
                />
              </Box>

              <Box sx={{ p: 2, bgcolor: "slate.50", borderRadius: 2, border: "1px solid", borderColor: "slate.200" }}>
                <Typography variant="body2" sx={{ fontWeight: 600, color: "slate.700", mb: 0.5 }}>
                  What happens next?
                </Typography>
                <Typography variant="caption" sx={{ color: "slate.500", display: "block" }}>
                  1. You are automatically added as the group creator.
                </Typography>
                <Typography variant="caption" sx={{ color: "slate.500", display: "block" }}>
                  2. Add your friends or roommates by their registered email address.
                </Typography>
                <Typography variant="caption" sx={{ color: "slate.500", display: "block" }}>
                  3. Start splitting expenses, uploading receipts, and settling debts!
                </Typography>
              </Box>

              <Box sx={{ display: "flex", gap: 2, justifyContent: "flex-end", pt: 1 }}>
                <Button variant="outlined" color="inherit" onClick={() => navigate("/groups")} disabled={loading}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <GroupAddIcon />}
                  disabled={loading || !name.trim()}
                >
                  {loading ? "Creating..." : "Create Group"}
                </Button>
              </Box>
            </Stack>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
