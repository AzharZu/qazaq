import { buildCrud } from "./crud";
import { Course, Module, Lesson, LessonBlock, VocabularyEntry, PlacementQuestion, UserRow } from "../types";
import { api } from "./client";

// Public APIs (with progress data)
export const coursesApi = buildCrud<Course>("/courses");
export const modulesApi = buildCrud<Module>("/modules");

// Admin APIs
export const adminCoursesApi = {
  async list(): Promise<Course[]> {
    const { data } = await api.get<Course[]>("admin/courses");
    return data;
  },
  async create(payload: Partial<Course>): Promise<Course> {
    const { data } = await api.post<Course>("admin/courses", payload);
    return data;
  },
  async update(id: number, payload: Partial<Course>): Promise<Course> {
    const { data } = await api.put<Course>(`courses/${id}`, payload);
    return data;
  },
  async remove(id: number): Promise<void> {
    await api.delete(`admin/courses/${id}`);
  },
};

export const adminModulesApi = {
  async list(courseId: number): Promise<Module[]> {
    const { data } = await api.get<Module[]>(`admin/modules?course_id=${courseId}`);
    return data;
  },
  async create(payload: Partial<Module>): Promise<Module> {
    const { data } = await api.post<Module>("admin/modules", payload);
    return data;
  },
  async update(id: number, payload: Partial<Module>): Promise<Module> {
    const { data } = await api.put<Module>(`modules/${id}`, payload);
    return data;
  },
  async remove(id: number): Promise<void> {
    await api.delete(`admin/modules/${id}`);
  },
};

export const adminLessonsApi = {
  async list(moduleId: number): Promise<Lesson[]> {
    const { data } = await api.get<Lesson[]>(`admin/lessons?module_id=${moduleId}`);
    return data;
  },
  async create(payload: Partial<Lesson>): Promise<Lesson> {
    const { data } = await api.post<Lesson>("admin/lessons", payload);
    return data;
  },
  async update(id: number, payload: Partial<Lesson>): Promise<Lesson> {
    const { data } = await api.patch<Lesson>(`admin/lessons/${id}`, payload);
    return data;
  },
  async remove(id: number): Promise<void> {
    await api.delete(`admin/lessons/${id}`);
  },
};

export const lessonsApi = buildCrud<Lesson>("/lessons");
export const blocksApi = buildCrud<LessonBlock>("/blocks");
export const vocabularyApi = buildCrud<VocabularyEntry>("/vocabulary");

export const placementApi = {
  async list(): Promise<PlacementQuestion[]> {
    const { data } = await api.get<PlacementQuestion[]>("placement/admin");
    return data;
  },
  async create(payload: Partial<PlacementQuestion>) {
    const { data } = await api.post<PlacementQuestion>("placement/admin", payload);
    return data;
  },
  async update(id: number, payload: Partial<PlacementQuestion>) {
    const { data } = await api.put<PlacementQuestion>(`placement/admin/${id}`, payload);
    return data;
  },
  async remove(id: number) {
    await api.delete(`placement/admin/${id}`);
  },
};

export const usersApi = {
  async list(): Promise<UserRow[]> {
    const { data } = await api.get<UserRow[]>("users");
    return data;
  },
  async get(id: number): Promise<UserRow> {
    const { data } = await api.get<UserRow>(`users/${id}`);
    return data;
  },
};
