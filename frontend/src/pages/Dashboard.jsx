import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { historyAPI, companyAPI, watchlistAPI } from "../api/api";
import { useAuth } from "../context/AuthContext";
import TickerTape from "../components/TickerTape";

export default function Dashboard() {
  const { user } = useAuth();
  const [recent, setRecent] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [companyCount, setCompanyCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const [historyRes, companiesRes, watchlistRes] = await Promise.all([
          historyAPI.list(),
          companyAPI.list(),
          watchlistAPI.list(),
        ]);
        setRecent(historyRes.data.history.slice(0, 5));
        setCompanyCount(companiesRes.data.companies.length);
        setWatchlist(watchlistRes.data.watchlist || []);
      } catch (err) {
        setError(err.response?.data?.error || "Failed to load dashboard data.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <>
      <TickerTape />
      <div className="page dashboard-page">
        <h2>Welcome back, {user?.full_name}</h2>

      <div className="stat-grid">
        <div className="stat-card">
          <span className="stat-value">{companyCount}</span>
          <span className="stat-label">Companies Available</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{recent.length}</span>
          <span className="stat-label">Recent Predictions</span>
        </div>
      </div>

      <div className="dashboard-actions">
        <Link to="/predict" className="btn-primary">New Prediction</Link>
        <Link to="/history" className="btn-secondary">View Full History</Link>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-section">
          <h3>⭐ My Watchlist</h3>
          {loading && <p>Loading...</p>}
          {!loading && watchlist.length === 0 && (
            <p className="empty-state">No companies in your watchlist yet.</p>
          )}
          {!loading && watchlist.length > 0 && (
            <div className="stat-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", marginBottom: "2rem" }}>
              {watchlist.map((item) => (
                <div key={item.equity_name} className="stat-card" style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <button 
                    onClick={async () => {
                      try {
                        await watchlistAPI.remove(item.equity_name);
                        setWatchlist(watchlist.filter(w => w.equity_name !== item.equity_name));
                      } catch (e) {
                        console.error(e);
                      }
                    }}
                    style={{ position: 'absolute', top: '10px', right: '10px', background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                  >
                    ✕
                  </button>
                  <span className="stat-label" style={{ fontWeight: '700', color: 'var(--text)', fontSize: '1.1rem' }}>{item.equity_name}</span>
                  {item.close ? (
                    <>
                      <span className="stat-value" style={{ fontSize: '1.4rem' }}>₹{item.close}</span>
                      <span className={item.change_val >= 0 ? "text-up" : "text-down"} style={{ fontSize: '0.85rem', fontWeight: 'bold' }}>
                        {item.change_val >= 0 ? "▲" : "▼"} {Math.abs(item.change_val)} ({Math.abs(item.change_pct)}%)
                      </span>
                      {item.shares > 0 && (
                        <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Portfolio: {item.shares} shares @ ₹{item.buy_price}</div>
                          <div style={{ 
                            fontSize: '0.9rem', 
                            fontWeight: 'bold', 
                            color: ((item.close - item.buy_price) * item.shares) >= 0 ? "var(--primary)" : "#ef4444" 
                          }}>
                            P&L: ₹{((item.close - item.buy_price) * item.shares).toFixed(2)}
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <span className="stat-value" style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>Market Closed</span>
                  )}
                </div>
              ))}
            </div>
          )}

          <h3>Recent Predictions</h3>
      {loading && <p>Loading...</p>}
      {error && <div className="alert-error">{error}</div>}
      {!loading && !error && recent.length === 0 && (
        <p className="empty-state">No predictions yet — try making your first one!</p>
      )}
      {!loading && recent.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Company</th>
              <th>Predicted Price</th>
              <th>Direction</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {recent.map((p) => (
              <tr key={p.id}>
                <td>{p.equity_name}</td>
                <td>₹{p.predicted_price}</td>
                <td className={p.direction === "UP" ? "text-up" : "text-down"}>
                  {p.direction === "UP" ? "▲ UP" : "▼ DOWN"}
                </td>
                <td>{new Date(p.predicted_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
        </div>
      </div>
    </div>
    </>
  );
}
