import Link from "next/link";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";
import LessonBlockRenderer from "@/components/LessonBlockRenderer";
import ProgressBar from "@/components/ProgressBar";
import { lessonsApi } from "@/lib/api/lessons";
import { LessonDetail, LessonBlock } from "@/types/lesson";
import { useProgressStore } from "@/store/progressStore";
import { useDictionaryStore } from "@/store/dictionaryStore";
import VideoPlayer from "@/components/lesson/VideoPlayer";

const STEP_DEFS: { key: string; label: string; types: string[] }[] = [
  { key: "theory", label: "Теория", types: ["theory", "video", "audio_theory"] },
  { key: "flashcards", label: "Флеш-карточки", types: ["flashcards", "flashcard"] },
  { key: "pronunciation", label: "Произношение", types: ["pronunciation"] },
  { key: "tasks", label: "Задания", types: ["quiz", "theory_quiz", "lesson_test", "audio_task", "audio", "image"] },
  { key: "free_writing", label: "Свободное письмо", types: ["free_writing"] },
];

export default function LessonPage() {
  const router = useRouter();
  const { id, preview } = router.query;
  const [lessonDetail, setLessonDetail] = useState<LessonDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);
  const [nextLessonId, setNextLessonId] = useState<number | null>(null);
  const [newWordsAdded, setNewWordsAdded] = useState<number>(0);
  const { loadWords } = useDictionaryStore();

  const { blocks, currentIndex, setLesson, markBlockComplete, saveProgress, reset, goToBlock } = useProgressStore();
  const previewMode = preview === "1";

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
      try {
        const detail = await lessonsApi.getLesson(id as string, { preview: previewMode });
        setLessonDetail(detail);
        if (!previewMode) {
          setNewWordsAdded(detail?.new_words_added || 0);
          await loadWords(detail?.lesson?.id).catch(() => {});
        }
        setLesson(detail.lesson.id, detail.lesson.blocks || detail.blocks || []);
        const incomingBlocks = detail.lesson.blocks || detail.blocks || [];
        console.info("[Lesson] blocks from backend:", incomingBlocks.map((b) => normalizeType(b)));
      } catch (err: any) {
        setError(err?.response?.data?.detail || "Не удалось загрузить урок");
      } finally {
        setLoading(false);
      }
    };
    load();
    return () => reset();
  }, [id, previewMode, reset, setLesson, normalizeType, loadWords]);

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
  const activeStep = useMemo(() => {
    let active = 0;
    stepTargets.forEach((idx, i) => {
      if (idx !== -1 && currentIndex >= idx) active = i;
    });
    return active;
  }, [currentIndex, stepTargets]);

  const goToStep = (key: string) => {
    const targetIndex = stepTargets[STEP_DEFS.findIndex((s) => s.key === key)];
    if (targetIndex !== undefined && targetIndex >= 0) {
      goToBlock(targetIndex);
      if (typeof window !== "undefined") {
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    }
  };
  const blockProgress = blocks.length ? Math.round((currentIndex / blocks.length) * 100) : 0;
  const hasVideoBlock = useMemo(() => blocks.some((b) => normalizeType(b) === "video"), [blocks, normalizeType]);
  const lessonVideoUrl = useMemo(() => {
    const videoBlock = blocks.find((b) => normalizeType(b) === "video");
    return (videoBlock as any)?.video_url || (videoBlock as any)?.content?.video_url || null;
  }, [blocks, normalizeType]);

  const finishLesson = async () => {
    if (!id) return;
    if (previewMode) {
      setCompleted(true);
      return;
    }
    const res = await lessonsApi.completeLesson(id as string, {});
    await saveProgress({ status: "done" });
    await loadWords(id as string).catch(() => {});
    setNextLessonId(res?.next_lesson_id ?? null);
    setCompleted(true);
  };

  const handleCompleteBlock = async () => {
    if (!blocks.length) return;
    const currentBlock = blocks[currentIndex];
    if (!previewMode) {
      await saveProgress({ status: currentIndex >= blocks.length - 1 ? "done" : "in_progress", block_id: currentBlock?.id });
    }
    if (currentIndex >= blocks.length - 1) {
      await finishLesson();
    } else {
      markBlockComplete(blocks[currentIndex]?.id || currentIndex);
    }
  };

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
          <ProgressBar value={blockProgress} label="Прогресс урока" />
        </div>
        {!previewMode && !!newWordsAdded && (
          <div className="mt-4 rounded-xl border border-gold/40 bg-gold/10 px-4 py-3 text-sm text-gold">
            {newWordsAdded} новых слов добавлено в словарь
            <Link href={`/dictionary?lessonId=${lessonDetail.lesson.id}`} className="ml-3 font-semibold underline underline-offset-4">
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

      {completed ? (
        <div className="rounded-2xl bg-panel p-8 shadow-card">
          <h2 className="text-2xl font-semibold text-gold">Урок завершен!</h2>
          <p className="mt-2 text-sm text-ink/80">Отличная работа. Продолжайте, чтобы закрепить материал.</p>
          <div className="mt-4 flex gap-3">
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
