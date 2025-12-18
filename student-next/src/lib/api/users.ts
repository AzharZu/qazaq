import client from "./client";
import { User } from "@/types/user";

export type UpdateMePayload = {
  name?: string;
  email?: string;
  current_password?: string;
  new_password?: string;
  confirm_password?: string;
};

export type UserProfileResponse = User & {
  full_name?: string | null;
  recommended_course?: string | null;
  completed_lessons_count?: number | null;
};

export const usersApi = {
  async me(): Promise<UserProfileResponse> {
    const { data } = await client.get<UserProfileResponse>("/users/me");
    return data;
  },

  async updateMe(payload: UpdateMePayload): Promise<UserProfileResponse> {
    const { data } = await client.put<UserProfileResponse>("/users/me", payload);
    return data;
  },
};

export default usersApi;
