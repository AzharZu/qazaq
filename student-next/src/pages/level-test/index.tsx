import Link from "next/link";
import { useRouter } from "next/router";
import { useState } from "react";
import { useTestStore } from "@/store/testStore";

export default function LevelTestStartPage() {
  const router = useRouter();
  const { loadQuestions, loading } = useTestStore();
  const [error, setError] = useState<string | null>(null);

  const start = async () => {
    setError(null);
    try {
      await loadQuestions();
      router.push("/level-test/question/0");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Не удалось загрузить тест");
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6 rounded-2xl bg-panel p-10 shadow-card">
      <div className="space-y-2">
        <p className="text-sm font-semibold uppercase tracking-wide text-gold">Уровневый тест</p>
        <h1 className="text-3xl font-semibold text-white">Проверим ваш уровень A1–C2</h1>
        <p className="text-sm text-ink/80">
          Ответьте на несколько коротких вопросов. Мы определим уровень и подскажем, с какого курса начать.
        </p>
      </div>
      {error && <div className="rounded-lg bg-red-500/20 px-4 py-3 text-sm text-red-100">{error}</div>}
      <div className="flex flex-wrap gap-3">
        <button
          onClick={start}
          disabled={loading}
          className="rounded-xl bg-gold px-6 py-3 text-base font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark disabled:cursor-not-allowed disabled:bg-slate/50"
        >
          {loading ? "Готовим вопросы..." : "Начать"}
        </button>
        <Link
          href="/courses"
          className="rounded-xl bg-slate px-6 py-3 text-base font-semibold text-ink transition hover:bg-slateDeep hover:text-white"
        >
          Вернуться к курсам
        </Link>
      </div>
    </div>
  );
}
