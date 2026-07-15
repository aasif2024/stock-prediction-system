import React, { useState } from "react";
import { Link } from "react-router-dom";
import { authAPI } from "../api/api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);
    try {
      const res = await authAPI.forgotPassword({ email });
      setMessage(res.data.message);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to send reset email. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h2>Forgot Password</h2>
        <p style={{marginBottom: "1rem", color: "#b3b3b3", fontSize: "0.9rem", textAlign: "center"}}>
          Enter your email address and we'll send you a link to reset your password.
        </p>
        {error && <div className="alert-error">{error}</div>}
        {message && <div className="alert-success" style={{ color: "#00e676", marginBottom: "1rem", textAlign: "center" }}>{message}</div>}
        <label>Email</label>
        <input type="email" name="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "Sending..." : "Send Reset Link"}
        </button>
        <p className="auth-switch">
          Remember your password? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  );
}
