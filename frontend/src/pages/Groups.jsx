import React, { useEffect, useState } from "react";
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  InputAdornment,
  Avatar,
  AvatarGroup,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Tooltip,
} from "@mui/material";
import {
  Add as AddIcon,
  Search as SearchIcon,
  Group as GroupIcon,
  ReceiptLong as ReceiptIcon,
  ArrowForward as ArrowForwardIcon,
  AccountBalanceWallet as WalletIcon,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";
import PageHeader from "../components/PageHeader";
import EmptyState from "../components/EmptyState";

export default function Groups() {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");

  // Create Group Dialog
  const [openCreate, setOpenCreate] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  const navigate = useNavigate();

  const fetchGroups = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get("/groups");
      setGroups(res.data || []);
    } catch (err) {
      console.error("Failed to load groups:", err);
      setError(err?.response?.data?.message || "Failed to load groups.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGroups();
  }, []);

  const handleCreateGroup = async (e) => {
    e.preventDefault();
    if (!newGroupName.trim()) return;
    try {
      setCreating(true);
      setCreateError("");
      const res = await api.post("/groups", { name: newGroupName.trim() });
      setOpenCreate(false);
      setNewGroupName("");
      fetchGroups();
      if (res.data?.id) {
        navigate(`/groups/${res.data.id}`);
      }
    } catch (err) {
      console.error("Failed to create group:", err);
      setCreateError(err?.response?.data?.message || "Failed to create group.");
    } finally {
      setCreating(false);
    }
  };

  const filteredGroups = groups.filter((g) =>
    g.name?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Box>
      <PageHeader
        title="Expense Groups"
        subtitle="Manage your sharing circles, monitor group spending, and settle balances"
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenCreate(true)}
            sx={{ px: 2.5 }}
          >
            Create Group
          </Button>
        }
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Search & filter toolbar */}
      <Box sx={{ mb: 3, display: "flex", gap: 2, alignItems: "center" }}>
        <TextField
          placeholder="Search groups by name..."
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ maxWidth: 360, width: "100%", bgcolor: "background.paper" }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" sx={{ color: "text.secondary" }} />
              </InputAdornment>
            ),
          }}
        />
        <Typography variant="body2" sx={{ color: "text.secondary", ml: "auto" }}>
          {filteredGroups.length} {filteredGroups.length === 1 ? "group" : "groups"} found
        </Typography>
      </Box>

      {/* Groups Grid */}
      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
          <CircularProgress />
        </Box>
      ) : filteredGroups.length === 0 ? (
        <EmptyState
          icon={GroupIcon}
          title={search ? "No matching groups" : "No expense groups yet"}
          description={
            search
              ? `No groups match the search "${search}". Try another query.`
              : "Create a group to start tracking shared expenses, scanning receipts, and settling balances."
          }
          actionLabel={search ? "Clear Search" : "Create First Group"}
          onAction={search ? () => setSearch("") : () => setOpenCreate(true)}
        />
      ) : (
        <Grid container spacing={3} sx={{ width: "100%" }}>
          {filteredGroups.map((group) => {
            const memberCount = group.memberCount ?? group.members?.length ?? 0;
            return (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={group.id}>
                <Card
                  sx={{
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    transition: "all 0.2s ease-in-out",
                    "&:hover": {
                      transform: "translateY(-3px)",
                      boxShadow: "0 12px 24px -10px rgba(15, 23, 42, 0.12)",
                      borderColor: "primary.main",
                    },
                  }}
                >
                  <CardContent sx={{ p: 3, flexGrow: 1, display: "flex", flexDirection: "column" }}>
                    <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", mb: 2 }}>
                      <Box
                        sx={{
                          width: 44,
                          height: 44,
                          borderRadius: 2,
                          bgcolor: "primary.50",
                          color: "primary.main",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontWeight: 700,
                          fontSize: "1.1rem",
                        }}
                      >
                        {group.name?.charAt(0).toUpperCase()}
                      </Box>
                      <Chip
                        size="small"
                        icon={<GroupIcon sx={{ fontSize: 14 }} />}
                        label={`${memberCount} ${memberCount === 1 ? "member" : "members"}`}
                        variant="outlined"
                        sx={{ borderRadius: 1.5, borderColor: "divider", fontSize: "0.75rem" }}
                      />
                    </Box>

                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                      {group.name}
                    </Typography>

                    <Typography variant="body2" sx={{ color: "text.secondary", mb: 3 }}>
                      Group #{group.id} • Created {group.createdAt ? new Date(group.createdAt).toLocaleDateString() : "recently"}
                    </Typography>

                    {/* Member Avatars */}
                    {group.members && group.members.length > 0 && (
                      <Box sx={{ display: "flex", alignItems: "center", mb: 3, mt: "auto" }}>
                        <AvatarGroup max={4} sx={{ "& .MuiAvatar-root": { width: 28, height: 28, fontSize: "0.75rem" } }}>
                          {group.members.map((m) => (
                            <Tooltip title={m.name || m.email} key={m.id}>
                              <Avatar sx={{ bgcolor: "slate.300", color: "slate.800" }}>
                                {(m.name || m.email || "U").charAt(0).toUpperCase()}
                              </Avatar>
                            </Tooltip>
                          ))}
                        </AvatarGroup>
                      </Box>
                    )}

                    <Box sx={{ pt: 2, borderTop: "1px solid", borderColor: "divider", display: "flex", gap: 1 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        fullWidth
                        startIcon={<ReceiptIcon fontSize="small" />}
                        onClick={() => navigate(`/groups/${group.id}/add-expense`)}
                        sx={{ whiteSpace: "nowrap" }}
                      >
                        Add Expense
                      </Button>
                      <Button
                        size="small"
                        variant="contained"
                        fullWidth
                        endIcon={<ArrowForwardIcon fontSize="small" />}
                        onClick={() => navigate(`/groups/${group.id}`)}
                      >
                        Details
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Quick Create Group Dialog */}
      <Dialog open={openCreate} onClose={() => setOpenCreate(false)} maxWidth="xs" fullWidth>
        <form onSubmit={handleCreateGroup}>
          <DialogTitle sx={{ fontWeight: 700 }}>Create New Group</DialogTitle>
          <DialogContent>
            {createError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {createError}
              </Alert>
            )}
            <Typography variant="body2" sx={{ color: "text.secondary", mb: 2 }}>
              Give your group a name (e.g., "Apartment 4B", "Goa Trip", "Family"). You can invite friends right after.
            </Typography>
            <TextField
              autoFocus
              fullWidth
              label="Group Name"
              placeholder="e.g. Goa Trip 2026"
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
              required
              margin="dense"
            />
          </DialogContent>
          <DialogActions sx={{ p: 2.5, pt: 0 }}>
            <Button onClick={() => setOpenCreate(false)} color="inherit" disabled={creating}>
              Cancel
            </Button>
            <Button type="submit" variant="contained" disabled={creating || !newGroupName.trim()}>
              {creating ? <CircularProgress size={20} /> : "Create Group"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}
