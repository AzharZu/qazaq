import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";
import QuizOption from "@/components/QuizOption";
import ProgressBar from "@/components/ProgressBar";
import { useTestStore } from "@/store/testStore";

export default function LevelTestQuestionPage() {
  const router = useRouter();
  const { n } = router.query;
  const index = useMemo(() => Number(n || 0), [n]);
  const { questions, answers, loadQuestions, answerQuestion, goToQuestion, finishTest, loading } = useTestStore();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!questions.length) {
      loadQuestions().catch((err: any) => {
        setError(err?.response?.data?.detail || "Не удалось загрузить тест");
      });
    } else {
      goToQuestion(index);
    }
  }, [index, questions.length, goToQuestion, loadQuestions]);

  const question = questions[index];
  const selected = answers[index];
  const progressValue = questions.length ? Math.round(((index + 1) / questions.length) * 100) : 0;

  const next = async () => {
    if (index + 1 < questions.length) {
      goToQuestion(index + 1);
      router.push(`/level-test/question/${index + 1}`);
    } else {
      await finishTest();
      router.push("/level-test/result");
    }
  };

  if (loading && !questions.length) {
    return <div className="rounded-2xl bg-panel p-8 text-ink shadow-card">Готовим вопросы...</div>;
  }

  if (error) {
    return <div className="rounded-2xl bg-panel p-8 text-red-200 shadow-card">{error}</div>;
  }

  if (!question) {
    return <div className="rounded-2xl bg-panel p-8 text-ink shadow-card">Вопросы не найдены. Попробуйте начать тест заново.</div>;
  }

  return (
    <div className="space-y-6 rounded-2xl bg-panel p-10 shadow-card">
      <div className="flex items-center justify-between gap-3">
        <div className="w-full text-center">
          <h1 className="text-3xl font-semibold text-white leading-snug">
            {index + 1}.{" "}{question.question}
          </h1>
        </div>
        <span className="shrink-0 rounded-full bg-slate px-3 py-1 text-xs font-semibold text-ink shadow-soft">
          {index + 1}/{questions.length}
        </span>
      </div>
      <ProgressBar value={progressValue} />
      <div className="space-y-3">
        {question.options.map((opt, idx) => (
          <QuizOption
            key={idx}
            index={idx}
            label={opt}
            selected={selected === idx}
            onSelect={() => answerQuestion(idx)}
          />
        ))}
      </div>
      <div className="flex justify-end">
        <button
          onClick={next}
          disabled={selected === undefined || selected === -1}
          className="rounded-xl bg-gold px-6 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark disabled:cursor-not-allowed disabled:bg-slate/50"
        >
          {index + 1 === questions.length ? "Завершить" : "Далее"}
        </button>
      </div>
    </div>
  );
}
