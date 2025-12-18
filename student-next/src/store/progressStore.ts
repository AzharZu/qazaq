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
  markBlockComplete: (blockId?: number | string, nextIndexOverride?: number) => void;
  markAllComplete: (blockIds: (number | string)[]) => void;
  goToBlock: (index: number) => void;
  saveProgress: (payload?: { status?: string; score?: number; answers?: Record<string, any>; block_id?: number | string }) => Promise<void>;
  reset: () => void;
};

const coerceIndex = (value: number | undefined | null) => (Number.isFinite(value) ? Number(value) : 0);
const clampIndex = (index: number, total: number) => {
  const safeIndex = coerceIndex(index);
  return Math.max(0, Math.min(safeIndex, Math.max(total - 1, 0)));
};
const normalizeBlockId = (blockId: number | string | undefined, fallbackIndex: number) =>
  (blockId ?? `idx-${fallbackIndex}`).toString();

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

  markBlockComplete: (blockId, nextIndexOverride) => {
    const { currentIndex, blocks, completedBlockIds } = get();
    const fallbackIndex = clampIndex(currentIndex, blocks.length);
    const resolvedId = normalizeBlockId(blockId ?? blocks[fallbackIndex]?.id, fallbackIndex);
    const idsSet = new Set<string>(completedBlockIds.map((id) => id.toString()));
    idsSet.add(resolvedId);
    const nextIndex = nextIndexOverride !== undefined ? clampIndex(nextIndexOverride, blocks.length) : clampIndex(currentIndex + 1, blocks.length);
    set({ currentIndex: nextIndex, completedBlockIds: Array.from(idsSet) });
  },

  markAllComplete: (blockIds) => {
    const unique = Array.from(new Set(blockIds.map((id) => id.toString())));
    const nextIndex = clampIndex(unique.length - 1, get().blocks.length);
    set({ completedBlockIds: unique, currentIndex: nextIndex });
  },

  goToBlock: (index) => {
    set({ currentIndex: clampIndex(index, get().blocks.length) });
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
