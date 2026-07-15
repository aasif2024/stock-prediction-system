import React, { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { authAPI } from "../api/api";

export default function ResetPassword() {
  const navigate = useNavigate();
  const location = useLocation();
  const { email, otp } = location.state || {};

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPass, setShowPass] = useState(false);

  // Redirect if no email/otp passed
  useEffect(() => {
    if (!email || !otp) {
      navigate("/forgot-password");
    }
  }, [email, otp, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");

    if (newPassword.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const res = await authAPI.resetPassword({
        email,
        otp,
        new_password: newPassword,
      });
      setMessage(res.data.message || "Password reset successfully!");
      setTimeout(() => navigate("/login"), 2500);
    } catch (err) {
      const errMsg = err.response?.data?.error || "Password reset failed.";
      setError(errMsg);
      // If OTP is invalid/expired, send back to verify page
      if (errMsg.includes("OTP") || errMsg.includes("expired")) {
        setTimeout(() => navigate("/forgot-password"), 2000);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
          <div style={{ fontSize: "3rem", marginBottom: "0.5rem" }}>🔑</div>
          <h2 style={{ margin: 0 }}>New Password</h2>
          <p style={{ color: "#b3b3b3", fontSize: "0.9rem", marginTop: "0.5rem" }}>
            Create a strong new password for <strong style={{ color: "#fff" }}>{email}</strong>
          </p>
        </div>

        {error && <div className="alert-error">{error}</div>}
        {message && (
          <div
            style={{
              background: "rgba(0, 230, 118, 0.1)",
              border: "1px solid #00e676",
              borderRadius: "10px",
              padding: "1rem",
              textAlign: "center",
              marginBottom: "1rem",
              color: "#00e676",
            }}
          >
            ✅ {message} Redirecting to login...
          </div>
        )}

        <label>New Password</label>
        <div style={{ position: "relative" }}>
          <input
            type={showPass ? "text" : "password"}
            name="new_password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="At least 6 characters"
            required
            minLength={6}
            style={{ paddingRight: "3rem", width: "100%", boxSizing: "border-box" }}
          />
          <button
            type="button"
            onClick={() => setShowPass((p) => !p)}
            style={{
              position: "absolute",
              right: "0.75rem",
              top: "50%",
              transform: "translateY(-50%)",
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "#b3b3b3",
              fontSize: "1.1rem",
            }}
          >
            {showPass ? "🙈" : "👁️"}
          </button>
        </div>

        <label style={{ marginTop: "1rem" }}>Confirm Password</label>
        <input
          type={showPass ? "text" : "password"}
          name="confirm_password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="Repeat your password"
          required
          minLength={6}
        />

        {/* Password strength indicator */}
        {newPassword && (
          <div style={{ marginTop: "0.5rem" }}>
            <div style={{ height: "4px", background: "#333", borderRadius: "4px", overflow: "hidden" }}>
              <div
                style={{
                  height: "100%",
                  borderRadius: "4px",
                  width:
                    newPassword.length >= 12
                      ? "100%"
                      : newPassword.length >= 8
                      ? "66%"
                      : "33%",
                  background:
                    newPassword.length >= 12
                      ? "#00e676"
                      : newPassword.length >= 8
                      ? "#ffab40"
                      : "#ff5252",
                  transition: "width 0.3s ease",
                }}
              />
            </div>
            <p style={{ color: "#b3b3b3", fontSize: "0.75rem", margin: "0.25rem 0 0" }}>
              {newPassword.length >= 12 ? "Strong" : newPassword.length >= 8 ? "Medium" : "Weak"} password
            </p>
          </div>
        )}

        <button type="submit" className="btn-primary" disabled={loading} style={{ marginTop: "1.5rem" }}>
          {loading ? "Resetting..." : "Reset Password"}
        </button>

        <p className="auth-switch">
          <Link to="/forgot-password" style={{ color: "#b3b3b3" }}>
            ← Start over
          </Link>
        </p>
      </form>
    </div>
  );
}
