import { create } from "zustand";
import { testApi } from "@/lib/api/test";
import { PlacementResult, TestQuestion } from "@/types/test";
import { resolveQuestionText } from "@/utils/question";

type TestState = {
  questions: TestQuestion[];
  answers: number[];
  currentIndex: number;
  result: PlacementResult | null;
  loading: boolean;
};

type TestActions = {
  loadQuestions: (limit?: number) => Promise<void>;
  answerQuestion: (optionIndex: number) => void;
  goToQuestion: (index: number) => void;
  finishTest: () => Promise<PlacementResult | null>;
  reset: () => void;
};

export const useTestStore = create<TestState & TestActions>((set, get) => ({
  questions: [],
  answers: [],
  currentIndex: 0,
  result: null,
  loading: false,

  loadQuestions: async (limit = 12) => {
    set({ loading: true });
    try {
      const { questions } = await testApi.fetchQuestions(limit);
      const normalized = questions.map((q, idx) => {
        const questionText = resolveQuestionText(q) || `Вопрос ${q.id ?? idx + 1}`;
        return {
          ...q,
          id: q.id ?? String(idx),
          question: questionText,
          prompt: q.prompt ?? questionText,
          title: q.title ?? questionText,
          correct: (q as any).correct ?? (q as any).correct_option,
          options: q.options || [],
        };
      });
      set({
        questions: normalized,
        answers: Array(normalized.length).fill(-1),
        currentIndex: 0,
        result: null,
      });
    } finally {
      set({ loading: false });
    }
  },

  answerQuestion: (optionIndex) => {
    const { answers, currentIndex } = get();
    const updated = [...answers];
    updated[currentIndex] = optionIndex;
    set({ answers: updated });
  },

  goToQuestion: (index) => {
    set({ currentIndex: Math.max(0, Math.min(index, get().questions.length - 1)) });
  },

  finishTest: async () => {
    const { questions, answers } = get();
    if (!questions.length) return null;
    set({ loading: true });
    try {
      const payload = questions.map((q, idx) => ({
        question_id: String(q.id ?? idx),
        selected_option: answers[idx],
      }));
      const res = await testApi.finish(payload, questions.length);
      set({ result: res });
      return res;
    } finally {
      set({ loading: false });
    }
  },

  reset: () => set({ questions: [], answers: [], currentIndex: 0, result: null }),
}));
