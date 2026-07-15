import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authAPI } from "../api/api";

export default function ForgotPassword() {
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSendOtp = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);
    try {
      const res = await authAPI.forgotPassword({ email });
      setMessage(res.data.message);
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to send reset email. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);
    try {
      const res = await authAPI.resetPassword({ email, otp, new_password: newPassword });
      setMessage(res.data.message);
      setTimeout(() => navigate("/login"), 2500);
    } catch (err) {
      setError(err.response?.data?.error || "Password reset failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page auth-page">
      {step === 1 ? (
        <form className="auth-card" onSubmit={handleSendOtp}>
          <h2>Forgot Password</h2>
          <p style={{marginBottom: "1rem", color: "#b3b3b3", fontSize: "0.9rem", textAlign: "center"}}>
            Enter your email address to receive a 6-digit OTP.
          </p>
          {error && <div className="alert-error">{error}</div>}
          {message && <div className="alert-success" style={{ color: "#00e676", marginBottom: "1rem", textAlign: "center" }}>{message}</div>}
          <label>Email</label>
          <input type="email" name="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Sending..." : "Send OTP"}
          </button>
          <p className="auth-switch">
            Remember your password? <Link to="/login">Log in</Link>
          </p>
        </form>
      ) : (
        <form className="auth-card" onSubmit={handleResetPassword}>
          <h2>Enter OTP</h2>
          <p style={{marginBottom: "1rem", color: "#b3b3b3", fontSize: "0.9rem", textAlign: "center"}}>
            Enter the 6-digit code sent to {email}. Code expires in 10 minutes.
          </p>
          {error && <div className="alert-error">{error}</div>}
          {message && <div className="alert-success" style={{ color: "#00e676", marginBottom: "1rem", textAlign: "center" }}>{message}</div>}
          <label>OTP Code</label>
          <input type="text" name="otp" value={otp} onChange={(e) => setOtp(e.target.value)} required maxLength={6} />
          <label>New Password</label>
          <input type="password" name="new_password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={6} />
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Resetting..." : "Reset Password"}
          </button>
          <p className="auth-switch">
            Didn't receive it? <button type="button" onClick={() => setStep(1)} style={{background: 'none', border: 'none', color: '#00e676', cursor: 'pointer', padding: 0, font: 'inherit'}}>Try again</button>
          </p>
        </form>
      )}
    </div>
  );
}
