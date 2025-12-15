import api from "@/lib/api";
import { User } from "@/types/user";

export type AuthResponse = {
  token: string;
  user: User;
};

export const AuthService = {
  async login(email: string, password: string): Promise<AuthResponse> {
    const { data } = await api.post("/auth/login", { email, password });
    return data;
  },

  async register(payload: { email: string; password: string; name?: string }): Promise<AuthResponse> {
    const body = {
      email: payload.email,
      password: payload.password,
      age: 18,
      target: "general",
      daily_minutes: 10,
    };
    await api.post("/auth/signup", body);
    const { data } = await api.post("/auth/login", { email: payload.email, password: payload.password });
    return data;
  },

  async me(): Promise<User> {
    const { data } = await api.get("/auth/me");
    return data;
  },

  async logout(): Promise<void> {
    try {
      await api.post("/auth/logout");
    } catch (err) {
      console.warn("Logout error", err);
    }
  },
};
