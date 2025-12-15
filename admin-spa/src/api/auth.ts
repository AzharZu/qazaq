import AuthService from "../services/AuthService";

export type LoginPayload = { email: string; password: string };
export type SessionUser = { id: number; email: string; role?: string; is_admin?: boolean };

export const authApi = {
  async login(payload: LoginPayload): Promise<SessionUser> {
    const { user } = await AuthService.login(payload.email, payload.password);
    return user;
  },
  async me(): Promise<SessionUser> {
    const { data } = await AuthService.api.get<SessionUser>("auth/me");
    return data;
  },
  async logout(): Promise<void> {
    await AuthService.api.post("auth/logout");
    AuthService.logout();
  },
};
