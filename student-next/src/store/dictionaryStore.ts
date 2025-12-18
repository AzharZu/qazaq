import { create } from "zustand";
import { dictionaryApi, DictionaryWord } from "@/lib/api/dictionary";

export type DictionaryMode = "all" | "learned" | "repeat";

type DictionaryState = {
  words: DictionaryWord[];
  currentIndex: number;
  mode: DictionaryMode;
  loading: boolean;
  error: string | null;
};

type DictionaryActions = {
  loadWords: () => Promise<void>;
  setMode: (mode: DictionaryMode) => void;
  markSuccess: (wordId: number) => Promise<void>;
  markFail: (wordId: number) => Promise<void>;
  submitResult: (wordId: number, mode: "repeat" | "mc" | "write", correct: boolean) => Promise<void>;
  getNextWordIndex: () => number;
  setCurrentIndex: (index: number) => void;
};

const filterByMode = (words: DictionaryWord[], mode: DictionaryMode) => {
  if (mode === "learned") return words.filter((w) => (w.status === "learned" || w.learned) || (w.progress?.success || 0) > (w.progress?.fails || 0));
  if (mode === "repeat") return words.filter((w) => w.status !== "learned");
  return words;
};

const sortByStatus = (list: DictionaryWord[]) => {
  const rank = (status?: string) => ({ new: 0, learning: 1, learned: 2 }[status || "learning"] ?? 1);
  return [...list].sort((a, b) => {
    const r = rank(a.status) - rank(b.status);
    if (r !== 0) return r;
    return (b.id || 0) - (a.id || 0);
  });
};

export const useDictionaryStore = create<DictionaryState & DictionaryActions>((set, get) => ({
  words: [],
  currentIndex: 0,
  mode: "all",
  loading: false,
  error: null,

  loadWords: async () => {
    set({ loading: true, error: null });
    try {
      const words = await dictionaryApi.getDictionaryWords();
      set({ words: sortByStatus(words), currentIndex: 0 });
    } catch (err: any) {
      set({ error: err?.response?.data?.detail || "Не удалось загрузить словарь" });
    } finally {
      set({ loading: false });
    }
  },

  setMode: (mode) => {
    const filtered = filterByMode(get().words, mode);
    set({ mode, currentIndex: filtered.length ? 0 : 0 });
  },

  markSuccess: async (wordId) => {
    await dictionaryApi.markSuccess(wordId);
    set((state) => ({
      words: sortByStatus(
        state.words.map((w) =>
          w.id === wordId
            ? {
                ...w,
                status: w.status === "learned" ? "learned" : "learning",
                progress: {
                  success: (w.progress?.success || 0) + 1,
                  fails: w.progress?.fails || 0,
                  last_review: new Date().toISOString(),
                },
              }
            : w
        )
      ),
    }));
  },

  markFail: async (wordId) => {
    await dictionaryApi.markFail(wordId);
    set((state) => ({
      words: sortByStatus(
        state.words.map((w) =>
          w.id === wordId
            ? {
                ...w,
                status: w.status === "learned" ? "learned" : "learning",
                progress: {
                  success: w.progress?.success || 0,
                  fails: (w.progress?.fails || 0) + 1,
                  last_review: new Date().toISOString(),
                },
              }
            : w
        )
      ),
    }));
  },

  submitResult: async (wordId, mode, correct) => {
    const updated = await dictionaryApi.submitResult(wordId, { mode, correct });
    set((state) => ({
      words: sortByStatus(state.words.map((w) => (w.id === updated.id ? { ...w, ...updated } : w))),
    }));
  },

  getNextWordIndex: () => {
    const { words, mode, currentIndex } = get();
    const filtered = filterByMode(words, mode);
    if (!filtered.length) return 0;
    const weights = filtered.map((w) => Math.max(1, (w.progress?.fails || 0) - (w.progress?.success || 0) + 1));
    const totalWeight = weights.reduce((acc, w) => acc + w, 0);
    let rnd = Math.random() * totalWeight;
    let nextIdx = 0;
    for (let i = 0; i < filtered.length; i++) {
      rnd -= weights[i];
      if (rnd <= 0) {
        nextIdx = i;
        break;
      }
    }
    if (filtered.length > 1 && nextIdx === currentIndex) {
      nextIdx = (currentIndex + 1) % filtered.length;
    }
    return nextIdx;
  },

  setCurrentIndex: (index) => set({ currentIndex: index }),
}));

export const selectFilteredWords = (state: DictionaryState & DictionaryActions) => filterByMode(state.words, state.mode);
