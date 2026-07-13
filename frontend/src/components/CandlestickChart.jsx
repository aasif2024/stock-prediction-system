import React from "react";
import Chart from "react-apexcharts";

const CandlestickChart = ({ data }) => {
  // data should be an array of objects: { date, open, high, low, close }
  const formattedData = data
    .filter((d) => d.open != null && d.high != null && d.low != null && d.close != null)
    .map((d) => ({
      x: new Date(d.date),
      y: [d.open, d.high, d.low, d.close],
    }));

  const options = {
    chart: {
      type: "candlestick",
      height: 350,
      background: "transparent",
      toolbar: {
        show: false,
      },
      animations: {
        enabled: true,
      }
    },
    theme: {
      mode: 'dark'
    },
    plotOptions: {
      candlestick: {
        colors: {
          upward: "#10b981", // Green
          downward: "#ef4444", // Red
        },
      },
    },
    xaxis: {
      type: "datetime",
      labels: {
        style: {
          colors: "#94a3b8",
        },
      },
      axisBorder: {
        color: "rgba(255,255,255,0.1)",
      },
      axisTicks: {
        color: "rgba(255,255,255,0.1)",
      }
    },
    yaxis: {
      tooltip: {
        enabled: true,
      },
      labels: {
        style: {
          colors: "#94a3b8",
        },
        formatter: (value) => {
          return "₹" + value.toFixed(2);
        }
      },
    },
    grid: {
      borderColor: "rgba(255,255,255,0.1)",
      strokeDashArray: 3,
    },
    tooltip: {
      theme: "dark",
      style: {
        fontSize: '14px',
        fontFamily: 'Inter, sans-serif'
      }
    }
  };

  const series = [
    {
      name: "Price",
      data: formattedData,
    },
  ];

  return (
    <div className="candlestick-chart-wrapper" style={{ width: "100%", height: "100%" }}>
      <Chart options={options} series={series} type="candlestick" height={350} />
    </div>
  );
};

export default CandlestickChart;
