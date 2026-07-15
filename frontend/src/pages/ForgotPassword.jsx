import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authAPI } from "../api/api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await authAPI.forgotPassword({ email });
      const data = res.data;

      // Navigate to OTP verification page, passing email and demo_otp (if any)
      navigate("/verify-otp", {
        state: {
          email,
          message: data.message,
          demo_otp: data.demo_otp || null,
        },
      });
    } catch (err) {
      setError(err.response?.data?.error || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
          <div style={{ fontSize: "3rem", marginBottom: "0.5rem" }}>🔐</div>
          <h2 style={{ margin: 0 }}>Forgot Password</h2>
          <p style={{ color: "#b3b3b3", fontSize: "0.9rem", marginTop: "0.5rem" }}>
            Enter your registered email to receive an OTP.
          </p>
        </div>

        {error && <div className="alert-error">{error}</div>}

        <label>Email Address</label>
        <input
          type="email"
          name="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          required
        />

        <button type="submit" className="btn-primary" disabled={loading} style={{ marginTop: "1rem" }}>
          {loading ? "Sending OTP..." : "Send OTP"}
        </button>

        <p className="auth-switch">
          Remember your password? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  );
}
