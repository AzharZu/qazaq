import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { playDictionaryAudio, useDictionaryWords } from "@/lib/useDictionaryWords";

export default function DictionaryPage() {
  const router = useRouter();
  const lessonId = router.query.lessonId as string | undefined;
  const { words: list, loading } = useDictionaryWords({ lessonId });
  const [showTranslation, setShowTranslation] = useState(false);
  const [learned, setLearned] = useState<Set<string | number>>(new Set());
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const saved = localStorage.getItem("dict_learned_ids");
    if (saved) setLearned(new Set(JSON.parse(saved)));
  }, []);

  useEffect(() => {
    setIndex(0);
    setShowTranslation(false);
  }, [lessonId, list.length]);

  const hasWords = list.length > 0;
  const word = hasWords ? list[index % list.length] : undefined;

  const toggleLearned = () => {
    if (!word) return;
    const next = new Set(learned);
    if (next.has(word.id)) next.delete(word.id);
    else next.add(word.id);
    setLearned(next);
    localStorage.setItem("dict_learned_ids", JSON.stringify(Array.from(next)));
  };

  const next = () => {
    if (!list.length) return;
    setShowTranslation(false);
    setIndex((i) => (i + 1) % list.length);
  };
  const prev = () => {
    if (!list.length) return;
    setShowTranslation(false);
    setIndex((i) => (i - 1 + list.length) % list.length);
  };

  return (
    <div className="space-y-8 bg-slate-900 px-4 py-8 text-white md:px-8 md:py-10">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold md:text-4xl">Интерактивный словарь</h1>
        <p className="text-sm text-ink/70 text-slate-200">Повторяйте слова, слушайте произношение и закрепляйте лексику через мини-упражнения.</p>
      </div>

      <div className="mx-auto flex max-w-5xl flex-col items-center gap-4 rounded-3xl bg-slate-800 px-6 py-8 shadow-2xl md:px-10 md:py-10">
        {loading ? (
          <div className="text-slate-300">Загружаем словарь...</div>
        ) : hasWords ? (
          <>
            <div className="flex w-full items-center justify-between">
              <button
                type="button"
                onClick={prev}
                className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-400 text-slate-900 shadow-lg transition hover:bg-amber-300"
              >
                ←
              </button>
              <div className="flex-1 px-6">
                <div className="mx-auto max-w-xl rounded-2xl bg-slate-900 px-6 py-8 text-center shadow-inner">
                  <p className="text-sm text-slate-300">Слово</p>
                  <div
                    className="mt-2 cursor-pointer text-4xl font-extrabold text-amber-300 md:text-5xl"
                    onClick={() => setShowTranslation((v) => !v)}
                  >
                    {showTranslation ? word?.translationRu : word?.wordKz}
                  </div>
                  <div className="mt-2 text-xs uppercase tracking-wide text-slate-400">
                    {showTranslation ? "КЛИКНИТЕ, ЧТОБЫ ВЕРНУТЬСЯ К СЛОВУ" : "НАЖМИТЕ, ЧТОБЫ УВИДЕТЬ ПЕРЕВОД"}
                  </div>
                  <div className="mt-3 text-sm text-slate-300">{showTranslation && word?.exampleRu ? word.exampleRu : null}</div>
                  <div className="mt-4 flex flex-wrap justify-center gap-3">
                    <button
                      type="button"
                      onClick={() => playDictionaryAudio(word)}
                      className="rounded-xl bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-100 shadow-inner transition hover:bg-slate-700"
                    >
                      Озвучить
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowTranslation((v) => !v)}
                      className="rounded-xl bg-amber-400 px-4 py-2 text-sm font-semibold text-slate-900 shadow-lg transition hover:bg-amber-300"
                    >
                      {showTranslation ? "Показать слово" : "Показать перевод"}
                    </button>
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
            <label className="flex items-center gap-2 text-xs text-slate-200">
              <input type="checkbox" checked={word ? learned.has(word.id) : false} onChange={toggleLearned} className="h-4 w-4" />
              Я выучил слово
            </label>
          </>
        ) : (
          <div className="text-center text-slate-300">
            Словарь пока пуст. Пройдите урок с карточками, чтобы слова появились автоматически.
          </div>
        )}
      </div>

      <div className="mx-auto flex max-w-5xl flex-col gap-4">
        <h2 className="text-xl font-semibold">Закрепим слова</h2>
        <div className="grid gap-3 md:grid-cols-3">
          {[
            { href: "/dictionary/repeat", title: "Повтори слово", desc: "Прослушай слово и введи его вручную." },
            { href: "/dictionary/choose", title: "Выбери перевод", desc: "Выбери правильный перевод слова." },
            { href: "/dictionary/write", title: "Напиши перевод", desc: "Введи перевод слова вручную." },
          ].map((item) => (
            <Link
              key={item.href}
              href={lessonId ? `${item.href}?lessonId=${lessonId}` : item.href}
              className="rounded-2xl bg-slate-800 px-4 py-4 shadow-lg transition hover:-translate-y-1 hover:bg-slate-700"
            >
              <div className="text-lg font-semibold text-amber-300">{item.title}</div>
              <div className="mt-2 text-sm text-slate-200">{item.desc}</div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
