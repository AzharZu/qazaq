import { api } from "./client";
import { BlockType, Course, Lesson, LessonBlock, Module } from "../types";

export type BlockPayload = {
  type: BlockType;
  content: Record<string, any>;
  insert_after?: number | null;
};

export const lessonBuilderApi = {
  async listCourses(): Promise<Course[]> {
    const { data } = await api.get("admin/courses");
    return data;
  },
  async createCourse(payload: Partial<Course>): Promise<Course> {
    const { data } = await api.post("admin/courses", payload);
    return data;
  },
  async deleteCourse(courseId: number) {
    await api.delete(`admin/courses/${courseId}`);
  },
  async listModules(courseId?: number): Promise<Module[]> {
    const { data } = await api.get("admin/modules", { params: courseId ? { course_id: courseId } : undefined });
    return data;
  },
  async createModule(payload: Partial<Module>): Promise<Module> {
    const { data } = await api.post("admin/modules", payload);
    return data;
  },
  async updateModule(moduleId: number, payload: Partial<Module>): Promise<Module> {
    const { data } = await api.patch(`admin/modules/${moduleId}`, payload);
    return data;
  },
  async deleteModule(moduleId: number) {
    await api.delete(`admin/modules/${moduleId}`);
  },
  async listLessons(moduleId?: number): Promise<Lesson[]> {
    const { data } = await api.get("admin/lessons", { params: moduleId ? { module_id: moduleId } : undefined });
    return data;
  },
  async createLesson(payload: Partial<Lesson>) {
    const { data } = await api.post("admin/lessons", payload);
    return data;
  },
  async fetchLesson(lessonId: number): Promise<Lesson & { blocks: LessonBlock[] }> {
    const { data } = await api.get(`admin/lessons/${lessonId}`);
    return data;
  },
  async updateLesson(lessonId: number, payload: Partial<Lesson>) {
    const { data } = await api.patch(`admin/lessons/${lessonId}`, payload);
    return data;
  },
  async publishLesson(lessonId: number) {
    const { data } = await api.post(`admin/lessons/${lessonId}/publish`);
    return data;
  },
  async createBlock(lessonId: number, payload: BlockPayload) {
    const { data } = await api.post(`admin/lessons/${lessonId}/blocks`, payload);
    return data;
  },
  async updateBlock(blockId: number, payload: Partial<BlockPayload> & { order?: number }) {
    const { data } = await api.patch(`admin/lessons/blocks/${blockId}`, payload);
    return data;
  },
  async deleteBlock(blockId: number) {
    await api.delete(`admin/lessons/blocks/${blockId}`);
  },
  async deleteLesson(lessonId: number) {
    await api.delete(`admin/lessons/${lessonId}`);
  },
  async duplicateBlock(blockId: number) {
    const { data } = await api.post(`admin/lessons/blocks/${blockId}/duplicate`);
    return data;
  },
  async reorderBlocks(lessonId: number, order: number[]) {
    await api.post(`admin/lessons/${lessonId}/blocks/reorder`, { order });
  },
  async upload(kind: "image" | "audio" | "video", file: File) {
    const form = new FormData();
    form.append("file", file);
    const { data } = await api.post(`upload/${kind}`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },
};
