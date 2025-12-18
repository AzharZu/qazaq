import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useDictionaryWords } from "@/lib/useDictionaryWords";
import { useDictionaryStore } from "@/store/dictionaryStore";

export default function DictionaryRepeatPage() {
  const { submitResult } = useDictionaryStore();
  const { words: list, loading } = useDictionaryWords();
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<"success" | "error" | null>(null);
  const [revealedWord, setRevealedWord] = useState<string | null>(null);

  const playableWords = useMemo(() => list.filter((w) => !!w.audioUrl), [list]);
  const hasWords = playableWords.length > 0;
  const word = hasWords ? playableWords[index % playableWords.length] : undefined;

  useEffect(() => {
    setIndex(0);
    setAnswer("");
    setResult(null);
    setRevealedWord(null);
  }, [playableWords.length]);

  const next = () => {
    setResult(null);
    setRevealedWord(null);
    setAnswer("");
    if (playableWords.length) setIndex((i) => (i + 1) % playableWords.length);
  };
  const prev = () => {
    setResult(null);
    setRevealedWord(null);
    setAnswer("");
    if (playableWords.length) setIndex((i) => (i - 1 + playableWords.length) % playableWords.length);
  };

  const playAudio = () => {
    if (!word?.audioUrl) {
      next();
      return;
    }
    const audio = new Audio(word.audioUrl);
    audio.play().catch(() => next());
  };

  const check = async () => {
    if (!word?.audioUrl) {
      next();
      return;
    }
    const userAnswer = answer.trim();
    if (!userAnswer) return;
    const ok = userAnswer.toLowerCase() === (word.wordKz || "").trim().toLowerCase();
    setResult(ok ? "success" : "error");
    setRevealedWord(ok ? null : word.wordKz);
    await submitResult(Number(word.id), "repeat", ok);
  };

  return (
    <div className="min-h-screen bg-slate-900 px-4 py-6 text-white md:px-8 md:py-10">
      <div className="mx-auto flex max-w-5xl flex-col gap-6">
        <Link
          href="/dictionary"
          className="inline-flex w-fit items-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
        >
          ← К словарю
        </Link>
        <h1 className="text-center text-3xl font-bold md:text-4xl">Мини-игры словаря — Повтори слово</h1>

        <div className="flex flex-col gap-6 rounded-3xl bg-slate-800 px-4 py-8 shadow-2xl md:px-10">
          {loading ? (
            <div className="text-center text-slate-300">Загружаем слова...</div>
          ) : !hasWords ? (
            <div className="text-center text-slate-300">Нет слов с аудио для тренировки. Пройдите урок с карточками.</div>
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
                  <p className="text-sm text-slate-300">Слушайте аудио и введите услышанное слово</p>
                  <div className="mt-6 flex flex-col items-center gap-3">
                    <button
                      type="button"
                      onClick={playAudio}
                      className="w-full max-w-xs rounded-xl bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-100 shadow-inner transition hover:bg-slate-700"
                    >
                      Озвучить
                    </button>
                    <input
                      value={answer}
                      onChange={(e) => {
                        setAnswer(e.target.value);
                        setResult(null);
                        setRevealedWord(null);
                      }}
                      placeholder="Введите услышанное слово"
                      className="w-full max-w-xs rounded-xl bg-slate-800 px-4 py-3 text-center text-white outline-none ring-amber-400/40 focus:ring"
                    />
                    <button
                      type="button"
                      onClick={check}
                      className="w-full max-w-xs rounded-xl bg-amber-400 px-4 py-2 text-sm font-semibold text-slate-900 shadow-lg transition hover:bg-amber-300"
                    >
                      Проверить
                    </button>
                    {result && (
                      <div
                        className={`w-full max-w-xs rounded-lg px-4 py-2 text-sm ${
                          result === "success" ? "bg-emerald-900/70 text-emerald-100" : "bg-rose-900/70 text-rose-100"
                        }`}
                      >
                        {result === "success" ? "Верно! Продолжай." : "Проверьте написание и попробуйте снова."}
                        {result === "error" ? (
                          <p className="mt-1 text-xs text-rose-100/80">Правильный ответ: {revealedWord || word?.wordKz}</p>
                        ) : null}
                      </div>
                    )}
                    {result ? (
                      <button
                        type="button"
                        onClick={next}
                        className="w-full max-w-xs rounded-xl bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-100 shadow-inner transition hover:bg-slate-700"
                      >
                        Дальше
                      </button>
                    ) : null}
                  </div>
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
