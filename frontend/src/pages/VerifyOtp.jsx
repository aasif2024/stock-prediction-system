import React, { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { authAPI } from "../api/api";

export default function VerifyOtp() {
  const navigate = useNavigate();
  const location = useLocation();
  const { email, message, demo_otp } = location.state || {};

  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendMsg, setResendMsg] = useState("");
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes in seconds

  // Redirect if no email passed in state
  useEffect(() => {
    if (!email) {
      navigate("/forgot-password");
    }
  }, [email, navigate]);

  // Countdown timer
  useEffect(() => {
    if (timeLeft <= 0) return;
    const timer = setInterval(() => setTimeLeft((t) => t - 1), 1000);
    return () => clearInterval(timer);
  }, [timeLeft]);

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60).toString().padStart(2, "0");
    const s = (secs % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    if (!otp || otp.length !== 6) {
      setError("Please enter the 6-digit OTP.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      // Verify OTP is valid before going to next step — we do a "dry" pre-check
      // by navigating with state; actual verification happens on reset page
      navigate("/reset-password", {
        state: { email, otp },
      });
    } catch (err) {
      setError(err.response?.data?.error || "Verification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResendMsg("");
    setError("");
    setResendLoading(true);
    try {
      const res = await authAPI.forgotPassword({ email });
      setResendMsg("A new OTP has been sent!");
      setTimeLeft(600);
      // Update demo OTP if returned
      if (res.data.demo_otp) {
        navigate("/verify-otp", {
          state: { email, message: res.data.message, demo_otp: res.data.demo_otp },
        });
      }
    } catch (err) {
      setResendMsg("Failed to resend OTP. Please try again.");
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="page auth-page">
      <form className="auth-card" onSubmit={handleVerify}>
        <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
          <div style={{ fontSize: "3rem", marginBottom: "0.5rem" }}>📧</div>
          <h2 style={{ margin: 0 }}>Enter OTP</h2>
          <p style={{ color: "#b3b3b3", fontSize: "0.9rem", marginTop: "0.5rem" }}>
            {message || `A 6-digit code was sent to`}{" "}
            <strong style={{ color: "#fff" }}>{email}</strong>
          </p>
        </div>

        {/* Demo OTP display — only visible when no SMTP is configured */}
        {demo_otp && (
          <div
            style={{
              background: "rgba(0, 230, 118, 0.1)",
              border: "1px solid #00e676",
              borderRadius: "10px",
              padding: "1rem",
              textAlign: "center",
              marginBottom: "1rem",
            }}
          >
            <p style={{ color: "#b3b3b3", fontSize: "0.8rem", margin: "0 0 0.3rem 0" }}>
              🔧 Demo Mode — No email server configured. Your OTP is:
            </p>
            <p
              style={{
                color: "#00e676",
                fontSize: "2rem",
                fontWeight: "bold",
                letterSpacing: "0.5rem",
                margin: 0,
              }}
            >
              {demo_otp}
            </p>
          </div>
        )}

        {error && <div className="alert-error">{error}</div>}
        {resendMsg && <p style={{ color: "#00e676", textAlign: "center", fontSize: "0.9rem" }}>{resendMsg}</p>}

        <label>6-Digit OTP Code</label>
        <input
          type="text"
          name="otp"
          value={otp}
          onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))}
          placeholder="• • • • • •"
          maxLength={6}
          required
          style={{ letterSpacing: "0.5rem", fontSize: "1.5rem", textAlign: "center" }}
        />

        {/* Countdown */}
        <p style={{ textAlign: "center", color: timeLeft < 60 ? "#ff5252" : "#b3b3b3", fontSize: "0.85rem" }}>
          {timeLeft > 0 ? `⏱ OTP expires in ${formatTime(timeLeft)}` : "⚠️ OTP may have expired. Please resend."}
        </p>

        <button type="submit" className="btn-primary" disabled={loading || otp.length !== 6}>
          {loading ? "Verifying..." : "Verify OTP →"}
        </button>

        <div style={{ textAlign: "center", marginTop: "1rem" }}>
          <button
            type="button"
            onClick={handleResend}
            disabled={resendLoading}
            style={{ background: "none", border: "none", color: "#00e676", cursor: "pointer", fontSize: "0.9rem" }}
          >
            {resendLoading ? "Resending..." : "Resend OTP"}
          </button>
          {" · "}
          <Link to="/forgot-password" style={{ color: "#b3b3b3", fontSize: "0.9rem" }}>
            Change Email
          </Link>
        </div>
      </form>
    </div>
  );
}
