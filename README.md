# StockSense — NSE Stock Market Price Prediction System

A full-stack application that analyzes historical NSE stock data, trains machine learning models to predict next-day closing prices, and serves predictions through a Flask REST API to a React frontend. The application features a highly modern, professional, premium UI with real-time Yahoo Finance market data integration.

---

## 🌟 Premium Features

- **Real-Time Data Integration**: Fully automated OHLCV data fetching using Yahoo Finance (`yfinance`). No manual data entry required!
- **Live Ticker Tape**: A professional scrolling ticker tape on the Dashboard displaying live stock prices and daily % changes for all supported companies.
- **Interactive Candlestick Charts**: Beautiful, responsive ApexCharts on the Predict page that allow users to toggle between line charts and professional candlestick charts.
- **Portfolio & Watchlist**: Users can easily save stocks to their Watchlist and track real-time portfolio performance straight from their Dashboard.
- **AI-Powered Predictions**: Uses Scikit-learn (Linear Regression, Random Forest, Gradient Boosting) to forecast the next day's price and direction (UP/DOWN).
- **Live Company News Feed**: Instantly pulls the latest news articles for the selected company, allowing you to gauge market sentiment before predicting.
- **Glassmorphism UI**: A dark-mode native interface featuring smooth animations, dynamic color-coded badges, and a sleek modern aesthetic.

---

## 1. Architecture

```
Excel dataset ──▶ train_model.py ──▶ model.pkl / scaler.pkl / company_encoder.pkl
                                              │
                                              ▼
React (frontend/) ──HTTP/JSON──▶ Flask API (backend/) ──▶ SQLite / MySQL
                                              │
                                              └──▶ yfinance (Live Data & News)
```

- **Frontend**: React 18 + React Router + ApexCharts. Talks to the backend via `axios` (`frontend/src/api/api.js`), stores JWT in `localStorage`.
- **Backend**: Flask + `yfinance`. Organized into `routes/` (HTTP endpoints), `models/` (SQL data access), `utils/` (auth + ML helpers), `database/`.
- **ML**: Scikit-learn Linear Regression / Random Forest / Gradient Boosting, trained in `machine_learning/train_model.py`.
- **Database**: SQLite (default fallback) or MySQL. Manages `users`, `companies`, `prediction_history`, and `watchlist` tables.

---

## 2. Folder structure

```
stock-prediction-system/
├── database/
│   └── schema.sql              # MySQL CREATE TABLE statements
├── machine_learning/
│   ├── train_model.py          # cleans data, engineers features, trains & saves model
│   ├── data/sample_dataset.xlsx
│   └── saved_model/            
├── backend/
│   ├── app.py                  # Flask app factory / entry point
│   ├── config.py               # env-driven settings
│   ├── seed_companies.py       # populates the companies table
│   ├── requirements.txt
│   ├── .env.example
│   ├── database/db.py          # SQLite/MySQL connection wrapper
│   ├── models/                 # user_model, company_model, prediction_model, watchlist_model
│   ├── routes/                 # auth_routes, company_routes, predict_routes, history_routes, watchlist_routes
│   ├── utils/                  # auth_utils, ml_utils (yfinance logic)
│   └── ml_model/               # trained model artifacts
├── frontend/
│   ├── package.json
│   └── src/
│       ├── api/api.js          # axios client
│       ├── components/         # Navbar, TickerTape, CandlestickChart, CompanyNews
│       ├── pages/              # Home, Login, Register, Dashboard, Predict, History
│       └── styles/App.css
└── README.md
```

---

## 3. Setup instructions

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- (Optional) MySQL 8+ (will default to SQLite if MySQL fails)

### Step 1 — Clone and install Python dependencies
```bash
cd stock-prediction-system
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

### Step 2 — Train the model (Optional if already trained)
```bash
cd machine_learning
python train_model.py --data data/sample_dataset.xlsx
# Writes artifacts to machine_learning/saved_model/ AND backend/ml_model/.
cd ..
```

### Step 3 — Configure and start the backend
```bash
cd backend
cp .env.example .env

python seed_companies.py     # Populates the companies table
python app.py                # Runs on http://localhost:5000 (auto-initializes SQLite)
```

### Step 4 — Start the frontend
```bash
cd ../frontend
npm install
npm start                    # runs on http://localhost:3000, proxies /api to :5000
```

### Step 5 — Use the app
1. Open `http://localhost:3000`
2. Register an account and login.
3. The **Dashboard** will load your Live Ticker Tape and Watchlist.
4. Go to **Predict**, select a company, and the platform will automatically fetch today's live prices and latest news.
5. Click **Predict Price** to forecast tomorrow's movement.

---

## 4. API reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | No | Register user |
| POST | `/api/auth/login` | No | Login user |
| GET | `/api/companies` | Yes | Get supported companies list |
| GET | `/api/predict/latest/<equity_name>` | Yes | Fetch live OHLC data from Yahoo Finance |
| GET | `/api/predict/news/<equity_name>` | Yes | Fetch latest news articles from Yahoo Finance |
| GET | `/api/predict/latest-all` | Yes | Fetch bulk live market data (used for Ticker/Watchlist) |
| POST | `/api/predict` | Yes | Get AI prediction |
| GET | `/api/history` | Yes | View user's prediction history |
| GET/POST/DEL | `/api/watchlist` | Yes | Manage user's saved stocks |

---

## 5. Known limitations / what to improve for production
- **Single-day prediction approximation**: The ML model was trained on historical rolling features, but live prediction is currently approximating rolling indicators (RSI, MA) from a single day's live API pull.
- **Production Server**: Use Waitress/Gunicorn for Flask instead of the default dev server. Use Vercel/Netlify for the React frontend.
- **JWT Revocation**: Logout is client-side only. Add a Redis blocklist for true token revocation.
