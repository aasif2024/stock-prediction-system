import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Home() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="page home-page">
      <section className="hero">
        <div className="hero-badge">🚀 Powered by ML &amp; NSE Historical Data</div>
        <h1>Predict Tomorrow's<br />Stock Price, Today.</h1>
        <p>
          StockSense combines historical NSE data with machine learning —
          Linear Regression, Random Forest &amp; Gradient Boosting — to forecast
          next-day closing prices. Backend by RSI, MACD &amp; Bollinger Bands.
        </p>
        <div className="hero-actions">
          <Link to={isAuthenticated ? "/predict" : "/register"} className="btn-primary">
            {isAuthenticated ? "⚡ Make a Prediction" : "🚀 Get Started Free"}
          </Link>
          <Link to="/about" className="btn-secondary">Learn More</Link>
        </div>
        <div className="hero-stats">
          <div className="hero-stat"><span className="hero-stat-val">3</span><span>ML Models</span></div>
          <div className="hero-stat-divider" />
          <div className="hero-stat"><span className="hero-stat-val">NSE</span><span>Market Data</span></div>
          <div className="hero-stat-divider" />
          <div className="hero-stat"><span className="hero-stat-val">Real-time</span><span>Predictions</span></div>
        </div>
      </section>

      <section className="feature-grid">
        <div className="feature-card">
          <div className="feature-icon">📊</div>
          <h3>Data-Driven</h3>
          <p>Trained on historical OHLCV data with engineered technical indicators for maximum accuracy.</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">🤖</div>
          <h3>Machine Learning</h3>
          <p>Compares Linear Regression, Random Forest &amp; Gradient Boosting to select the best performer.</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">📈</div>
          <h3>Track History</h3>
          <p>Every prediction is saved with UP/DOWN direction so you can review accuracy over time.</p>
        </div>
      </section>
    </div>
  );
}
