import axios from "axios";

const RAW_API_URL = import.meta.env.VITE_API_URL || "";
const API_URL = (RAW_API_URL || "http://127.0.0.1:8000/api").replace(/\/$/, "");

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
