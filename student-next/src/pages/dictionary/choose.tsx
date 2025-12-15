import Link from "next/link";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";
import { useDictionaryWords } from "@/lib/useDictionaryWords";
import { useDictionaryStore } from "@/store/dictionaryStore";

export default function DictionaryChoosePage() {
  const router = useRouter();
  const lessonId = router.query.lessonId as string | undefined;
  const { submitResult } = useDictionaryStore();
  const { words: list, loading } = useDictionaryWords({ lessonId });
  const [index, setIndex] = useState(0);
  const [choice, setChoice] = useState<string | null>(null);
  const [result, setResult] = useState<"success" | "error" | null>(null);

  const hasWords = list.length > 0;
  const word = hasWords ? list[index % list.length] : undefined;

  const options = useMemo(() => {
    if (!word || !list.length) return [];
    const translations = list.map((w) => w.translationRu);
    const unique = translations.filter((val, idx) => translations.indexOf(val) === idx);
    const currentIdx = unique.indexOf(word.translationRu);
    const variants: string[] = [];
    for (let i = 1; variants.length < 3; i++) {
      variants.push(unique[(currentIdx + i) % unique.length]);
    }
    return [...variants, word.translationRu];
  }, [word, list]);

  const next = () => {
    setResult(null);
    setChoice(null);
    if (list.length) setIndex((i) => (i + 1) % list.length);
  };
  const prev = () => {
    setResult(null);
    setChoice(null);
    if (list.length) setIndex((i) => (i - 1 + list.length) % list.length);
  };

  const check = async (value: string) => {
    setChoice(value);
    if (!word) return;
    const ok = value === word.translationRu;
    setResult(ok ? "success" : "error");
    await submitResult(Number(word.id), "mc", ok);
  };

  return (
    <div className="min-h-screen bg-slate-900 px-4 py-6 text-white md:px-8 md:py-10">
      <div className="mx-auto flex max-w-5xl flex-col gap-6">
        <Link href="/dictionary" className="inline-flex w-fit items-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700">
          ← К словарю
        </Link>
        <h1 className="text-center text-3xl font-bold md:text-4xl">Мини-игры словаря — Выбери перевод</h1>

        <div className="flex flex-col gap-6 rounded-3xl bg-slate-800 px-4 py-8 shadow-2xl md:px-10">
          {loading ? (
            <div className="text-center text-slate-300">Загружаем слова...</div>
          ) : !hasWords ? (
            <div className="text-center text-slate-300">Нет слов для тренировки. Пройдите урок с карточками.</div>
          ) : (
            <div className="flex items-center justify-between gap-4">
              <button
                type="button"
                onClick={prev}
                className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-400 text-slate-900 shadow-lg transition hover:bg-amber-300"
              >
                ←
              </button>
              <div className="flex-1 px-4">
                <div className="mx-auto max-w-xl rounded-2xl bg-slate-900 px-6 py-8 text-center shadow-inner">
                  <p className="text-sm text-slate-300">Слово</p>
                  <div className="mt-2 text-4xl font-extrabold text-amber-300 md:text-5xl">{word?.wordKz}</div>
                  <div className="mt-6 grid grid-cols-2 gap-3">
                    {options.map((opt) => (
                      <button
                        key={opt + index}
                        type="button"
                        onClick={() => check(opt)}
                        className={`rounded-xl px-4 py-3 text-sm font-semibold shadow-inner transition ${
                          choice === opt
                            ? opt === word?.translationRu
                              ? "bg-emerald-700 text-white"
                              : "bg-rose-700 text-white"
                            : "bg-slate-800 text-slate-100 hover:bg-slate-700"
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                  {result && (
                    <div
                      className={`mt-4 rounded-lg px-4 py-2 text-sm ${
                        result === "success" ? "bg-emerald-900/70 text-emerald-100" : "bg-rose-900/70 text-rose-100"
                      }`}
                    >
                      {result === "success" ? "Правильно!" : "Неверно, попробуйте снова."}
                    </div>
                  )}
                </div>
              </div>
              <button
                type="button"
                onClick={next}
                className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-400 text-slate-900 shadow-lg transition hover:bg-amber-300"
              >
                →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
