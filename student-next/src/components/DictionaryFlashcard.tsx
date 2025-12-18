/* eslint-disable @next/next/no-img-element */
import { useMemo, useState } from "react";
import { DictionaryWord } from "@/lib/api/dictionary";
import { resolveMediaUrl } from "@/lib/media";

type Props = {
  word: DictionaryWord;
  index: number;
  total: number;
  onPrev: () => void;
  onNext: () => void;
  onSuccess: () => void;
  onFail: () => void;
};

export default function DictionaryFlashcard({ word, index, total, onPrev, onNext, onSuccess, onFail }: Props) {
  const [showBack, setShowBack] = useState(false);

  const progressText = useMemo(() => {
    const success = word.progress?.success || 0;
    const fails = word.progress?.fails || 0;
    return `Знаю: ${success} • Повтор: ${fails}`;
  }, [word.progress]);

  const playAudio = () => {
    const src = resolveMediaUrl(word.audio_path || word.audio_url);
    if (src) {
      const audio = new Audio(src);
      audio.play().catch((err) => console.warn("audio play error", err));
    } else if (typeof window !== "undefined") {
      const utter = new SpeechSynthesisUtterance(word.word);
      utter.lang = "kk-KZ";
      window.speechSynthesis?.speak(utter);
    }
  };

  return (
    <div className="space-y-4 rounded-xl bg-gray-100 p-6 shadow-sm">
      <div className="flex items-center justify-between text-sm text-gray-700">
        <span className="font-semibold text-gray-800">Слово {index + 1} / {total}</span>
        <span>{progressText}</span>
      </div>

      <div className="flex flex-col gap-4 rounded-xl bg-white p-6 shadow-sm transition">
        {!showBack ? (
          <div className="space-y-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-wide text-blue-600">Лицевая сторона</p>
                <h3 className="text-3xl font-semibold text-gray-900">{word.word}</h3>
              </div>
              <button
                type="button"
                onClick={playAudio}
                className="rounded-full bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
              >
                🔊
              </button>
            </div>
            {word.image_url && (
              <div className="overflow-hidden rounded-lg border border-gray-200">
                <img src={word.image_url} alt={word.word} className="h-48 w-full object-cover" />
              </div>
            )}
            {word.example_sentence && <p className="text-sm text-gray-700">{word.example_sentence}</p>}
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-xs uppercase tracking-wide text-blue-600">Перевод</p>
            <div className="rounded-lg bg-gray-100 px-4 py-6 text-2xl font-semibold text-gray-900">{word.translation}</div>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={onSuccess}
                className="rounded-lg bg-green-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-green-700"
              >
                👍 Знаю
              </button>
              <button
                type="button"
                onClick={onFail}
                className="rounded-lg bg-red-500 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-red-600"
              >
                👎 Нужно повторить
              </button>
            </div>
          </div>
        )}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setShowBack((v) => !v)}
            className="rounded-lg bg-gray-200 px-4 py-2 text-sm font-semibold text-gray-800 transition hover:bg-gray-300"
          >
            {showBack ? "Показать слово" : "Показать перевод"}
          </button>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onPrev}
              className="rounded-full bg-gray-200 px-3 py-2 text-sm font-semibold text-gray-800 shadow-sm transition hover:bg-gray-300"
            >
              ←
            </button>
            <button
              type="button"
              onClick={() => {
                if (showBack) {
                  onSuccess();
                } else {
                  setShowBack(true);
                }
              }}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700"
            >
              Следующее
            </button>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm text-gray-700">
        <button
          type="button"
          onClick={onPrev}
          className="rounded-full bg-gray-200 px-4 py-2 font-semibold text-gray-800 shadow-sm transition hover:bg-gray-300"
        >
          ← Prev
        </button>
        <button
          type="button"
          onClick={onNext}
          className="rounded-full bg-gray-200 px-4 py-2 font-semibold text-gray-800 shadow-sm transition hover:bg-gray-300"
        >
          Next →
        </button>
      </div>
    </div>
  );
}
