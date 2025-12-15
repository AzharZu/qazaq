import axios from "axios";

// Prefer env backend URL, fallback to /api (proxy)
const API_URL = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");
const TOKEN_KEY = "auth_token";

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

const getToken = () => localStorage.getItem(TOKEN_KEY) || null;

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) {
      logout();
      window.location.href = "/admin/login";
    }
    return Promise.reject(err);
  }
);

async function login(email, password) {
  const { data } = await api.post("/auth/login", { email, password });
  if (data?.token) {
    localStorage.setItem(TOKEN_KEY, data.token);
  }
  return data;
}

function logout() {
  localStorage.removeItem(TOKEN_KEY);
}

function isAuthenticated() {
  return Boolean(getToken());
}

const AuthService = {
  api,
  login,
  logout,
  getToken,
  isAuthenticated,
};

export default AuthService;
export { api, login, logout, getToken, isAuthenticated };
