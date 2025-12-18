import Link from "next/link";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";
import LessonBlockRenderer from "@/components/LessonBlockRenderer";
import ProgressBar from "@/components/ProgressBar";
import { lessonsApi } from "@/lib/api/lessons";
import { LessonDetail, LessonBlock } from "@/types/lesson";
import { useProgressStore } from "@/store/progressStore";
import VideoPlayer from "@/components/lesson/VideoPlayer";
import { computeStubLessonScore, MOCK_CHECKS_ENABLED } from "@/lib/mockAssessments";

const STEP_DEFS: { key: string; label: string; types: string[] }[] = [
  { key: "theory", label: "Теория", types: ["theory", "video", "audio_theory"] },
  { key: "flashcards", label: "Флеш-карточки", types: ["flashcards", "flashcard"] },
  { key: "pronunciation", label: "Произношение", types: ["pronunciation"] },
  { key: "tasks", label: "Задания", types: ["quiz", "theory_quiz", "lesson_test", "audio_task", "audio", "image"] },
  { key: "free_writing", label: "Свободное письмо", types: ["free_writing"] },
];
type StepKey = (typeof STEP_DEFS)[number]["key"];

export default function LessonPage() {
  const router = useRouter();
  const { id, preview } = router.query;
  const [lessonDetail, setLessonDetail] = useState<LessonDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);
  const [nextLessonId, setNextLessonId] = useState<number | null>(null);
  const [newWordsAdded, setNewWordsAdded] = useState<number>(0);
  const [resultScore, setResultScore] = useState<{ score: number; total: number; reason: string } | null>(null);

  const { blocks, currentIndex, completedBlockIds, setLesson, markBlockComplete, saveProgress, reset, goToBlock } = useProgressStore();
  const previewMode = preview === "1";
  const stubModeActive = MOCK_CHECKS_ENABLED;
  const [backendCompleted, setBackendCompleted] = useState(false);

  const normalizeType = useCallback((block: LessonBlock) => {
    const raw = (block?.type ||
      (block as any).block_type ||
      (block as any).blockType ||
      (block as any).kind ||
      (block as any).content?.type ||
      "") as string;
    return typeof raw === "string" ? raw.toLowerCase().replace(/-/g, "_") : "";
  }, []);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      setLoading(true);
      setNewWordsAdded(0);
      setResultScore(null);
      setCompleted(false);
      setNextLessonId(null);
      setBackendCompleted(false);
      try {
        const detail = await lessonsApi.getLesson(id as string, { preview: previewMode });
        setLessonDetail(detail);
        const lessonId = detail.lesson.id;
        const progressMap = detail.progress_map || {};
        const doneFromBackend =
          detail.progress_status === "done" ||
          progressMap?.[lessonId] === "done" ||
          progressMap?.[String(lessonId)] === "done";
        setBackendCompleted(doneFromBackend);
        setCompleted(doneFromBackend);
        if (!previewMode) {
          setNewWordsAdded(detail?.new_words_added || 0);
        }
        const incomingBlocks = (Array.isArray(detail.blocks) && detail.blocks.length ? detail.blocks : detail.lesson.blocks) || [];
        setLesson(detail.lesson.id, incomingBlocks);
        console.info("[Lesson] blocks from backend:", incomingBlocks.map((b) => normalizeType(b)));
      } catch (err: any) {
        setError(err?.response?.data?.detail || "Не удалось загрузить урок");
      } finally {
        setLoading(false);
      }
    };
    load();
    return () => reset();
  }, [id, previewMode, reset, setLesson, normalizeType]);
  const currentBlock = useMemo(() => blocks[currentIndex], [blocks, currentIndex]);
  const stepTargets = useMemo(
    () =>
      STEP_DEFS.map((def) =>
        blocks.findIndex((b, idx) => {
          const t = normalizeType(b);
          return def.types.includes(t);
        }),
      ),
    [blocks, normalizeType],
  );
  const hasPronunciationBlock = useMemo(() => blocks.some((b) => normalizeType(b) === "pronunciation"), [blocks, normalizeType]);
  const scoreSummary = useMemo(
    () => resultScore || computeStubLessonScore(hasPronunciationBlock),
    [resultScore, hasPronunciationBlock],
  );
  const activeStep = useMemo(() => {
    let active = 0;
    stepTargets.forEach((idx, i) => {
      if (idx !== -1 && currentIndex >= idx) active = i;
    });
    return active;
  }, [currentIndex, stepTargets]);

  const resolveBlockId = useCallback((block: LessonBlock | undefined, idx: number) => (block?.id ?? `idx-${idx}`).toString(), []);
  const uniqueBlockIds = useMemo(() => {
    const seen = new Set<string>();
    return blocks.reduce<string[]>((acc, block, idx) => {
      const id = resolveBlockId(block, idx);
      if (!seen.has(id)) {
        seen.add(id);
        acc.push(id);
      }
      return acc;
    }, []);
  }, [blocks, resolveBlockId]);
  const blockTypes = useMemo(() => blocks.map((b) => normalizeType(b) || "unknown"), [blocks, normalizeType]);
  const completedSet = useMemo(() => {
    const set = new Set<string>();
    completedBlockIds.forEach((id) => set.add(id.toString()));
    return set;
  }, [completedBlockIds]);
  const completedSteps = useMemo(() => uniqueBlockIds.filter((id) => completedSet.has(id)).length, [completedSet, uniqueBlockIds]);
  const totalSteps = uniqueBlockIds.length;
  const allStepsDone = totalSteps > 0 && completedSteps >= totalSteps;
  const isLessonCompleted = completed || allStepsDone || backendCompleted;
  const blockProgress = totalSteps ? Math.round((completedSteps / totalSteps) * 100) : 0;
  const displayProgress = isLessonCompleted ? 100 : blockProgress;

  useEffect(() => {
    console.debug("[LessonProgress]", {
      total_steps: totalSteps,
      completed_steps: completedSteps,
      block_ids: uniqueBlockIds,
      block_types: blockTypes,
      current_index: currentIndex,
      completed_block_ids: completedBlockIds,
      progress: displayProgress,
    });
  }, [totalSteps, completedSteps, uniqueBlockIds, blockTypes, currentIndex, completedBlockIds, displayProgress]);

  const hasVideoBlock = useMemo(() => blocks.some((b) => normalizeType(b) === "video"), [blocks, normalizeType]);
  const lessonVideoUrl = useMemo(() => {
    const videoBlock = blocks.find((b) => normalizeType(b) === "video");
    return (videoBlock as any)?.video_url || (videoBlock as any)?.content?.video_url || null;
  }, [blocks, normalizeType]);

  const finishLesson = async () => {
    if (!id) return;
    const stubScore = computeStubLessonScore(hasPronunciationBlock);
    setResultScore(stubScore);
    if (previewMode) {
      setCompleted(true);
      return;
    }
    try {
      const res = await lessonsApi.completeLesson(id as string, { score: stubScore.score, total_questions: stubScore.total });
      await saveProgress({ status: "done", score: stubScore.score });
      setNextLessonId(res?.next_lesson_id ?? null);
    } catch (_err) {
      await saveProgress({ status: "done", score: stubScore.score }).catch(() => {});
    } finally {
      setCompleted(true);
    }
  };

  const handleCompleteBlock = async (nextIndexOverride?: number) => {
    if (!blocks.length) return;
    const currentBlock = blocks[currentIndex];
    const blockId = resolveBlockId(currentBlock, currentIndex);
    const apiBlockId = currentBlock?.id;
    if (!previewMode) {
      await saveProgress({
        status: currentIndex >= blocks.length - 1 ? "done" : "in_progress",
        block_id: apiBlockId,
        score: currentIndex >= blocks.length - 1 ? computeStubLessonScore(hasPronunciationBlock).score : undefined,
      });
    }
    markBlockComplete(blockId, nextIndexOverride);
    if (currentIndex >= blocks.length - 1) {
      await finishLesson();
    }
  };

  const findStepIndex = useCallback(
    (key: StepKey) => {
      const idx = STEP_DEFS.findIndex((s) => s.key === key);
      return idx >= 0 ? stepTargets[idx] : -1;
    },
    [stepTargets],
  );

  const goToStep = useCallback(
    async (key: StepKey, opts?: { completeCurrent?: boolean }) => {
      const targetIndex = findStepIndex(key);
      const fallbackIndex = targetIndex >= 0 ? targetIndex : Math.min(currentIndex + 1, Math.max(blocks.length - 1, 0));
      if (fallbackIndex < 0 || !blocks.length) return;
      if (opts?.completeCurrent) {
        await handleCompleteBlock(fallbackIndex);
      } else {
        goToBlock(fallbackIndex);
      }
      if (typeof window !== "undefined") {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    },
    [blocks.length, currentIndex, findStepIndex, goToBlock, handleCompleteBlock],
  );

  if (loading) {
    return <div className="rounded-2xl bg-panel p-8 text-ink shadow-card">Загрузка урока...</div>;
  }

  if (error || !lessonDetail) {
    return <div className="rounded-2xl bg-panel p-8 text-red-300 shadow-card">{error || "Урок не найден"}</div>;
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-panel p-8 shadow-card">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-gold">Урок</p>
            <h1 className="text-3xl font-semibold text-white">{lessonDetail.lesson.title}</h1>
            {lessonDetail.lesson.description && <p className="mt-2 text-sm text-ink/80">{lessonDetail.lesson.description}</p>}
          </div>
          <div className="space-y-2 text-right">
            <span className="rounded-full bg-slate px-3 py-1 text-xs font-semibold text-ink shadow-soft">
              {lessonDetail.module_progress || 0}% модуля
            </span>
            <span className="rounded-full bg-slate px-3 py-1 text-xs font-semibold text-ink shadow-soft">
              {lessonDetail.course_progress || 0}% курса
            </span>
          </div>
        </div>
        <div className="mt-4">
          <ProgressBar value={displayProgress} label="Прогресс урока" />
        </div>
        {!previewMode && !!newWordsAdded && (
          <div className="mt-4 rounded-xl border border-gold/40 bg-gold/10 px-4 py-3 text-sm text-gold">
            {newWordsAdded} новых слов добавлено в словарь
            <Link href="/dictionary" className="ml-3 font-semibold underline underline-offset-4">
              Закрепить слова
            </Link>
          </div>
        )}
      </div>

      {!hasVideoBlock && lessonVideoUrl ? (
        <div className="rounded-2xl bg-panel p-4 shadow-card">
          <VideoPlayer url={lessonVideoUrl} />
        </div>
      ) : null}

      <div className="rounded-2xl bg-panel p-4 shadow-card">
        <div className="flex flex-wrap gap-3">
          {STEP_DEFS.map((step, idx) => {
            const target = stepTargets[idx];
            const status = target === -1 ? "missing" : currentIndex === target ? "active" : currentIndex > target ? "done" : "todo";
            return (
              <button
                key={step.key}
                onClick={() => goToStep(step.key)}
                disabled={target === -1}
                className={`flex-1 min-w-[140px] rounded-xl border px-4 py-3 text-sm font-semibold transition ${
                  status === "active"
                    ? "border-gold bg-gold/20 text-gold"
                    : status === "done"
                    ? "border-green-400 bg-green-400/10 text-green-100"
                    : target === -1
                    ? "border-slate/50 bg-slate/30 text-ink/50"
                    : "border-slate bg-slate/40 text-ink hover:border-gold hover:text-white"
                }`}
              >
                {step.label}
              </button>
            );
          })}
        </div>
      </div>

      {isLessonCompleted ? (
        <div className="rounded-2xl bg-panel p-8 shadow-card space-y-5">
          <h2 className="text-2xl font-semibold text-gold">Урок завершен!</h2>
          {stubModeActive ? (
            <span className="inline-flex items-center gap-2 rounded-full bg-slate px-3 py-1 text-xs font-semibold uppercase tracking-wide text-ink shadow-soft">
              Проверяется автоматически нашим ИИ
            </span>
          ) : null}
          <div className="flex flex-wrap items-start gap-4">
            <div className="rounded-2xl bg-slate px-6 py-5 shadow-inner">
              <p className="text-xs font-semibold uppercase tracking-wide text-ink/70">Результат урока</p>
              <p className="text-4xl font-bold text-white">
                {scoreSummary.score} / {scoreSummary.total}
              </p>
              <p className="text-sm text-ink/80">{scoreSummary.reason}</p>
            </div>
            <div className="flex-1 rounded-2xl border border-green-400/40 bg-green-500/15 px-6 py-5 text-sm text-green-50 shadow-inner">
              <p className="text-base font-semibold">Проверяется автоматически нашим ИИ.</p>
              <p className="mt-1 text-green-100/80">Результаты фиксируются без ожидания ручной проверки.</p>
            </div>
          </div>
          <p className="text-sm text-ink/80">Отличная работа. Продолжайте, чтобы закрепить материал.</p>
          <div className="mt-2 flex gap-3">
            {nextLessonId && (
              <Link
                href={`/lesson/${nextLessonId}`}
                className="rounded-lg bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
              >
                Следующий урок
              </Link>
            )}
            <Link
              href={`/course/${lessonDetail.lesson.module?.course?.slug || lessonDetail.lesson.module?.id || ""}`}
              className="rounded-lg bg-slate px-5 py-3 text-sm font-semibold text-ink transition hover:bg-slateDeep hover:text-white"
            >
              Вернуться к курсу
            </Link>
          </div>
        </div>
      ) : currentBlock ? (
        <LessonBlockRenderer
          block={currentBlock}
          lessonId={lessonDetail.lesson.id}
          onComplete={handleCompleteBlock}
          preview={previewMode}
          onGoToStep={goToStep}
          lessonLanguage={lessonDetail.lesson.language || "kk"}
        />
      ) : (
        <div className="rounded-2xl bg-panel p-6 shadow-card">
          <p className="text-ink/80">Блоки отсутствуют</p>
        </div>
      )}
    </div>
  );
}
