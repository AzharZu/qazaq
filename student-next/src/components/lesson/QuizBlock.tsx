import { useMemo, useState } from "react";

type Quiz = {
  question: string;
  choices: string[];
  answer: number;
};

export default function QuizBlock({ quiz }: { quiz: Quiz }) {
  const [selected, setSelected] = useState<number | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const submit = (i: number) => {
    setSelected(i);
    setSubmitted(true);
  };

  const statusLabel = useMemo(() => {
    if (!submitted || selected === null) return "";
    return selected === quiz.answer ? "Верно" : "Неверно";
  }, [submitted, selected, quiz.answer]);

  return (
    <div className="rounded-lg border border-slate-200 bg-[#ededed] p-4">
      <h3 className="text-lg font-semibold text-slate-900">{quiz.question}</h3>
      <div className="mt-3 space-y-2">
        {quiz.choices.map((c, i) => {
          const isCorrect = submitted && i === quiz.answer;
          const isWrong = submitted && selected === i && selected !== quiz.answer;
          return (
            <button
              key={i}
              type="button"
              onClick={() => submit(i)}
              className={`w-full rounded-md border px-3 py-2 text-left transition ${
                isCorrect
                  ? "border-green-600 bg-green-100"
                  : isWrong
                    ? "border-red-500 bg-red-100"
                    : "border-slate-300 bg-white hover:border-slate-400"
              }`}
            >
              {c}
            </button>
          );
        })}
      </div>
      {statusLabel && <p className="mt-3 text-sm font-semibold text-slate-700">{statusLabel}</p>}
    </div>
  );
}
