import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { historyAPI, companyAPI, watchlistAPI } from "../api/api";
import { useAuth } from "../context/AuthContext";
import TickerTape from "../components/TickerTape";

// Format UTC datetime string → IST readable format
function formatIST(utcStr) {
  if (!utcStr) return "—";
  try {
    // SQLite stores as "YYYY-MM-DD HH:MM:SS" (UTC), parse as UTC explicitly
    const normalized = utcStr.trim().replace(" ", "T") + (utcStr.includes("Z") ? "" : "Z");
    const dt = new Date(normalized);
    if (isNaN(dt.getTime())) return utcStr;
    return dt.toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata",
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  } catch {
    return utcStr;
  }
}

export default function Dashboard() {
  const { user } = useAuth();
  const [recent, setRecent] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [companyCount, setCompanyCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [watchlistLoading, setWatchlistLoading] = useState(false);
  const [error, setError] = useState("");
  const [removingItem, setRemovingItem] = useState(null);

  const loadWatchlist = useCallback(async () => {
    setWatchlistLoading(true);
    try {
      const res = await watchlistAPI.list();
      setWatchlist(res.data.watchlist || []);
    } catch (err) {
      console.error("Watchlist load error:", err);
    } finally {
      setWatchlistLoading(false);
    }
  }, []);

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

            {/* ── Watchlist ── */}
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "1rem" }}>
              <h3 style={{ margin: 0 }}>⭐ MY WATCHLIST</h3>
              <button
                onClick={loadWatchlist}
                disabled={watchlistLoading}
                style={{
                  background: "var(--primary)",
                  border: "none",
                  borderRadius: "6px",
                  color: "#fff",
                  padding: "4px 12px",
                  fontSize: "0.78rem",
                  cursor: "pointer",
                  opacity: watchlistLoading ? 0.6 : 1,
                }}
              >
                {watchlistLoading ? "Refreshing..." : "🔄 Refresh Live Prices"}
              </button>
            </div>

            {(loading || watchlistLoading) && <p>Loading watchlist...</p>}
            {!loading && !watchlistLoading && watchlist.length === 0 && (
              <p className="empty-state">
                No companies in your watchlist yet.
                <br />
                <Link to="/predict" style={{ color: "var(--primary)", textDecoration: "underline" }}>
                  Go to Predict page → Add to Watchlist
                </Link>
              </p>
            )}
            {!loading && watchlist.length > 0 && (() => {
              // ── Portfolio Totals ─────────────────────────────────────
              let totalInvested = 0, totalCurrent = 0, hasPortfolio = false;
              watchlist.forEach((item) => {
                const shares = Number(item.shares) || 0;
                const buyP   = Number(item.buy_price) || 0;
                const close  = Number(item.close) || 0;
                if (shares > 0 && buyP > 0 && close > 0) {
                  totalInvested += shares * buyP;
                  totalCurrent  += shares * close;
                  hasPortfolio = true;
                }
              });
              const totalPnl    = totalCurrent - totalInvested;
              const totalPnlPct = totalInvested > 0 ? (totalPnl / totalInvested) * 100 : 0;
              const totalIsProfit = totalPnl >= 0;
              const totalColor    = totalIsProfit ? "#10b981" : "#ef4444";

              return (
                <>
                  {/* ── Portfolio Summary Banner ── */}
                  {hasPortfolio && (
                    <div style={{
                      display: "flex", flexWrap: "wrap",
                      marginBottom: "1.5rem",
                      border: `1px solid ${totalIsProfit ? "rgba(16,185,129,0.35)" : "rgba(239,68,68,0.35)"}`,
                      borderRadius: "14px",
                      overflow: "hidden",
                      background: totalIsProfit ? "rgba(16,185,129,0.04)" : "rgba(239,68,68,0.04)",
                    }}>
                      {[
                        {
                          label: "TOTAL INVESTED",
                          value: `₹${totalInvested.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
                          color: "var(--text)",
                        },
                        {
                          label: "CURRENT VALUE",
                          value: `₹${totalCurrent.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
                          color: "var(--text)",
                        },
                        {
                          label: totalIsProfit ? "✅ TOTAL PROFIT" : "❌ TOTAL LOSS",
                          value: `${totalPnl >= 0 ? "+" : "−"}₹${Math.abs(totalPnl).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
                          sub: `${totalPnlPct >= 0 ? "+" : ""}${totalPnlPct.toFixed(2)}% overall return`,
                          color: totalColor,
                          bold: true,
                        },
                      ].map((stat, i) => (
                        <div key={i} style={{
                          flex: "1 1 160px",
                          padding: "16px 22px",
                          borderRight: i < 2 ? "1px solid rgba(255,255,255,0.08)" : "none",
                        }}>
                          <div style={{ fontSize: "0.63rem", color: "var(--text-muted)", letterSpacing: "0.09em", fontWeight: 700, marginBottom: "6px" }}>
                            {stat.label}
                          </div>
                          <div style={{ fontSize: stat.bold ? "1.2rem" : "1.05rem", fontWeight: stat.bold ? 900 : 700, color: stat.color }}>
                            {stat.value}
                          </div>
                          {stat.sub && (
                            <div style={{ fontSize: "0.75rem", color: totalColor, fontWeight: 600, marginTop: "3px" }}>
                              {stat.sub}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* ── Watchlist Cards ── */}
                  <div style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
                    gap: "16px",
                    marginBottom: "2rem",
                  }}>
                    {watchlist.map((item) => {
                      const shares    = Number(item.shares) || 0;
                      const buyP      = Number(item.buy_price) || 0;
                      const close     = Number(item.close) || 0;
                      const changeVal = item.change_val != null ? Number(item.change_val) : null;
                      const changePct = item.change_pct != null ? Number(item.change_pct) : null;
                      const dayIsUp   = changeVal != null ? changeVal >= 0 : null;

                      // P&L calculation — core of the card
                      const hasPosition = shares > 0 && buyP > 0 && close > 0;
                      const pnl     = hasPosition ? (close - buyP) * shares : null;
                      const pnlPct  = hasPosition ? ((close - buyP) / buyP) * 100 : null;
                      const isProfit = pnl !== null && pnl >= 0;
                      const pnlColor  = pnl === null ? "var(--text-muted)" : isProfit ? "#10b981" : "#ef4444";
                      const cardBorder = pnl === null
                        ? "var(--glass-border)"
                        : isProfit ? "rgba(16,185,129,0.4)" : "rgba(239,68,68,0.4)";
                      const pnlBg = pnl === null ? "rgba(255,255,255,0.03)"
                        : isProfit ? "rgba(16,185,129,0.07)" : "rgba(239,68,68,0.07)";

                      return (
                        <div
                          key={item.equity_name}
                          style={{
                            background: "var(--bg-secondary)",
                            border: `1px solid ${cardBorder}`,
                            borderRadius: "14px",
                            padding: "18px",
                            display: "flex",
                            flexDirection: "column",
                            gap: "0",
                            position: "relative",
                            transition: "transform 0.18s, box-shadow 0.18s",
                          }}
                          onMouseEnter={e => {
                            e.currentTarget.style.transform = "translateY(-3px)";
                            e.currentTarget.style.boxShadow = "0 10px 30px rgba(0,0,0,0.25)";
                          }}
                          onMouseLeave={e => {
                            e.currentTarget.style.transform = "none";
                            e.currentTarget.style.boxShadow = "none";
                          }}
                        >
                          {/* ── Remove Button ── */}
                          {removingItem === item.equity_name ? (
                            <div style={{
                              position: "absolute", top: "12px", right: "12px",
                              display: "flex", gap: "5px", alignItems: "center",
                              background: "rgba(239,68,68,0.12)",
                              border: "1px solid rgba(239,68,68,0.4)",
                              borderRadius: "8px", padding: "4px 8px",
                            }}>
                              <span style={{ fontSize: "0.68rem", color: "#ef4444", fontWeight: 700 }}>Remove?</span>
                              <button
                                onClick={async () => {
                                  try {
                                    await watchlistAPI.remove(item.equity_name);
                                    setWatchlist(prev => prev.filter(w => w.equity_name !== item.equity_name));
                                    setRemovingItem(null);
                                  } catch { setRemovingItem(null); }
                                }}
                                style={{ background: "#ef4444", border: "none", color: "#fff", cursor: "pointer", borderRadius: "4px", padding: "2px 7px", fontSize: "0.68rem", fontWeight: 700 }}
                              >Yes</button>
                              <button
                                onClick={() => setRemovingItem(null)}
                                style={{ background: "transparent", border: "1px solid var(--glass-border)", color: "var(--text-muted)", cursor: "pointer", borderRadius: "4px", padding: "2px 7px", fontSize: "0.68rem" }}
                              >No</button>
                            </div>
                          ) : (
                            <button
                              onClick={() => setRemovingItem(item.equity_name)}
                              title="Remove from watchlist"
                              style={{
                                position: "absolute", top: "12px", right: "12px",
                                background: "transparent", border: "none",
                                color: "var(--text-muted)", cursor: "pointer",
                                fontSize: "1rem", padding: "2px 5px",
                                borderRadius: "4px", transition: "color 0.15s",
                              }}
                              onMouseEnter={e => e.target.style.color = "#ef4444"}
                              onMouseLeave={e => e.target.style.color = "var(--text-muted)"}
                            >✕</button>
                          )}

                          {/* ── Company Name ── */}
                          <div style={{ paddingRight: "28px", marginBottom: "10px" }}>
                            <div style={{ fontWeight: 800, fontSize: "1rem", color: "var(--text)" }}>
                              {item.equity_name}
                            </div>
                            {item.date && (
                              <div style={{ fontSize: "0.67rem", color: "var(--text-muted)", marginTop: "2px" }}>
                                As of {item.date}
                              </div>
                            )}
                          </div>

                          {/* ── Live Price + Day Change ── */}
                          <div style={{ marginBottom: "14px" }}>
                            {close > 0 ? (
                              <>
                                <div style={{ fontSize: "1.55rem", fontWeight: 800, color: "var(--text)", lineHeight: 1 }}>
                                  ₹{close.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </div>
                                {dayIsUp !== null && changeVal !== null && (
                                  <div style={{
                                    fontSize: "0.78rem", fontWeight: 600, marginTop: "4px",
                                    color: dayIsUp ? "#10b981" : "#ef4444",
                                  }}>
                                    {dayIsUp ? "▲" : "▼"} ₹{Math.abs(changeVal).toFixed(2)}
                                    {changePct !== null && ` (${Math.abs(changePct).toFixed(2)}%) today`}
                                  </div>
                                )}
                              </>
                            ) : (
                              <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                                Market Closed / No Data
                              </div>
                            )}
                          </div>

                          {/* ══ P&L BLOCK — THE HERO ══ */}
                          <div style={{
                            background: pnlBg,
                            border: `1px solid ${cardBorder}`,
                            borderRadius: "10px",
                            padding: "14px",
                            flexGrow: 1,
                          }}>
                            {hasPosition ? (
                              <>
                                {/* Holdings row */}
                                <div style={{
                                  fontSize: "0.68rem", color: "var(--text-muted)",
                                  marginBottom: "10px",
                                }}>
                                  {shares} shares &nbsp;·&nbsp; Avg buy ₹{buyP.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </div>

                                {/* Invested / Current */}
                                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
                                  <div>
                                    <div style={{ fontSize: "0.6rem", textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: "3px" }}>Invested</div>
                                    <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "var(--text)" }}>
                                      ₹{(shares * buyP).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                    </div>
                                  </div>
                                  <div style={{ width: "1px", background: "rgba(255,255,255,0.08)" }} />
                                  <div style={{ textAlign: "right" }}>
                                    <div style={{ fontSize: "0.6rem", textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: "3px" }}>Current</div>
                                    <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "var(--text)" }}>
                                      ₹{(shares * close).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                    </div>
                                  </div>
                                </div>

                                {/* Separator */}
                                <div style={{ height: "1px", background: "rgba(255,255,255,0.08)", marginBottom: "12px" }} />

                                {/* BIG P&L ROW */}
                                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                  <div>
                                    <div style={{
                                      fontSize: "0.62rem", fontWeight: 800,
                                      color: pnlColor, textTransform: "uppercase",
                                      letterSpacing: "0.08em", marginBottom: "4px",
                                    }}>
                                      {isProfit ? "✅ PROFIT" : "❌ LOSS"}
                                    </div>
                                    <div style={{
                                      fontSize: "1.5rem", fontWeight: 900,
                                      color: pnlColor, lineHeight: 1,
                                    }}>
                                      {pnl >= 0 ? "+" : "−"}₹{Math.abs(pnl).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                    </div>
                                  </div>
                                  <div style={{
                                    background: isProfit ? "rgba(16,185,129,0.18)" : "rgba(239,68,68,0.18)",
                                    border: `1.5px solid ${pnlColor}`,
                                    borderRadius: "10px",
                                    padding: "6px 12px",
                                    fontSize: "1rem",
                                    fontWeight: 900,
                                    color: pnlColor,
                                    letterSpacing: "0.01em",
                                  }}>
                                    {pnlPct >= 0 ? "+" : ""}{pnlPct.toFixed(2)}%
                                  </div>
                                </div>
                              </>
                            ) : (
                              <div style={{
                                textAlign: "center", padding: "10px 0",
                                color: "var(--text-muted)", fontSize: "0.78rem",
                              }}>
                                <div style={{ fontSize: "1.2rem", marginBottom: "4px" }}>📊</div>
                                <strong>No position tracked</strong>
                                <div style={{ fontSize: "0.7rem", marginTop: "4px", opacity: 0.7 }}>
                                  Add shares &amp; buy price to see P&amp;L
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </>
              );
            })()}

            {/* ── Recent Predictions ── */}
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
                    <th>Date & Time (IST)</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((p) => (
                    <tr key={p.id}>
                      <td>{p.equity_name}</td>
                      <td>₹{Number(p.predicted_price).toFixed(2)}</td>
                      <td className={p.direction === "UP" ? "text-up" : "text-down"}>
                        {p.direction === "UP" ? "▲ UP" : "▼ DOWN"}
                      </td>
                      <td>{formatIST(p.predicted_at)}</td>
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
