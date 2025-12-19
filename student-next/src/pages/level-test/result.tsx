import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import ErrorBoundary from "@/components/ErrorBoundary";
import { testApi } from "@/lib/api/test";
import { useAuthStore } from "@/store/authStore";
import { useTestStore } from "@/store/testStore";
import { PlacementResult, RecommendedCourseInfo } from "@/types/test";

const RECOMMENDED_COPY: Record<string, { name: string; description: string }> = {
  kazkids: {
    name: "KazKids",
    description: "Стартовый курс для начинающих и младших уровней A1–A2.",
  },
  kazpro: {
    name: "KazMentor",
    description: "Курс для уровня B1: практика, диалоги и уверенное общение.",
  },
  "qyzmet-qazaq": {
    name: "Qyzmet Qazaq",
    description: "B2+ и деловое общение: официальные письма, встречи, телефон.",
  },
};

const DEFAULT_ERROR_MESSAGE = "Не удалось загрузить результат, попробуйте ещё раз";

const normalizeLevel = (level?: string | null) => (typeof level === "string" ? level : "").toUpperCase();

const slugFromLevel = (level?: string | null): string | null => {
  const normalized = normalizeLevel(level);
  if (!normalized) return null;
  if (["A0", "A1", "A2"].includes(normalized)) return "kazkids";
  if (normalized === "B1") return "kazpro";
  if (["B2", "C1", "C2"].includes(normalized)) return "qyzmet-qazaq";
  return null;
};

const extractCourseInfo = (value: unknown): RecommendedCourseInfo | null => {
  if (value && typeof value === "object") return value as RecommendedCourseInfo;
  return null;
};

export default function LevelTestResultPage() {
  const { result, finishTest, questions, answers, loading } = useTestStore();
  const { user, setUser } = useAuthStore();
  const [data, setData] = useState<PlacementResult | null>(result);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const canSubmit = useMemo(
    () => questions.length > 0 && answers.length === questions.length && answers.every((a) => a >= 0),
    [answers, questions.length]
  );

  const loadResult = useCallback(async () => {
    setError(null);
    setIsLoading(true);
    try {
      const res = canSubmit ? await finishTest() : await testApi.result();
      if (!res) {
        throw new Error("Пустой ответ от сервера");
      }
      setData(res);
    } catch (err: any) {
      console.error("Failed to load placement result", err);
      const message = err?.response?.data?.detail || DEFAULT_ERROR_MESSAGE;
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [canSubmit, finishTest]);

  useEffect(() => {
    if (result) {
      setData(result);
      return;
    }
    loadResult();
  }, [loadResult, result]);

  useEffect(() => {
    if (data?.level && user) {
      setUser({ ...user, level: data.level });
    }
  }, [data?.level, setUser, user]);

  const recommended = useMemo(() => {
    if (!data) return null;

    const courseFromRecommended = extractCourseInfo(data.recommended_course);
    const courseFromPayload = extractCourseInfo(data.course);

    const recommendedSlug =
      typeof data.recommended_course === "string" && data.recommended_course
        ? data.recommended_course.toLowerCase()
        : (courseFromRecommended?.slug || courseFromPayload?.slug || "").toLowerCase();

    const inferredSlug = recommendedSlug || slugFromLevel(data.level);
    const copy = inferredSlug ? RECOMMENDED_COPY[inferredSlug] : undefined;
    const courseInfo = courseFromRecommended || courseFromPayload || null;

    return {
      slug: inferredSlug || courseInfo?.slug || null,
      name: copy?.name || courseInfo?.name || "Рекомендуемый курс",
      description:
        copy?.description || courseInfo?.description || "Мы подберем курс под ваш уровень и цели.",
    };
  }, [data]);

  const renderError = (message: string, onRetry?: () => void) => (
    <div className="mx-auto max-w-3xl space-y-4 rounded-2xl bg-panel p-8 text-red-100 shadow-card">
      <p className="text-sm font-semibold uppercase tracking-wide text-red-300">Ошибка</p>
      <p className="text-sm text-red-100">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
        >
          Повторить
        </button>
      )}
    </div>
  );

  const busy = loading || isLoading;
  const content = (() => {
    if (busy && !data) {
      return <div className="rounded-2xl bg-white p-8 shadow-sm">Подготавливаем результат...</div>;
    }
    if (error || !data) {
      return renderError(error || DEFAULT_ERROR_MESSAGE, loadResult);
    }
    return (
      <div className="mx-auto max-w-3xl space-y-6 rounded-2xl bg-panel p-10 shadow-card">
        <p className="text-sm font-semibold uppercase tracking-wide text-gold">Результат теста</p>
        <h1 className="text-3xl font-semibold text-white">Ваш уровень: {data.level}</h1>
        <p className="text-sm text-ink/80">
          Баллы: <span className="font-semibold text-white">{data.score}</span> из {data.total}
        </p>
        {recommended && (
          <div className="rounded-2xl bg-slate/60 p-5 shadow-inner">
            <p className="text-sm font-semibold text-ink/80">Рекомендуемый курс</p>
            <p className="text-lg font-semibold text-white">Рекомендуемый курс: {recommended.name}</p>
            {recommended.description && <p className="text-sm text-ink/80">{recommended.description}</p>}
            <Link
              href={recommended.slug ? `/course/${recommended.slug}` : "/courses"}
              className="mt-3 inline-flex rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
            >
              Начать обучение
            </Link>
          </div>
        )}
        <div className="flex flex-wrap gap-3">
          <Link
            href="/courses"
            className="rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
          >
            К списку курсов
          </Link>
          <Link
            href="/level-test"
            className="rounded-xl bg-slate px-5 py-3 text-sm font-semibold text-ink transition hover:bg-slateDeep hover:text-white"
          >
            Пройти снова
          </Link>
        </div>
      </div>
    );
  })();

  return (
    <ErrorBoundary
      onReset={loadResult}
      fallback={({ error: boundaryError, reset }) =>
        renderError(boundaryError?.message || DEFAULT_ERROR_MESSAGE, () => {
          reset();
          loadResult();
        })
      }
    >
      {content}
    </ErrorBoundary>
  );
}
