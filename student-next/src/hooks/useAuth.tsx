"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { clearToken, getToken, setToken as persistToken } from "@/lib/auth";
import { AuthService } from "@/services/AuthService";
import { User } from "@/types/user";

type AuthContextValue = {
  user: User | null;
  token: string | null;
  loading: boolean;
  language: "kk" | "ru";
  login: (email: string, password: string) => Promise<void>;
  register: (payload: { email: string; password: string; name?: string }) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  setLanguage: (lang: "kk" | "ru") => void;
  isAuthenticated: boolean;
};

const AuthContext = createContext<AuthContextValue>({
  user: null,
  token: null,
  loading: true,
  language: "kk",
  login: async () => {},
  register: async () => {},
  logout: async () => {},
  refresh: async () => {},
  setLanguage: () => {},
  isAuthenticated: false,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [language, setLanguageState] = useState<"kk" | "ru">("kk");

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const me = await AuthService.me();
      setUser(me);
    } catch {
      clearToken();
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      setLoading(true);
      try {
        const data = await AuthService.login(email, password);
        if (data?.token) {
          persistToken(data.token);
          setToken(data.token);
        }
        if (data?.user) {
          setUser(data.user);
        } else {
          await refresh();
        }
      } finally {
        setLoading(false);
      }
    },
    [refresh]
  );

  const register = useCallback(
    async (payload: { email: string; password: string; name?: string }) => {
      setLoading(true);
      try {
        const data = await AuthService.register(payload);
        if (data?.token) {
          persistToken(data.token);
          setToken(data.token);
        }
        if (data?.user) {
          setUser(data.user);
        } else {
          await refresh();
        }
      } finally {
        setLoading(false);
      }
    },
    [refresh]
  );

  const logout = useCallback(async () => {
    await AuthService.logout();
    clearToken();
    setToken(null);
    setUser(null);
    router.push("/login");
  }, [router]);

  const setLanguage = useCallback((lang: "kk" | "ru") => {
    setLanguageState(lang);
    if (typeof window !== "undefined") {
      localStorage.setItem("language", lang);
    }
  }, []);

  useEffect(() => {
    const storedLang = typeof window !== "undefined" ? (localStorage.getItem("language") as "kk" | "ru" | null) : null;
    if (storedLang) {
      setLanguageState(storedLang);
    }
    const savedToken = getToken();
    if (savedToken) {
      setToken(savedToken);
      refresh();
    } else {
      setLoading(false);
    }
  }, [refresh]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      loading,
      language,
      login,
      register,
      logout,
      refresh,
      setLanguage,
      isAuthenticated: Boolean(token),
    }),
    [user, token, loading, language, login, register, logout, refresh, setLanguage]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
