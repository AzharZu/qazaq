import { create } from "zustand";
import { checkPronunciation, PronunciationResult } from "@/lib/api/pronunciation";

type Status = "excellent" | "good" | "ok" | "bad" | null;

type PronunciationState = {
  lastScore: number | null;
  status: Status;
  loading: boolean;
  error: string | null;
};

type PronunciationActions = {
  evaluate: (phrase: string, language?: string) => Promise<PronunciationResult>;
  reset: () => void;
};

export const usePronunciationStore = create<PronunciationState & PronunciationActions>((set) => ({
  lastScore: null,
  status: null,
  loading: false,
  error: null,

  evaluate: async (phrase: string, language?: string) => {
    set({ loading: true, error: null });
    try {
      const res = await checkPronunciation(phrase, language);
      set({ lastScore: res.score, status: res.status, loading: false });
      return res;
    } catch (err: any) {
      const message = err?.response?.data?.detail || "Не удалось оценить произношение";
      set({ error: message, loading: false });
      throw err;
    }
  },

  reset: () => set({ lastScore: null, status: null, loading: false, error: null }),
}));
