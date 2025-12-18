import { useMemo, useState } from "react";
import { resolveMediaUrl } from "@/lib/media";

type Question = {
  question: string;
  type: string;
  options?: string[];
  correct_answer?: string | number | (string | number)[];
  audio_path?: string;
  audio_url?: string;
  placeholder?: string;
};

export default function LessonTestBlock({ questions }: { questions: Question[] }) {
  const [answers, setAnswers] = useState<Record<number, any>>({});
  const [aiResult, setAiResult] = useState<string>("");

  const items = useMemo(() => questions || [], [questions]);

  const setAnswer = (idx: number, value: any) => {
    setAnswers((prev) => ({ ...prev, [idx]: value }));
  };

  return (
    <div className="space-y-6 rounded-lg bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <h3 className="text-xl font-semibold text-slate-900">Задания</h3>
      {items.map((q, idx) => {
        const type = (q.type || "single").toLowerCase();
        return (
          <div key={idx} className="space-y-3">
            <div className="text-base font-semibold text-slate-900">
              {idx + 1}. {q.question}
            </div>
            {type === "audio_repeat" ? (
              <div className="space-y-2">
                <button
                  type="button"
                  onClick={() => {
                    const src = resolveMediaUrl(q.audio_path || q.audio_url);
                    if (src) new Audio(src).play();
                  }}
                  className="flex items-center gap-2 rounded bg-gray-200 px-3 py-2 text-sm font-semibold text-gray-800"
                >
                  ▶ Прослушать
                </button>
                <textarea
                  className="w-full rounded border border-slate-200 bg-gray-100 p-3 text-sm"
                  placeholder="Ваше произношение (заметка для себя)"
                  onChange={(e) => setAnswer(idx, e.target.value)}
                />
              </div>
            ) : null}
            {type === "single" || type === "multiple" ? (
              <div className="space-y-2">
                {(q.options || []).map((opt, optIdx) => (
                  <label
                    key={optIdx}
                    className="flex cursor-pointer items-center gap-3 rounded bg-gray-200 px-3 py-2 text-sm font-semibold text-gray-800"
                  >
                    <input
                      type={type === "multiple" ? "checkbox" : "radio"}
                      name={`q-${idx}`}
                      value={optIdx}
                      checked={
                        type === "multiple"
                          ? Array.isArray(answers[idx]) && answers[idx].includes(optIdx)
                          : answers[idx] === optIdx
                      }
                      onChange={(e) => {
                        if (type === "multiple") {
                          const prev = Array.isArray(answers[idx]) ? answers[idx] : [];
                          const val = Number(e.target.value);
                          if (prev.includes(val)) setAnswer(idx, prev.filter((v) => v !== val));
                          else setAnswer(idx, [...prev, val]);
                        } else {
                          setAnswer(idx, Number(e.target.value));
                        }
                      }}
                    />
                    <span>{opt}</span>
                  </label>
                ))}
              </div>
            ) : null}
            {type === "fill-in" ? (
              <input
                className="w-full rounded border border-slate-200 bg-gray-100 p-3 text-sm"
                placeholder={q.placeholder || "Введите ответ"}
                onChange={(e) => setAnswer(idx, e.target.value)}
              />
            ) : null}
            {type === "open" ? (
              <div className="space-y-2">
                <textarea
                  className="w-full rounded border border-slate-200 bg-gray-100 p-3 text-sm"
                  placeholder={q.placeholder || "Введите текст..."}
                  onChange={(e) => setAnswer(idx, e.target.value)}
                />
                <button
                  type="button"
                  className="rounded bg-gray-300 px-3 py-2 text-sm font-semibold text-gray-800"
                  onClick={() => setAiResult("AI: Проверьте окончания и согласование в третьем предложении.")}
                >
                  Проверить через ИИ
                </button>
              </div>
            ) : null}
          </div>
        );
      })}

      {aiResult ? (
        <div className="rounded bg-gray-100 p-4 text-sm text-gray-800">
          <div className="font-semibold">Результат проверки ИИ</div>
          <div>{aiResult}</div>
        </div>
      ) : null}

      <div className="flex justify-end">
        <button
          type="button"
          className="rounded bg-gray-300 px-4 py-2 text-sm font-semibold text-gray-800"
          onClick={() => console.log("answers", answers)}
        >
          Завершить
        </button>
      </div>
    </div>
  );
}
