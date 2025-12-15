import { User } from "@/types/user";
import client from "./client";

export type AuthResponse = {
  token: string;
  user: User;
};

export const authApi = {
  async login(email: string, password: string): Promise<AuthResponse> {
    const { data } = await client.post<AuthResponse>("/auth/login", { email, password });
    return data;
  },

  async register(payload: { email: string; password: string; name?: string }): Promise<AuthResponse> {
    const body = {
      email: payload.email,
      password: payload.password,
      name: payload.name,
      age: 18,
      target: "general",
      daily_minutes: 15,
    };
    await client.post("/auth/signup", body);
    const { data } = await client.post<AuthResponse>("/auth/login", { email: payload.email, password: payload.password });
    return data;
  },

  async me(): Promise<User> {
    const { data } = await client.get<User>("/auth/me");
    return data;
  },

  async logout(): Promise<void> {
    try {
      await client.post("/auth/logout");
    } catch (err) {
      console.warn("Logout request failed", err);
    }
  },
};

export default authApi;
