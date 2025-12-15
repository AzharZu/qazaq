import Link from "next/link";
import { useEffect, useState } from "react";
import { testApi } from "@/lib/api/test";
import { useTestStore } from "@/store/testStore";
import { PlacementResult } from "@/types/test";

export default function LevelTestResultPage() {
  const { result, finishTest, questions, answers, loading } = useTestStore();
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
        setError(err?.response?.data?.detail || "Не удалось получить результат");
      }
    };
    load();
  }, [answers, finishTest, questions.length, result]);

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
      {data.recommended_course && (
        <div className="rounded-2xl bg-slate/60 p-5 shadow-inner">
          <p className="text-sm font-semibold text-ink/80">Рекомендуемый курс</p>
          <p className="text-lg font-semibold text-white">{data.recommended_course.name}</p>
          <p className="text-sm text-ink/80">{data.recommended_course.description}</p>
          <Link
            href={`/course/${data.recommended_course.slug || data.recommended_course.id}`}
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
