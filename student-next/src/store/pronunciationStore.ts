import { create } from "zustand";
import { checkPronunciation, PronunciationResult } from "@/lib/api/pronunciation";

type Status = "excellent" | "good" | "bad" | null;

type PronunciationState = {
  lastScore: number | null;
  status: Status;
  loading: boolean;
  error: string | null;
};

type PronunciationActions = {
  evaluate: (wordId: number, audio: Blob) => Promise<PronunciationResult>;
  reset: () => void;
};

export const usePronunciationStore = create<PronunciationState & PronunciationActions>((set) => ({
  lastScore: null,
  status: null,
  loading: false,
  error: null,

  evaluate: async (wordId: number, audio: Blob) => {
    set({ loading: true, error: null });
    try {
      const res = await checkPronunciation(wordId, audio);
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
