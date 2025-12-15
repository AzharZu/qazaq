import api from "@/lib/api";
import { LessonDetail } from "@/types/lesson";

export const LessonService = {
  async get(lessonId: number | string): Promise<LessonDetail> {
    const { data } = await api.get(`/lessons/${lessonId}`);
    return data;
  },

  async complete(lessonId: number | string, payload: Record<string, any> = {}) {
    const { data } = await api.post(`/lessons/${lessonId}/complete`, payload);
    return data as { next_lesson_id?: number | null; passed?: boolean; score?: number; total_questions?: number };
  },
};
