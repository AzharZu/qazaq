import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
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

const normalizeLevel = (level?: string | null) => (level || "").toUpperCase();

const slugFromLevel = (level?: string | null): string | null => {
  const normalized = normalizeLevel(level);
  if (!normalized) return null;
  if (["A0", "A1", "A2"].includes(normalized)) return "kazkids";
  if (normalized === "B1") return "kazpro";
  if (["B2", "C1", "C2"].includes(normalized)) return "qyzmet-qazaq";
  return null;
};

const extractCourseInfo = (value: PlacementResult["recommended_course"] | null | undefined): RecommendedCourseInfo | null => {
  if (value && typeof value === "object") return value as RecommendedCourseInfo;
  return null;
};

export default function LevelTestResultPage() {
  const { result, finishTest, questions, answers, loading } = useTestStore();
  const { user, setUser } = useAuthStore();
  const [data, setData] = useState<PlacementResult | null>(result);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (result) return;
    const load = async () => {
      try {
        if (questions.length && answers.some((a) => a >= 0)) {
          const res = await finishTest();
          setData(res);
        } else {
          const res = await testApi.result();
          setData(res);
        }
      } catch (err: any) {
        const message = err?.response?.data?.detail || err?.message || "Не удалось получить результат";
        setError(message);
      }
    };
    load();
  }, [answers, finishTest, questions.length, result]);

  useEffect(() => {
    if (data?.level && user) {
      setUser({ ...user, level: data.level });
    }
  }, [data?.level, setUser, user]);

  const recommended = useMemo(() => {
    if (!data) return null;

    const courseFromRecommended = extractCourseInfo(data.recommended_course);
    const courseFromPayload = data.course as RecommendedCourseInfo | null;

    const slugFromPayload =
      typeof data.recommended_course === "string" && data.recommended_course
        ? data.recommended_course.toLowerCase()
        : (courseFromRecommended?.slug || courseFromPayload?.slug || "").toLowerCase();

    const inferredSlug = slugFromPayload || slugFromLevel(data.level);
    if (!inferredSlug) return null;

    const copy = RECOMMENDED_COPY[inferredSlug] || {};
    const courseInfo = courseFromRecommended || courseFromPayload || null;

    return {
      slug: inferredSlug,
      name: copy.name || courseInfo?.name || "Рекомендуемый курс",
      description: copy.description || courseInfo?.description || "",
    };
  }, [data]);

  if (loading && !data) {
    return <div className="rounded-2xl bg-white p-8 shadow-sm">Подготавливаем результат...</div>;
  }

  if (error || !data) {
    return <div className="rounded-2xl bg-white p-8 text-red-600 shadow-sm">{error || "Результат не найден"}</div>;
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
          <p className="text-lg font-semibold text-white">
            Рекомендуемый курс: {recommended.name}
          </p>
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
}
