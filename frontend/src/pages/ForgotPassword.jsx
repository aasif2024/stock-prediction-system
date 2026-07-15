import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authAPI } from "../api/api";

export default function ForgotPassword() {
  const [form, setForm] = useState({ email: "", new_password: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);
    try {
      const res = await authAPI.resetPassword(form);
      setMessage(res.data.message);
      setTimeout(() => {
        navigate("/login");
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.error || "Password reset failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h2>Reset Password</h2>
        {error && <div className="alert-error">{error}</div>}
        {message && <div className="alert-success" style={{ color: "#00e676", marginBottom: "1rem", textAlign: "center" }}>{message}</div>}
        <label>Email</label>
        <input type="email" name="email" value={form.email} onChange={handleChange} required />
        <label>New Password</label>
        <input type="password" name="new_password" value={form.new_password} onChange={handleChange} required minLength={6} />
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "Resetting..." : "Reset Password"}
        </button>
        <p className="auth-switch">
          Remember your password? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  );
}
