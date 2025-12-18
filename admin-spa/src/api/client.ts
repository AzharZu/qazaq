import axios from "axios";

// Always use /api for proxy through nginx
const API_URL = "/api";

export const api = axios.create({
  baseURL: `${API_URL}/`,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.data?.detail) {
      const error = new Error(err.response.data.detail);
      throw error;
    }
    throw err;
  }
);
