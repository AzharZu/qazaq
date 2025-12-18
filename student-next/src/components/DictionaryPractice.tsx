import { FormEvent, useEffect, useMemo, useState } from "react";
import PronunciationRecorder from "./PronunciationRecorder";
import { useDictionaryStore } from "@/store/dictionaryStore";

type Phase = "choose" | "pronounce" | "write";

export default function DictionaryPractice() {
  const { words, loadWords, getNextWordIndex, setCurrentIndex, currentIndex, markSuccess, markFail } = useDictionaryStore();
  const [phase, setPhase] = useState<Phase>("choose");
  const [selected, setSelected] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [pronunciationScore, setPronunciationScore] = useState<number | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!loaded && words.length === 0) {
      loadWords().then(() => setLoaded(true));
    }
  }, []); // eslint-disable-next-line react-hooks/exhaustive-deps

  const word = words[currentIndex];

  const options = useMemo(() => {
    if (!word || !words.length) return [];
    const others = words.filter((w) => w.id !== word.id);
    const shuffled = others.sort(() => 0.5 - Math.random()).slice(0, 3).map((w) => w.translation);
    const all = [...shuffled, word.translation];
    return all.sort(() => 0.5 - Math.random());
  }, [word, words]);

  const goNextWord = () => {
    if (!words.length) return;
    const nextIdx = getNextWordIndex();
    setCurrentIndex(nextIdx);
    setPhase("choose");
    setSelected(null);
    setFeedback(null);
    setInput("");
    setPronunciationScore(null);
  };

  const handleChoose = (option: string) => {
    if (!word) return;
    setSelected(option);
    if (option === word.translation) {
      setFeedback("Верно!");
      setTimeout(() => setPhase("pronounce"), 500);
    } else {
      setFeedback("Неверно, попробуйте еще.");
      markFail(word.id);
      setTimeout(() => goNextWord(), 700);
    }
  };

  const handlePronunciation = (score: number, status: "excellent" | "good" | "bad") => {
    setPronunciationScore(score);
    if (status === "excellent") {
      setFeedback("Отлично! Произнесено верно.");
      setTimeout(() => setPhase("write"), 400);
    } else if (status === "good") {
      setFeedback("Неплохо, попробуйте еще раз для улучшения.");
    } else {
      setFeedback("Произнесите чётче, чтобы продолжить.");
    }
  };

  const handleWrite = (e: FormEvent) => {
    e.preventDefault();
    if (!word) return;
    if (input.trim().toLowerCase() === (word.word || "").trim().toLowerCase()) {
      setFeedback("Правильно!");
      markSuccess(word.id);
      setTimeout(() => goNextWord(), 600);
    } else {
      setFeedback("Ошибка. Попробуйте снова.");
      markFail(word.id);
    }
  };

  if (!word) {
    return <div className="rounded-xl bg-white p-6 text-gray-700 shadow-sm">Нет слов для тренировки. Добавьте слова в уроках.</div>;
  }

  return (
    <div className="space-y-6 rounded-2xl bg-white p-8 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">Практика</p>
          <h2 className="text-2xl font-semibold text-gray-900">Быстрая тренировка слов</h2>
        </div>
        <span className="rounded-full bg-gray-100 px-4 py-2 text-sm font-semibold text-gray-800">
          {currentIndex + 1} / {words.length}
        </span>
      </div>

      <div className="space-y-6">
        {phase === "choose" && (
          <div className="space-y-4 rounded-xl bg-gray-100 p-6 shadow-sm">
            <p className="text-sm font-semibold text-blue-600">Мини-игра: Выберите перевод</p>
            <p className="text-3xl font-semibold text-gray-900">{word.word}</p>
            <div className="grid gap-3 md:grid-cols-2">
              {options.map((opt) => {
                const isCorrect = selected === opt && opt === word.translation;
                const isWrong = selected === opt && opt !== word.translation;
                return (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => handleChoose(opt)}
                    className={`rounded-lg px-4 py-3 text-left text-sm font-semibold shadow-sm transition ${
                      isCorrect
                        ? "bg-green-100 text-green-800"
                        : isWrong
                        ? "bg-red-100 text-red-800"
                        : "bg-white text-gray-800 hover:bg-gray-200"
                    }`}
                  >
                    {opt}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {phase === "pronounce" && (
          <div className="space-y-4 rounded-xl bg-gray-100 p-6 shadow-sm">
            <p className="text-sm font-semibold text-blue-600">Мини-игра: Произнесите слово</p>
            <p className="text-3xl font-semibold text-gray-900">{word.word}</p>
            <PronunciationRecorder wordId={word.id} word={word.word} onResult={handlePronunciation} />
            {pronunciationScore !== null && (
              <p className="text-sm text-gray-700">
                Совпадение: <span className="font-semibold text-gray-900">{Math.round(pronunciationScore * 100)}%</span>
              </p>
            )}
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setPhase("write")}
                disabled={(pronunciationScore || 0) <= 0.75}
                className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
              >
                Далее
              </button>
            </div>
          </div>
        )}

        {phase === "write" && (
          <div className="space-y-4 rounded-xl bg-gray-100 p-6 shadow-sm">
            <p className="text-sm font-semibold text-blue-600">Мини-игра: Напишите слово</p>
            <p className="text-lg text-gray-800">
              Перевод: <span className="font-semibold text-gray-900">{word.translation}</span>
            </p>
            <form onSubmit={handleWrite} className="space-y-3">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-3 text-base text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none"
                placeholder="Введите слово на казахском"
              />
              <div className="flex justify-between">
                <button
                  type="button"
                  onClick={goNextWord}
                  className="rounded-lg bg-gray-200 px-4 py-2 text-sm font-semibold text-gray-800 transition hover:bg-gray-300"
                >
                  Пропустить
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
                >
                  Проверить
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

      {feedback && <div className="rounded-lg bg-gray-100 px-4 py-3 text-sm text-gray-800">{feedback}</div>}

      <div className="flex justify-end">
        <button
          type="button"
          onClick={goNextWord}
          className="rounded-lg bg-gray-200 px-4 py-2 text-sm font-semibold text-gray-800 transition hover:bg-gray-300"
        >
          Следующее слово →
        </button>
      </div>
    </div>
  );
}
