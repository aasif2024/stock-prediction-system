import React, { useEffect, useState } from "react";
import { historyAPI } from "../api/api";

export default function History() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    historyAPI
      .list()
      .then((res) => setRows(res.data.history))
      .catch((err) => setError(err.response?.data?.error || "Failed to load history."))
      .finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this prediction?")) return;
    setIsDeleting(true);
    try {
      await historyAPI.delete(id);
      setRows((prevRows) => prevRows.filter((r) => r.id !== id));
    } catch (err) {
      setError(err.response?.data?.error || "Failed to delete prediction.");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="page history-page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <h2>Prediction History</h2>
        {!loading && rows.length > 0 && (
          <input 
            type="text" 
            placeholder="Search company..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ padding: "10px 16px", borderRadius: "20px", border: "1px solid var(--glass-border)", background: "rgba(15, 23, 42, 0.6)", color: "var(--text)", width: "250px" }}
          />
        )}
      </div>

      {loading && <p>Loading...</p>}
      {error && <div className="alert-error">{error}</div>}
      {!loading && !error && rows.length === 0 && (
        <p className="empty-state">You haven't made any predictions yet.</p>
      )}

      {!loading && rows.length > 0 && (
        <div style={{ overflowX: "auto", borderRadius: "8px", border: "1px solid var(--glass-border)", background: "rgba(15, 23, 42, 0.4)" }}>
          <table className="data-table" style={{ border: "none", margin: 0 }}>
          <thead>
            <tr>
              <th>Company</th>
              <th>Open</th>
              <th>High</th>
              <th>Low</th>
              <th>Close</th>
              <th>Traded Qty</th>
              <th>Predicted Price</th>
              <th>Direction</th>
              <th>Date</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {rows
              .filter(r => r.company_name.toLowerCase().includes(searchTerm.toLowerCase()) || r.equity_name.toLowerCase().includes(searchTerm.toLowerCase()))
              .map((r) => (
              <tr key={r.id}>
                <td style={{ fontWeight: "600" }}>{r.company_name} <span style={{ color: "var(--text-muted)", fontWeight: "400", fontSize: "0.85em" }}>({r.equity_name})</span></td>
                <td>₹{r.input_open}</td>
                <td>₹{r.input_high}</td>
                <td>₹{r.input_low}</td>
                <td>₹{r.input_close}</td>
                <td>{r.input_traded_qty.toLocaleString()}</td>
                <td style={{ fontWeight: "700" }}>₹{r.predicted_price}</td>
                <td>
                  <span style={{ 
                    display: "inline-block", padding: "4px 10px", borderRadius: "12px", fontSize: "0.75rem", fontWeight: "700",
                    background: r.direction === "UP" ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                    color: r.direction === "UP" ? "#10b981" : "#ef4444"
                  }}>
                    {r.direction === "UP" ? "▲ UP" : "▼ DOWN"}
                  </span>
                </td>
                <td style={{ color: "var(--text-muted)", fontSize: "0.9em" }}>{new Date(r.predicted_at).toLocaleString()}</td>
                <td>
                  <button 
                    className="btn-delete"
                    onClick={() => handleDelete(r.id)}
                    disabled={isDeleting}
                    style={{ background: "transparent", color: "#ef4444", border: "1px solid #ef4444", padding: "4px 8px", borderRadius: "4px", cursor: "pointer", fontSize: "0.8rem", transition: "all 0.2s" }}
                    onMouseOver={(e) => { e.currentTarget.style.background = "#ef4444"; e.currentTarget.style.color = "white"; }}
                    onMouseOut={(e) => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#ef4444"; }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      )}
    </div>
  );
}
