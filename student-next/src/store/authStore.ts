import Router from "next/router";
import { create } from "zustand";
import { authApi, AuthResponse } from "@/lib/api/auth";
import { setTokenProvider, setUnauthorizedHandler } from "@/lib/api/client";
import { User } from "@/types/user";

const TOKEN_KEY = "token";

type AuthState = {
  token: string | null;
  user: User | null;
  loading: boolean;
  error: string | null;
};

type AuthActions = {
  setToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  login: (email: string, password: string) => Promise<AuthResponse>;
  register: (payload: { email: string; password: string; name?: string }) => Promise<AuthResponse>;
  logout: (skipRedirect?: boolean) => Promise<void>;
  forceLogout: (redirect?: boolean) => void;
  loadUser: () => Promise<void>;
};

export const useAuthStore = create<AuthState & AuthActions>((set, get) => ({
  token: null,
  user: null,
  loading: false,
  error: null,

  setToken: (token) => {
    set({ token });
    if (typeof window !== "undefined") {
      if (token) {
        localStorage.setItem(TOKEN_KEY, token);
      } else {
        localStorage.removeItem(TOKEN_KEY);
      }
    }
  },

  setUser: (user) => set({ user }),

  login: async (email, password) => {
    set({ loading: true, error: null });
    try {
      const res = await authApi.login(email, password);
      get().setToken(res.token);
      set({ user: res.user });
      return res;
    } catch (err: any) {
      const message = err?.response?.data?.detail || "Не удалось войти";
      set({ error: message });
      throw err;
    } finally {
      set({ loading: false });
    }
  },

  register: async (payload) => {
    set({ loading: true, error: null });
    try {
      const res = await authApi.register(payload);
      get().setToken(res.token);
      set({ user: res.user });
      return res;
    } catch (err: any) {
      const message = err?.response?.data?.detail || "Не удалось зарегистрироваться";
      set({ error: message });
      throw err;
    } finally {
      set({ loading: false });
    }
  },

  logout: async (skipRedirect = false) => {
    set({ loading: true });
    try {
      await authApi.logout();
    } catch (err) {
      console.warn("Logout failed", err);
    } finally {
      get().forceLogout(!skipRedirect);
      set({ loading: false });
    }
  },

  forceLogout: (redirect = true) => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(TOKEN_KEY);
    }
    set({ token: null, user: null });
    if (redirect && typeof window !== "undefined" && Router.pathname !== "/login") {
      Router.push("/login");
    }
  },

  loadUser: async () => {
    const storedToken = get().token || (typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null);
    if (!storedToken) return;
    get().setToken(storedToken);
    set({ loading: true });
    try {
      const user = await authApi.me();
      set({ user });
    } catch {
      get().forceLogout(false);
    } finally {
      set({ loading: false });
    }
  },
}));

// Wire up axios token handling to the store
setTokenProvider(() => useAuthStore.getState().token);
setUnauthorizedHandler(() => useAuthStore.getState().forceLogout(true));
