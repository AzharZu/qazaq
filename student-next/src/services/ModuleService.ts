import api from "@/lib/api";
import { Module } from "@/types/module";
import { LessonSummary } from "@/types/lesson";

export const ModuleService = {
  async get(moduleId: number | string): Promise<Module> {
    const { data } = await api.get(`/modules/${moduleId}`);
    return data;
  },

  async lessons(moduleId: number | string): Promise<{ lessons: LessonSummary[]; progress_map: Record<number, string> }> {
    const { data } = await api.get(`/modules/${moduleId}/lessons`);
    return data;
  },
};
