import axios from "axios";

// CRA proxies /api to http://localhost:5000 in development (see package.json).
// In production, set REACT_APP_API_BASE_URL to your deployed backend URL.
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach the JWT (if present) to every outgoing request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If the token expires/is invalid, clear it and bounce to login.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (payload) => api.post("/api/auth/register", payload),
  login: (payload) => api.post("/api/auth/login", payload),
  logout: () => api.post("/api/auth/logout"),
  forgotPassword: (payload) => api.post("/api/auth/forgot-password", payload),
  resetPassword: (payload) => api.post("/api/auth/reset-password", payload),
};

export const companyAPI = {
  list: () => api.get("/api/companies"),
};

export const predictAPI = {
  predict: (payload) => api.post("/api/predict", payload),
  historyChart: (equityName) => api.get(`/api/predict/history/${equityName}`),
  latestLive: (equityName) => api.get(`/api/predict/latest/${equityName}`),
  latestAll: () => api.get("/api/predict/latest-all"),
  news: (equityName) => api.get(`/api/predict/news/${equityName}`),
};

export const historyAPI = {
  list: () => api.get("/api/history"),
  delete: (id) => api.delete(`/api/history/${id}`),
};

export const watchlistAPI = {
  list: () => api.get("/api/watchlist/"),
  add: (equityName, shares = 0, buyPrice = 0.0) => api.post("/api/watchlist/", { 
    equity_name: equityName, 
    shares: shares, 
    buy_price: buyPrice 
  }),
  remove: (equityName) => api.delete(`/api/watchlist/${equityName}`),
};

export default api;
