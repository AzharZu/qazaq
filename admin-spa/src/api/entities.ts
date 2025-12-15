import { buildCrud } from "./crud";
import { Course, Module, Lesson, LessonBlock, VocabularyEntry, PlacementQuestion, UserRow } from "../types";
import { api } from "./client";

export const coursesApi = buildCrud<Course>("/courses");
export const modulesApi = buildCrud<Module>("/modules");
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
