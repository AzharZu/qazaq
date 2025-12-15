import client from "./client";
import { LessonBlock, LessonDetail } from "@/types/lesson";

export const lessonsApi = {
  async getLesson(lessonId: number | string, opts?: { preview?: boolean }): Promise<LessonDetail> {
    const suffix = opts?.preview ? "?preview=1" : "";
    const { data } = await client.get<LessonDetail>(`/lessons/${lessonId}${suffix}`);
    return data;
  },

  async completeLesson(lessonId: number | string, payload: Record<string, any> = {}) {
    const { data } = await client.post<{ next_lesson_id?: number | null; passed?: boolean; score?: number; total_questions?: number }>(
      `/lessons/${lessonId}/complete`,
      payload
    );
    return data;
  },

  async saveProgress(lessonId: number | string, payload: { status?: string; time_spent?: number; score?: number; answers?: Record<string, any> }) {
    const { data } = await client.post(`/lessons/${lessonId}/progress`, payload);
    return data;
  },

  async blocks(lessonId: number | string): Promise<LessonBlock[]> {
    const detail = await lessonsApi.getLesson(lessonId);
    return detail.blocks || [];
  },

  async blockFinished(payload: { lesson_id: number | string; block_id: number | string; status?: string; time_spent?: number }) {
    const { data } = await client.post("/progress/block-finished", payload);
    return data;
  },
};

export default lessonsApi;
