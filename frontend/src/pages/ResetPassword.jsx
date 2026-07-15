import React, { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { authAPI } from "../api/api";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) {
      setError("Invalid or missing reset token.");
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token) return;
    
    setError("");
    setMessage("");
    setLoading(true);
    try {
      const res = await authAPI.resetPassword({ token, new_password: newPassword });
      setMessage(res.data.message);
      setTimeout(() => {
        navigate("/login");
      }, 2500);
    } catch (err) {
      setError(err.response?.data?.error || "Password reset failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h2>Enter New Password</h2>
        {error && <div className="alert-error">{error}</div>}
        {message && <div className="alert-success" style={{ color: "#00e676", marginBottom: "1rem", textAlign: "center" }}>{message}</div>}
        
        <label>New Password</label>
        <input 
          type="password" 
          name="new_password" 
          value={newPassword} 
          onChange={(e) => setNewPassword(e.target.value)} 
          required 
          minLength={6} 
          disabled={!token || loading}
        />
        <button type="submit" className="btn-primary" disabled={!token || loading}>
          {loading ? "Resetting..." : "Reset Password"}
        </button>
        <p className="auth-switch">
          Remember your password? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  );
}
