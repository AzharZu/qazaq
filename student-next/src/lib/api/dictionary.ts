import client from "./client";
import { VocabularyWord } from "@/types/vocabulary";

export type DictionaryWord = VocabularyWord & {
  progress?: {
    success: number;
    fails: number;
    last_review?: string | null;
  };
};

export type DictionaryStats = {
  total?: number;
  learned?: number;
  avg_success?: number;
  hardest?: { id: number; word: string; translation: string; wrong_attempts?: number; correct_attempts?: number }[];
};

export const dictionaryApi = {
  async getDictionaryWords(opts?: { lessonId?: number | string }): Promise<DictionaryWord[]> {
    const query = opts?.lessonId ? `?lessonId=${opts.lessonId}` : "";
    const { data } = await client.get<DictionaryWord[]>(`/dictionary${query}`);
    return (data || []).map((w) => ({
      ...w,
      progress: w.progress || { success: 0, fails: 0, last_review: null },
    }));
  },

  async markSuccess(wordId: number | string) {
    try {
      await client.post(`/dictionary/${wordId}/success`);
    } catch (err) {
      console.warn("markSuccess fallback (endpoint may be missing)", err);
    }
  },

  async markFail(wordId: number | string) {
    try {
      await client.post(`/dictionary/${wordId}/fail`);
    } catch (err) {
      console.warn("markFail fallback (endpoint may be missing)", err);
    }
  },

  async submitResult(wordId: number | string, payload: { mode: "repeat" | "mc" | "write" | string; correct: boolean }) {
    const { data } = await client.post<DictionaryWord>(`/dictionary/${wordId}/result`, payload);
    return data;
  },

  async getStats(): Promise<DictionaryStats> {
    const { data } = await client.get<DictionaryStats>("/vocabulary/stats");
    return data || {};
  },

  async getWordOfWeek(): Promise<VocabularyWord | null> {
    const { data } = await client.get<{ word?: VocabularyWord | null }>("/vocabulary/weekly");
    return data?.word || null;
  },
};

export default dictionaryApi;
