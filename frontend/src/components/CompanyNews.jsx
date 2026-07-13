import React, { useEffect, useState } from "react";
import { predictAPI } from "../api/api";

const CompanyNews = ({ equityName }) => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!equityName) {
      setNews([]);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError("");

    predictAPI.news(equityName)
      .then((res) => {
        if (isMounted) {
          setNews(res.data.news || []);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.response?.data?.error || "Failed to load news");
          console.error("News fetch error:", err);
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [equityName]);

  if (!equityName) return null;

  return (
    <div className="company-news-section animate-slide-up stagger-4" style={{ marginTop: "40px" }}>
      <h3 className="section-title">📰 Latest {equityName} News</h3>
      
      {loading && <p style={{ color: "var(--text-muted)" }}>Loading news...</p>}
      {error && <p className="alert-error">{error}</p>}
      
      {!loading && !error && news.length === 0 && (
        <p style={{ color: "var(--text-muted)" }}>No recent news found for {equityName}.</p>
      )}

      {!loading && news.length > 0 && (
        <div className="news-grid" style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: "16px",
          marginTop: "16px"
        }}>
          {news.map((article, idx) => (
            <a 
              key={idx} 
              href={article.link} 
              target="_blank" 
              rel="noopener noreferrer"
              className="news-card"
              style={{
                display: "block",
                padding: "16px",
                background: "rgba(15, 23, 42, 0.4)",
                border: "1px solid var(--glass-border)",
                borderRadius: "8px",
                textDecoration: "none",
                transition: "all 0.2s ease"
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = "rgba(255,255,255,0.05)";
                e.currentTarget.style.transform = "translateY(-2px)";
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = "rgba(15, 23, 42, 0.4)";
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              <div style={{ fontSize: "0.8rem", color: "var(--primary)", fontWeight: "700", marginBottom: "8px" }}>
                {article.publisher}
              </div>
              <h4 style={{ color: "var(--text)", margin: "0 0 12px 0", fontSize: "1rem", lineHeight: "1.4" }}>
                {article.title}
              </h4>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                {article.providerPublishTime ? new Date(article.providerPublishTime * 1000).toLocaleString() : ""}
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
};

export default CompanyNews;
