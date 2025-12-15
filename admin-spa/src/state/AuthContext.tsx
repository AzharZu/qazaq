import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { authApi, type LoginPayload, type SessionUser } from "../api/auth";
import { useToast } from "../components/ui/use-toast";

type AuthContextState = {
  user: SessionUser | null;
  loading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextState | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      const data = await authApi.me();
      setUser(data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = useCallback(
    async (payload: LoginPayload) => {
      try {
        await authApi.login(payload);
        const data = await authApi.me();
        setUser(data);
        const redirectTo =
          (location.state as any)?.from?.pathname && (location.state as any)?.from?.pathname !== "/admin/login"
            ? (location.state as any).from.pathname
            : "/admin/dashboard";
        navigate(redirectTo, { replace: true });
        toast({ title: "Welcome", description: `Signed in as ${data.email}` });
      } catch (err: any) {
        toast({ title: "Login failed", description: err?.message || "Invalid credentials", variant: "destructive" });
        setUser(null);
        throw err;
      }
    },
    [navigate, toast, location.state]
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
      navigate("/admin/login", { replace: true });
    }
  }, [navigate]);

  const value: AuthContextState = { user, loading, login, logout, refresh };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextState => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
};
