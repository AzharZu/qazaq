import { getToken } from "./auth";
import client, { setTokenProvider, setUnauthorizedHandler } from "./api/client";

// Default token/401 handling for legacy imports; can be overridden by stores
setTokenProvider(() => (typeof window !== "undefined" ? getToken() : null));
setUnauthorizedHandler(() => {
  if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
    localStorage.removeItem("token");
    window.location.href = "/login";
  }
});

export default client;
