import { api } from "./client";

export type IdType = number | string;

export function buildCrud<T extends { id: IdType }>(base: string) {
  const normalizedBase = base.replace(/^\/+/, "");
  return {
    async list(): Promise<T[]> {
      const { data } = await api.get<T[]>(normalizedBase);
      return data;
    },
    async create(payload: Partial<T>): Promise<T> {
      const { data } = await api.post<T>(normalizedBase, payload);
      return data;
    },
    async update(id: IdType, payload: Partial<T>): Promise<T> {
      const { data } = await api.put<T>(`${normalizedBase}/${id}`, payload);
      return data;
    },
    async remove(id: IdType): Promise<void> {
      await api.delete(`${normalizedBase}/${id}`);
    },
  };
}
