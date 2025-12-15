import { create } from "zustand";
import { lessonsApi } from "@/lib/api/lessons";
import { LessonBlock } from "@/types/lesson";

type ProgressState = {
  currentLesson: number | null;
  currentLessonId: number | null;
  blocks: LessonBlock[];
  currentIndex: number;
  completedBlockIds: (number | string)[];
  startedAt: number | null;
};

type ProgressActions = {
  setLesson: (lessonId: number, blocks: LessonBlock[]) => void;
  markBlockComplete: (blockId?: number | string) => void;
  goToBlock: (index: number) => void;
  saveProgress: (payload?: { status?: string; score?: number; answers?: Record<string, any>; block_id?: number | string }) => Promise<void>;
  reset: () => void;
};

export const useProgressStore = create<ProgressState & ProgressActions>((set, get) => ({
  currentLesson: null,
  currentLessonId: null,
  blocks: [],
  currentIndex: 0,
  completedBlockIds: [],
  startedAt: null,

  setLesson: (lessonId, blocks) =>
    set({
      currentLesson: Number(lessonId),
      currentLessonId: Number(lessonId),
      blocks: [...blocks].sort((a, b) => (a.order || 0) - (b.order || 0)),
      currentIndex: 0,
      completedBlockIds: [],
      startedAt: Date.now(),
    }),

  markBlockComplete: (blockId) => {
    const { currentIndex, blocks, completedBlockIds } = get();
    const nextIndex = Math.min(currentIndex + 1, Math.max(blocks.length - 1, 0));
    const ids = completedBlockIds.includes(blockId ?? currentIndex) ? completedBlockIds : [...completedBlockIds, blockId ?? currentIndex];
    set({ currentIndex: nextIndex, completedBlockIds: ids });
  },

  goToBlock: (index) => {
    set({ currentIndex: Math.max(0, Math.min(index, get().blocks.length - 1)) });
  },

  saveProgress: async (payload = {}) => {
    const { currentLessonId, startedAt } = get();
    if (!currentLessonId) return;
    const time_spent = startedAt ? Math.floor((Date.now() - startedAt) / 1000) : undefined;
    if (payload.block_id !== undefined) {
      await lessonsApi.blockFinished({
        lesson_id: currentLessonId,
        block_id: payload.block_id,
        status: payload.status,
        time_spent,
      });
    } else {
      await lessonsApi.saveProgress(currentLessonId, { ...payload, time_spent });
    }
  },

  reset: () => set({ currentLesson: null, currentLessonId: null, blocks: [], currentIndex: 0, completedBlockIds: [], startedAt: null }),
}));
