import axios from "axios";

type TokenProvider = () => string | null;
type UnauthorizedHandler = () => void;

let tokenProvider: TokenProvider | null = null;
let unauthorizedHandler: UnauthorizedHandler | null = null;

const resolveApiBase = (): string => {
  const raw = (process.env.NEXT_PUBLIC_API_URL || "").trim();
  const normalized = raw.replace(/\/+$/, "");
  if (!normalized) {
    const message =
      "NEXT_PUBLIC_API_URL is not set. Please define it in student-next/.env.local (e.g. http://localhost:8000) so the frontend can reach the API.";
    // Fail loudly during build/dev to avoid silent fallback to an incorrect host.
    console.error(message);
    throw new Error(message);
  }
  return normalized.endsWith("/api") ? normalized : `${normalized}/api`;
};

const apiBase = resolveApiBase();

export const setTokenProvider = (provider: TokenProvider) => {
  tokenProvider = provider;
};

export const setUnauthorizedHandler = (handler: UnauthorizedHandler) => {
  unauthorizedHandler = handler;
};

export const client = axios.create({
  baseURL: apiBase,
  withCredentials: true,
});

client.interceptors.request.use((config) => {
  const token = tokenProvider?.();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error?.response?.status;
    const url = error?.config?.url || "";
    // Для открытых эндпоинтов (placement/level-test) не разлогиниваем пользователя
    const isOpenTestEndpoint = url.includes("/placement") || url.includes("/level-test");
    if (status === 401 && !isOpenTestEndpoint) {
      unauthorizedHandler?.();
    }
    return Promise.reject(error);
  }
);

export default client;
