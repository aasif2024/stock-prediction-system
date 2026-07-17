import React, { useEffect, useState } from "react";
import { companyAPI, predictAPI, watchlistAPI } from "../api/api";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Label,
} from "recharts";

import CandlestickChart from "../components/CandlestickChart";
import CompanyNews from "../components/CompanyNews";

const EMPTY_FORM = { equity_name: "", open: "", high: "", low: "", close: "", traded_qty: "" };

/* ── Custom tooltip for the chart ───────────────────────────── */
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="chart-tooltip">
        <p className="chart-tooltip-label">{label}</p>
        {payload.map((entry) => (
          <p key={entry.dataKey} style={{ color: entry.color, margin: "2px 0" }}>
            {entry.name}: <strong>₹{Number(entry.value).toFixed(2)}</strong>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

/* ── Custom dot renderer for the predicted point ─────────────── */
const PredictedDot = (props) => {
  const { cx, cy, value, direction } = props;
  if (value == null) return null;
  const color = direction === "UP" ? "#059669" : "#dc2626";
  return (
    <g>
      <circle cx={cx} cy={cy} r={8} fill={color} stroke="#ffffff" strokeWidth={2} />
      <circle cx={cx} cy={cy} r={14} fill={color} fillOpacity={0.2} />
    </g>
  );
};

export default function Predict() {
  const [companies, setCompanies] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [result, setResult] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [historicalRows, setHistoricalRows] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [chartType, setChartType] = useState("line");
  const [watchlistStatus, setWatchlistStatus] = useState(""); // Track button status
  const [isInWatchlist, setIsInWatchlist] = useState(false); // track if already in watchlist

  // Portfolio Modal State
  const [showPortfolioModal, setShowPortfolioModal] = useState(false);
  const [sharesToBuy, setSharesToBuy] = useState(0);
  const [buyPrice, setBuyPrice] = useState(0.0);

  // Sector filter state
  const [selectedSector, setSelectedSector] = useState("all");

  useEffect(() => {
    companyAPI
      .list()
      .then((res) => setCompanies(res.data.companies))
      .catch(() => setError("Could not load company list."));
  }, []);

  const handleSectorChange = (e) => {
    setSelectedSector(e.target.value);
    setForm(EMPTY_FORM);
    setResult(null);
    setChartData([]);
    setHistoricalRows([]);
  };

  const handleLoadCompanyData = async (selectedEquity) => {
    if (!selectedEquity) return;

    setForm((prev) => ({
      ...EMPTY_FORM,
      equity_name: selectedEquity,
    }));
    setResult(null);
    setChartData([]);
    setHistoricalRows([]);
    setError("");
    setWatchlistStatus("");
    setIsInWatchlist(false);
    setLoading(true);

    try {
      // Run all three fetches IN PARALLEL for speed
      const [historyRes, liveRes, wlRes] = await Promise.all([
        predictAPI.historyChart(selectedEquity),
        predictAPI.latestLive(selectedEquity),
        watchlistAPI.list().catch(() => ({ data: { watchlist: [] } })),
      ]);

      // Check watchlist membership
      const wl = wlRes.data.watchlist || [];
      const inWL = wl.some((w) => w.equity_name === selectedEquity);
      setIsInWatchlist(inWL);

      // If already in watchlist, pre-fill shares/buy price for modal
      const existingWLItem = wl.find((w) => w.equity_name === selectedEquity);
      if (existingWLItem) {
        setSharesToBuy(existingWLItem.shares || 0);
        setBuyPrice(parseFloat(existingWLItem.buy_price) || 0);
      }

      const historyRows = (historyRes.data.historical_data || []).slice(-10);
      setHistoricalRows(historyRows);

      const chartSeries = historyRows.map((d) => ({
        date: d.date,
        open: d.open != null ? parseFloat(d.open) : null,
        high: d.high != null ? parseFloat(d.high) : null,
        low: d.low != null ? parseFloat(d.low) : null,
        close: d.close != null ? parseFloat(d.close) : null,
        predicted: null,
      }));
      setChartData(chartSeries);

      const liveData = liveRes.data.live_data;
      if (liveData && liveData.close) {
        const closeVal = parseFloat(liveData.close);
        setForm({
          equity_name: selectedEquity,
          open: liveData.open.toString(),
          high: liveData.high.toString(),
          low: liveData.low.toString(),
          close: closeVal.toString(),
          traded_qty: liveData.traded_qty.toString(),
        });
        // Default buy price to live close only if not already in watchlist
        if (!existingWLItem) {
          setBuyPrice(closeVal);
        }
      } else {
        setError("Could not load latest live market data.");
      }
    } catch (historyErr) {
      console.error("Failed to fetch data", historyErr);
      setError("Could not load live/historical data for the selected company.");
    } finally {
      setLoading(false);
    }
  };




  useEffect(() => {
    if (!result && historicalRows.length > 0) {
      let sliceCount = 10;
      if (form.close && !isNaN(parseFloat(form.close))) {
        sliceCount = 9;
      }
      const slicedHistory = historicalRows.slice(0, sliceCount);
      const chartSeries = slicedHistory.map((d) => ({
        date: d.date,
        open: d.open != null ? parseFloat(d.open) : null,
        high: d.high != null ? parseFloat(d.high) : null,
        low: d.low != null ? parseFloat(d.low) : null,
        close: d.close != null ? parseFloat(d.close) : null,
        predicted: null,
      }));

      if (form.close && !isNaN(parseFloat(form.close))) {
        const nextRecord = historicalRows[sliceCount];
        const inputDateStr = nextRecord ? nextRecord.date : new Date().toISOString().split("T")[0];
        chartSeries.push({
          date: inputDateStr + " (Input)",
          open: parseFloat(form.open),
          high: parseFloat(form.high),
          low: parseFloat(form.low),
          close: parseFloat(form.close),
          predicted: parseFloat(form.close),
        });
      }
      setChartData(chartSeries);
    }
  }, [form.close, form.open, form.high, form.low, historicalRows, result]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);

    let historyRows = historicalRows;
    if (historyRows.length === 0) {
      try {
        const historyRes = await predictAPI.historyChart(form.equity_name);
        historyRows = (historyRes.data.historical_data || []).slice(-10);
        setHistoricalRows(historyRows);
      } catch (historyErr) {
        console.error("Failed to fetch historical data for chart", historyErr);
      }
    }

    try {
      // Now run prediction
      const res = await predictAPI.predict(form);
      setResult(res.data);

      // Update chart series with prediction (8 historical + 1 input + 1 prediction = 10 total)
      const slicedHistory = historyRows.slice(0, 8);
      const chartSeries = slicedHistory.map((d) => ({
        date: d.date,
        open: d.open != null ? parseFloat(d.open) : null,
        high: d.high != null ? parseFloat(d.high) : null,
        low: d.low != null ? parseFloat(d.low) : null,
        close: d.close != null ? parseFloat(d.close) : null,
        predicted: null,
      }));

      const record9 = historyRows[8];
      const date9 = record9 ? record9.date : new Date().toISOString().split("T")[0];
      chartSeries.push({
        date: date9 + " (Input)",
        open: parseFloat(form.open),
        high: parseFloat(form.high),
        low: parseFloat(form.low),
        close: parseFloat(form.close),
        predicted: parseFloat(form.close),
      });

      const record10 = historyRows[9];
      const date10 = record10 ? record10.date : new Date().toISOString().split("T")[0];
      chartSeries.push({
        date: date10 + " (Pred)",
        open: null,
        high: null,
        low: null,
        close: null,
        predicted: res.data.predicted_price,
      });

      setChartData(chartSeries);
    } catch (err) {
      setError(err.response?.data?.error || "Prediction failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const direction = result?.direction;
  const predColor = direction === "UP" ? "#059669" : "#dc2626";
  const predBg = direction === "UP" ? "rgba(5,150,105,0.06)" : "rgba(220,38,38,0.06)";

  const getBarChartData = () => {
    let sliceCount = 10;
    if (result) {
      sliceCount = 8;
    } else if (form.close && !isNaN(parseFloat(form.close))) {
      sliceCount = 9;
    }
    
    const barData = [
      ...historicalRows.slice(0, sliceCount).map((d) => ({
        name: d.date,
        value: d.close != null ? parseFloat(d.close) : 0,
        isPrediction: false,
      })),
    ];
    
    if (result) {
      const record9 = historicalRows[8];
      const date9 = record9 ? record9.date : "";
      barData.push({
        name: date9 + " (Input)",
        value: parseFloat(form.close),
        isPrediction: false,
      });
      const record10 = historicalRows[9];
      const date10 = record10 ? record10.date : "";
      barData.push({
        name: date10 + " (Pred)",
        value: result.predicted_price,
        isPrediction: true,
      });
    } else if (form.close && !isNaN(parseFloat(form.close))) {
      const record10 = historicalRows[9];
      const date10 = record10 ? record10.date : "";
      barData.push({
        name: date10 + " (Input)",
        value: parseFloat(form.close),
        isPrediction: false,
      });
    }
    return barData;
  };

  const barChartData = getBarChartData();

  const confidenceDistribution = result
    ? [
        { name: "Confidence", value: result.probability },
        { name: "Uncertainty", value: Math.max(0, 100 - result.probability) },
      ]
    : [
        { name: "Confidence", value: 0 },
        { name: "Uncertainty", value: 100 },
      ];

  const calculateAverages = () => {
    if (!historicalRows || historicalRows.length === 0) return null;
    let totalClose = 0, totalHigh = 0, totalLow = 0, totalQty = 0;
    let count = historicalRows.length;
    historicalRows.forEach((row) => {
      totalClose += parseFloat(row.close || 0);
      totalHigh += parseFloat(row.high || 0);
      totalLow += parseFloat(row.low || 0);
      totalQty += parseFloat(row.tradedQty || 0);
    });
    return {
      avgClose: (totalClose / count).toFixed(2),
      avgHigh: (totalHigh / count).toFixed(2),
      avgLow: (totalLow / count).toFixed(2),
      avgQty: Math.round(totalQty / count).toLocaleString(),
    };
  };

  const filteredCompanies = selectedSector === "all"
    ? companies
    : companies.filter((c) => c.sector === selectedSector);

  const averages = calculateAverages();



  return (
    <div className="page predict-page">
      <h2 className="animate-slide-up">Predict Next-Day Closing Price</h2>

      <form className="predict-form animate-slide-up stagger-1" onSubmit={handleSubmit}>
        <div style={{ padding: "24px", border: "1px solid var(--glass-border)", borderRadius: "var(--radius-sm)", marginBottom: "32px", background: "rgba(15, 23, 42, 0.3)" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
            {/* Sector Filter */}
            <div>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: "700" }}>Sector Filter</label>
              <div style={{ display: "flex", gap: "12px", alignItems: "center", width: "100%" }}>
                <span style={{ fontSize: "1.6rem", flexShrink: 0 }} title="Sector Selector">📁</span>
                <select
                  name="sector"
                  value={selectedSector}
                  onChange={handleSectorChange}
                  style={{ width: "100%", height: "48px" }}
                >
                  <option value="all">All Sectors</option>
                  <option value="auto mobiles & auto components">Auto Mobiles & Components</option>
                  <option value="banking & finance">Banking & Finance</option>
                  <option value="cement & materials">Cement & Materials</option>
                  <option value="consumer goods">Consumer Goods</option>
                  <option value="materials">Materials</option>
                </select>
              </div>
            </div>

            {/* Company Dropdown */}
            <div>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: "700" }}>Company</label>
              <div style={{ display: "flex", flexDirection: "column", gap: "16px", width: "100%" }}>
                <div style={{ display: "flex", gap: "12px", alignItems: "center", width: "100%" }}>
                  <span style={{ fontSize: "1.6rem", flexShrink: 0 }} title="Company Selector">🏢</span>
                  <select
                    name="equity_name"
                    value={form.equity_name}
                    onChange={(e) => {
                      const newEquity = e.target.value;
                      setForm({ ...form, equity_name: newEquity });
                      handleLoadCompanyData(newEquity);
                    }}
                    required
                    style={{ width: "100%", height: "48px" }}
                  >
                    <option value="">Select a company…</option>
                    {filteredCompanies.map((c) => (
                      <option key={c.id} value={c.equity_name}>
                        {c.company_name} ({c.equity_name})
                      </option>
                    ))}
                  </select>
                </div>
                {form.equity_name && (
                  <button
                    type="button"
                    className={isInWatchlist ? "btn-secondary" : "btn-primary"}
                    onClick={() => {
                      if (isInWatchlist) {
                        // Remove directly with confirmation inline
                        if (window.confirm(`Remove ${form.equity_name} from your watchlist?`)) {
                          watchlistAPI.remove(form.equity_name)
                            .then(() => {
                              setIsInWatchlist(false);
                              setWatchlistStatus("Removed!");
                              setTimeout(() => setWatchlistStatus(""), 3000);
                            })
                            .catch(() => setWatchlistStatus("Error"));
                        }
                      } else {
                        setSharesToBuy(0);
                        setBuyPrice(form.close || 0);
                        setShowPortfolioModal(true);
                      }
                    }}
                    style={{
                      width: "100%",
                      height: "48px",
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      gap: "8px",
                      fontSize: "1rem"
                    }}
                  >
                    {isInWatchlist
                      ? (watchlistStatus || "🗑 Remove from Watchlist")
                      : (watchlistStatus ? `⭐ ${watchlistStatus}` : "⭐ Add to Watchlist")
                    }
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Portfolio Simulator Modal */}
        {showPortfolioModal && (() => {
          const liveClose = parseFloat(form.close) || 0;
          const sharesNum = parseFloat(sharesToBuy) || 0;
          const buyPriceNum = parseFloat(buyPrice) || 0;
          const pnlPreview = sharesNum > 0 && buyPriceNum > 0 && liveClose > 0
            ? ((liveClose - buyPriceNum) * sharesNum)
            : null;
          const pnlColor = pnlPreview === null ? "var(--text-muted)" : pnlPreview >= 0 ? "#10b981" : "#ef4444";
          const investedValue = sharesNum * buyPriceNum;
          const currentValue = sharesNum * liveClose;

          return (
            <div style={{
              position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
              background: "rgba(0,0,0,0.7)", backdropFilter: "blur(6px)",
              display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000
            }}>
              <div style={{
                background: "var(--bg-secondary)", padding: "28px", borderRadius: "16px",
                width: "440px", border: "1px solid var(--glass-border)",
                display: "flex", flexDirection: "column", gap: "18px",
                boxShadow: "0 20px 60px rgba(0,0,0,0.5)"
              }}>
                {/* Header */}
                <div>
                  <h3 style={{ margin: "0 0 4px 0", color: "var(--text)", fontSize: "1.2rem" }}>
                    ⭐ Add to Watchlist
                  </h3>
                  <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--text-muted)" }}>
                    {form.equity_name} — Live Price: <strong style={{ color: "var(--text)" }}>
                      ₹{liveClose.toFixed(2)}
                    </strong>
                  </p>
                </div>

                {/* Shares input */}
                <div>
                  <label style={{ display: "block", marginBottom: "6px", fontWeight: 600, fontSize: "0.9rem" }}>
                    Number of Shares Owned
                  </label>
                  <input
                    type="number" min="0" step="1"
                    value={sharesToBuy}
                    onChange={e => setSharesToBuy(e.target.value)}
                    placeholder="0 = just watch (no P&L tracking)"
                    style={{
                      width: "100%", padding: "10px 12px", boxSizing: "border-box",
                      background: "var(--bg-primary)", color: "var(--text)",
                      border: "1px solid var(--glass-border)", borderRadius: "8px",
                      fontSize: "0.95rem"
                    }}
                  />
                </div>

                {/* Buy price input */}
                <div>
                  <label style={{ display: "block", marginBottom: "6px", fontWeight: 600, fontSize: "0.9rem" }}>
                    Average Buy Price (₹)
                  </label>
                  <input
                    type="number" step="0.01" min="0"
                    value={buyPrice}
                    onChange={e => setBuyPrice(e.target.value)}
                    placeholder="e.g. 1500.00"
                    style={{
                      width: "100%", padding: "10px 12px", boxSizing: "border-box",
                      background: "var(--bg-primary)", color: "var(--text)",
                      border: "1px solid var(--glass-border)", borderRadius: "8px",
                      fontSize: "0.95rem"
                    }}
                  />
                </div>

                {/* Live P&L Preview */}
                {sharesNum > 0 && buyPriceNum > 0 && (
                  <div style={{
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid var(--glass-border)",
                    borderRadius: "10px", padding: "14px",
                    display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px"
                  }}>
                    <div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: "3px" }}>Invested Value</div>
                      <div style={{ fontWeight: 700, fontSize: "1rem", color: "var(--text)" }}>
                        ₹{investedValue.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: "3px" }}>Current Value</div>
                      <div style={{ fontWeight: 700, fontSize: "1rem", color: "var(--text)" }}>
                        ₹{currentValue.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                    </div>
                    <div style={{ gridColumn: "1 / -1" }}>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: "3px" }}>Unrealised P&amp;L</div>
                      <div style={{ fontWeight: 700, fontSize: "1.2rem", color: pnlColor }}>
                        {pnlPreview >= 0 ? "+" : ""}₹{pnlPreview.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        <span style={{ fontSize: "0.8rem", marginLeft: "8px", opacity: 0.8 }}>
                          ({buyPriceNum > 0 ? ((pnlPreview / investedValue) * 100).toFixed(2) : 0}%)
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div style={{ display: "flex", gap: "12px" }}>
                  <button type="button" onClick={() => setShowPortfolioModal(false)} className="btn-secondary" style={{ flex: 1 }}>
                    Cancel
                  </button>
                  <button type="button" onClick={async () => {
                    try {
                      await watchlistAPI.add(form.equity_name, Number(sharesToBuy), Number(buyPrice));
                      setWatchlistStatus("Added! ✓");
                      setIsInWatchlist(true);
                      setShowPortfolioModal(false);
                      setTimeout(() => setWatchlistStatus(""), 3000);
                    } catch (err) {
                      setWatchlistStatus("Error ✗");
                      setShowPortfolioModal(false);
                    }
                  }} className="btn-primary" style={{ flex: 1 }}>
                    ⭐ Save to Watchlist
                  </button>
                </div>
              </div>
            </div>
          );
        })()}



        <div className="form-grid">
          <div>
            <label>Live Open Price (₹)</label>
            <input type="number" step="0.01" name="open" value={form.open} readOnly required />
          </div>
          <div>
            <label>Live High Price (₹)</label>
            <input type="number" step="0.01" name="high" value={form.high} readOnly required />
          </div>
          <div>
            <label>Live Low Price (₹)</label>
            <input type="number" step="0.01" name="low" value={form.low} readOnly required />
          </div>
          <div>
            <label>Live Close Price (₹)</label>
            <input type="number" step="0.01" name="close" value={form.close} readOnly required />
          </div>
          <div>
            <label>Live Traded Quantity</label>
            <input type="number" name="traded_qty" value={form.traded_qty} readOnly required />
          </div>
        </div>

        <button type="submit" className="btn-secondary" disabled={loading} style={{ marginTop: "20px", width: "100%" }}>
          {loading ? "Predicting…" : "Predict"}
        </button>
      </form>

      {error && <div className="alert-error animate-slide-up stagger-1">{error}</div>}

      {result && (
        <div className="prediction-results-container animate-slide-up stagger-2">

          {/* ── Result card ─────────────────────────────── */}
          <div
            className={`result-card ${direction === "UP" ? "result-up" : "result-down"}`}
            style={{ borderLeftColor: predColor }}
          >
            <h3>{result.equity_name}</h3>
            <p className="result-price" style={{ color: predColor }}>₹{result.predicted_price}</p>
            <p className="result-direction" style={{ color: predColor }}>
              {direction === "UP" ? "▲ Expected to rise" : "▼ Expected to fall"} ({result.change_pct}%)
            </p>
            <p className="result-note">Last close was ₹{result.last_close}</p>

            {result.probability != null && (
              <div className="probability-section">
                <p className="probability-label">
                  Prediction Confidence: <strong>{result.probability}%</strong>
                </p>
                <div className="probability-bar-track">
                  <div
                    className={`probability-bar-fill ${direction === "UP" ? "prob-up" : "prob-down"}`}
                    style={{ width: `${result.probability}%` }}
                  />
                </div>
                <p className="probability-hint">
                  Based on RSI momentum, MA-20 position &amp; model R² score
                </p>
              </div>
            )}
          </div>

          {/* ── Past data table ──────────────────────────── */}
          {historicalRows.length > 0 && (
            <div className="past-data-section">
              <h3 className="section-title">
                📊 Past Close Price Data — <span style={{ color: "var(--primary)" }}>{result.equity_name}</span>
              </h3>
              <div className="table-scroll">
                <table className="data-table hist-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Date</th>
                      <th>Close Price (₹)</th>
                      <th>Change</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historicalRows.map((row, idx) => {
                      const prev = historicalRows[idx - 1];
                      const change = prev ? parseFloat(row.close) - parseFloat(prev.close) : null;
                      const isUp = change > 0;
                      return (
                        <tr key={idx}>
                          <td className="row-num">{idx + 1}</td>
                          <td>{row.date}</td>
                          <td className="close-val">₹{parseFloat(row.close).toFixed(2)}</td>
                          <td>
                            {change != null ? (
                              <span className={isUp ? "text-up" : "text-down"}>
                                {isUp ? "▲" : "▼"} ₹{Math.abs(change).toFixed(2)}
                              </span>
                            ) : (
                              <span className="text-muted">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                    {/* Input row */}
                    <tr className="input-row">
                      <td className="row-num">—</td>
                      <td>Today (Input)</td>
                      <td className="close-val input-close">₹{parseFloat(form.close).toFixed(2)}</td>
                      <td>
                        {(() => {
                          const last = historicalRows[historicalRows.length - 1];
                          const ch = last ? parseFloat(form.close) - parseFloat(last.close) : null;
                          if (ch == null) return <span className="text-muted">—</span>;
                          return (
                            <span className={ch >= 0 ? "text-up" : "text-down"}>
                              {ch >= 0 ? "▲" : "▼"} ₹{Math.abs(ch).toFixed(2)}
                            </span>
                          );
                        })()}
                      </td>
                    </tr>
                    {/* Predicted row */}
                    <tr className="predicted-row" style={{ background: predBg }}>
                      <td className="row-num">—</td>
                      <td>Next Day (Predicted)</td>
                      <td className="close-val" style={{ color: predColor, fontWeight: 700 }}>
                        ₹{result.predicted_price}
                      </td>
                      <td>
                        <span style={{ color: predColor, fontWeight: 600 }}>
                          {direction === "UP" ? "▲" : "▼"} {result.change_pct}%
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Line Chart, Bar Chart & Pie Chart ───────────────────────────────── */}
      {chartData.length > 0 && (
            <div className="chart-section animate-slide-up stagger-3">
              <h3 className="section-title">
                📊 Historical Statistics &amp; Predictions
              </h3>
              
              {averages && (
                <div className="stat-grid" style={{ marginBottom: "30px", marginTop: "15px" }}>
                  <div className="stat-card">
                    <span className="stat-value">₹{averages.avgClose}</span>
                    <span className="stat-label">Avg Close Price</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">₹{averages.avgHigh}</span>
                    <span className="stat-label">Avg Max Price</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">₹{averages.avgLow}</span>
                    <span className="stat-label">Avg Low Price</span>
                  </div>
                  <div className="stat-card">
                    <span className="stat-value">{averages.avgQty}</span>
                    <span className="stat-label">Avg Traded Qty</span>
                  </div>
                </div>
              )}

              <div className="chart-header-actions" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "15px", marginBottom: "15px" }}>
                <div className="chart-legend-info">
                  <span className="legend-dot" style={{ background: "#2563eb" }} /> Historical Close
                  &nbsp;&nbsp;
                  <span className="legend-dot" style={{ background: "#7c3aed" }} /> Today's Close (Input)
                  {result && (
                    <>
                      &nbsp;&nbsp;
                      <span className="legend-dot" style={{ background: predColor }} />
                      Predicted Close
                    </>
                  )}
                </div>

                <div style={{ display: "flex", gap: "8px", background: "rgba(15, 23, 42, 0.4)", borderRadius: "8px", padding: "4px" }}>
                  <button 
                    type="button"
                    onClick={() => setChartType("line")}
                    style={{ 
                      background: chartType === "line" ? "rgba(255,255,255,0.1)" : "transparent",
                      border: "none", color: chartType === "line" ? "white" : "var(--text-muted)",
                      padding: "4px 12px", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem", fontWeight: "600"
                    }}>Line</button>
                  <button 
                    type="button"
                    onClick={() => setChartType("candle")}
                    style={{ 
                      background: chartType === "candle" ? "rgba(255,255,255,0.1)" : "transparent",
                      border: "none", color: chartType === "candle" ? "white" : "var(--text-muted)",
                      padding: "4px 12px", borderRadius: "6px", cursor: "pointer", fontSize: "0.85rem", fontWeight: "600"
                    }}>Candle</button>
                </div>
              </div>

              {/* Chart container */}
              <div style={{ width: "100%", height: 360, marginBottom: 30 }}>
                {chartType === "candle" ? (
                  <CandlestickChart data={chartData} />
                ) : (
                  <ResponsiveContainer>
                    <LineChart data={chartData} margin={{ top: 20, right: 20, left: 25, bottom: 50 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis
                        dataKey="date"
                        tick={{ fill: "#94a3b8", fontSize: 10 }}
                        angle={-25}
                        textAnchor="end"
                        interval={0}
                        height={50}
                      >
                        <Label value="Timeline (Date)" offset={0} position="insideBottom" fill="#cbd5e1" style={{ fontSize: '11px', fontWeight: 600, textAnchor: 'middle' }} />
                      </XAxis>
                      <YAxis
                        domain={["auto", "auto"]}
                        tick={{ fill: "#94a3b8", fontSize: 11 }}
                        tickFormatter={(v) => `₹${v}`}
                        width={60}
                      >
                        <Label value="Price (₹)" angle={-90} position="insideLeft" offset={0} fill="#cbd5e1" style={{ fontSize: '11px', fontWeight: 600, textAnchor: 'middle' }} />
                      </YAxis>
                      <Tooltip content={<CustomTooltip />} />
  
                      <Line
                        type="monotone"
                        dataKey="close"
                        name="Historical Close"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        dot={(props) => {
                          const { cx, cy, payload } = props;
                          if (payload.date.includes("Input")) {
                            return <circle key={payload.date} cx={cx} cy={cy} r={5} fill="#a855f7" stroke="#ffffff" strokeWidth={1.5} />;
                          }
                          return <circle key={payload.date} cx={cx} cy={cy} r={4} fill="#3b82f6" stroke="#ffffff" strokeWidth={1} />;
                        }}
                        activeDot={{ r: 6 }}
                        label={{ fill: "#cbd5e1", fontSize: 9, position: "top", formatter: (v) => v ? `₹${Number(v).toFixed(2)}` : "" }}
                      />
                      {result && (
                        <Line
                          type="monotone"
                          dataKey="predicted"
                          name="Predicted Close"
                          stroke={predColor}
                          strokeWidth={3}
                          strokeDasharray="6 4"
                          dot={(props) => (
                            <PredictedDot {...props} direction={direction} />
                          )}
                          activeDot={{ r: 6 }}
                          label={{ fill: predColor, fontSize: 10, fontWeight: "bold", position: "top", formatter: (v) => v ? `₹${Number(v).toFixed(2)}` : "" }}
                        />
                      )}
  
                      {/* Reference line at last close */}
                      {(result || form.close) && (
                        <ReferenceLine
                          y={result ? result.last_close : form.close}
                          stroke="#94a3b8"
                          strokeDasharray="4 4"
                          label={{ value: `Last close ₹${result ? result.last_close : form.close}`, fill: "#94a3b8", fontSize: 11, position: "insideTopRight" }}
                        />
                      )}
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>

              <div className="chart-grid" style={!result ? { gridTemplateColumns: "1fr" } : {}}>
                <div className="chart-card">
                  <h4>📊 Historical &amp; Predicted Close Prices</h4>
                  <div style={{ width: "100%", height: 280 }}>
                    <ResponsiveContainer>
                      <BarChart data={barChartData} margin={{ top: 20, right: 16, left: 15, bottom: 45 }}>
                        <XAxis
                          dataKey="name"
                          tick={{ fill: "#94a3b8", fontSize: 9 }}
                          angle={-25}
                          textAnchor="end"
                          axisLine={false}
                          tickLine={false}
                          interval={0}
                          height={45}
                        >
                          <Label value="Date" offset={0} position="insideBottom" fill="#cbd5e1" style={{ fontSize: '10px', fontWeight: 600, textAnchor: 'middle' }} />
                        </XAxis>
                        <YAxis 
                          domain={["auto", "auto"]} 
                          tick={{ fill: "#94a3b8", fontSize: 11 }} 
                          tickFormatter={(v) => `₹${v}`}
                          width={55}
                        >
                          <Label value="Price (₹)" angle={-90} position="insideLeft" offset={0} fill="#cbd5e1" style={{ fontSize: '10px', fontWeight: 600, textAnchor: 'middle' }} />
                        </YAxis>
                        <Tooltip formatter={(value) => `₹${Number(value).toFixed(2)}`} />
                        <Bar
                          dataKey="value"
                          radius={[4, 4, 0, 0]}
                          label={{ fill: "#cbd5e1", fontSize: 9, position: "top", formatter: (v) => v ? `₹${Number(v).toFixed(2)}` : "" }}
                        >
                          {barChartData.map((entry, index) => {
                            let fill = "#2563eb";
                            if (entry.isPrediction) {
                              fill = predColor;
                            } else if (entry.name.includes("Input")) {
                              fill = "#7c3aed";
                            }
                            return <Cell key={`cell-${index}`} fill={fill} />;
                          })}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {result && (
                  <div className="chart-card">
                    <h4>🎯 Prediction confidence</h4>
                    <div style={{ width: "100%", height: 280, position: "relative" }}>
                      <ResponsiveContainer>
                        <PieChart>
                          <Pie
                            data={confidenceDistribution}
                            dataKey="value"
                            nameKey="name"
                            innerRadius={60}
                            outerRadius={100}
                            paddingAngle={4}
                            stroke="transparent"
                          >
                            {confidenceDistribution.map((entry, index) => (
                              <Cell
                                key={`cell-${index}`}
                                fill={index === 0 ? predColor : "rgba(148,163,184,0.25)"}
                              />
                            ))}
                          </Pie>
                          <Tooltip formatter={(value) => `${value}%`} />
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="pie-center">
                        <span className="pie-value">{result ? result.probability : 0}%</span>
                        <span className="pie-label">Confidence</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Company News Section */}
              <CompanyNews equityName={form.equity_name} />
              
            </div>
          )}
    </div>
  );
}
