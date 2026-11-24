import React, { useState, useContext } from "react";
import { useNavigate, Link as RouterLink } from "react-router-dom";
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
  Link,
  InputAdornment,
  IconButton,
} from "@mui/material";
import {
  AccountBalanceWallet as WalletIcon,
  Visibility,
  VisibilityOff,
  AutoAwesome as AutoAwesomeIcon,
} from "@mui/icons-material";
import api from "../api/axios";
import { AuthContext } from "../context/AuthContext";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const resp = await api.post("/auth/login", { email, password });
      const token = resp.data?.token;
      if (!token) {
        setError("Login succeeded but no token returned by server.");
        setLoading(false);
        return;
      }

      login(token);
      api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      navigate("/dashboard");
    } catch (err) {
      if (err.response && err.response.data) {
        setError(
          typeof err.response.data === "string"
            ? err.response.data
            : err.response.data.message || "Invalid email or password."
        );
      } else {
        setError("Network error. Make sure the backend is running on port 8080.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "slate.50",
        p: 2,
      }}
    >
      <Card sx={{ maxWidth: 440, width: "100%", boxShadow: "0 20px 40px -15px rgba(15, 23, 42, 0.1)" }}>
        <CardContent sx={{ p: { xs: 3, sm: 4.5 } }}>
          {/* Logo & Headline */}
          <Box sx={{ textAlign: "center", mb: 3 }}>
            <Box
              sx={{
                width: 52,
                height: 52,
                borderRadius: 3,
                bgcolor: "primary.main",
                color: "#fff",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                mb: 1.5,
                boxShadow: "0 8px 16px -4px rgba(99, 102, 241, 0.4)",
              }}
            >
              <WalletIcon sx={{ fontSize: 30 }} />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: "slate.900" }}>
              Splitwise AI
            </Typography>
            <Typography variant="body2" sx={{ color: "text.secondary", mt: 0.5 }}>
              Intelligent group expenses & receipt intelligence
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <Stack spacing={2.5}>
              <Box>
                <Typography variant="caption" sx={{ fontWeight: 600, color: "slate.700", display: "block", mb: 0.75 }}>
                  Email Address
                </Typography>
                <TextField
                  fullWidth
                  placeholder="you@example.com"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </Box>

              <Box>
                <Typography variant="caption" sx={{ fontWeight: 600, color: "slate.700", display: "block", mb: 0.75 }}>
                  Password
                </Typography>
                <TextField
                  fullWidth
                  placeholder="••••••••"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          size="small"
                          onClick={() => setShowPassword(!showPassword)}
                          edge="end"
                        >
                          {showPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Box>

              <Button
                type="submit"
                variant="contained"
                size="large"
                fullWidth
                disabled={loading}
                sx={{ py: 1.2, fontWeight: 700 }}
              >
                {loading ? <CircularProgress size={22} color="inherit" /> : "Sign In to Splitwise AI"}
              </Button>
            </Stack>
          </form>

          <Box sx={{ mt: 3, textAlign: "center" }}>
            <Typography variant="body2" sx={{ color: "text.secondary" }}>
              Don't have an account?{" "}
              <Link component={RouterLink} to="/register" sx={{ fontWeight: 600, textDecoration: "none" }}>
                Create one now
              </Link>
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
