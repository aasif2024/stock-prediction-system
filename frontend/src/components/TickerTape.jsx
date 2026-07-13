import React, { useEffect, useState } from "react";
import { predictAPI } from "../api/api";

const TickerTape = () => {
  const [tickerData, setTickerData] = useState([]);

  useEffect(() => {
    predictAPI
      .latestAll()
      .then((res) => {
        if (res.data && res.data.live_data) {
          // Double the data to create a seamless infinite marquee effect
          setTickerData([...res.data.live_data, ...res.data.live_data]);
        }
      })
      .catch((err) => {
        console.error("Failed to load ticker data", err);
      });
  }, []);

  if (tickerData.length === 0) return null;

  return (
    <div className="ticker-wrap animate-slide-up">
      <div className="ticker">
        {tickerData.map((item, index) => {
          const isUp = item.change_val >= 0;
          return (
            <div className="ticker-item" key={index}>
              <span className="ticker-symbol">{item.equity_name}</span>
              <span className="ticker-price">₹{item.close.toFixed(2)}</span>
              <span className={`ticker-change ${isUp ? "up" : "down"}`}>
                {isUp ? "▲" : "▼"} {Math.abs(item.change_val).toFixed(2)} (
                {Math.abs(item.change_pct).toFixed(2)}%)
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TickerTape;
