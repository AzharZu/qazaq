/* eslint-disable @next/next/no-img-element */
import { useEffect, useRef, useState } from "react";
import client from "@/lib/api/client";
import { Flashcard as FlashcardType } from "@/types/lesson";
import { resolveMediaUrl } from "@/lib/media";

type FlashcardProps = {
  cards: FlashcardType[];
  onComplete?: () => void;
  title?: string;
  ctaLabel?: string;
  onCta?: () => void;
};

export default function Flashcard({ cards, onComplete, title, ctaLabel, onCta }: FlashcardProps) {
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const touchStartX = useRef<number | null>(null);

  const card = cards[index];

  useEffect(() => {
    setIndex(0);
    setFlipped(false);
  }, [cards]);

  const speak = () => {
    if (!card) return;
    const src = resolveMediaUrl(card.audio_path || card.audio_url);
    if (src) {
      const audio = new Audio(src);
      audio.play().catch(() => {
        const text = flipped ? card.translation || card.back || "" : card.word || card.front || "";
        if (typeof window !== "undefined" && text) {
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.lang = "kk-KZ";
          window.speechSynthesis?.speak(utterance);
        }
      });
      return;
    }
    const text = flipped ? card.translation || card.back || "" : card.word || card.front || "";
    if (typeof window === "undefined" || !text) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "kk-KZ";
    window.speechSynthesis?.speak(utterance);
  };

  const prev = () => {
    setFlipped(false);
    setIndex((prevIdx) => Math.max(prevIdx - 1, 0));
  };
  const next = () => {
    if (index + 1 >= cards.length) {
      onComplete?.();
    } else {
      setFlipped(false);
      setIndex((prevIdx) => Math.min(prevIdx + 1, cards.length - 1));
    }
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };
  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX.current === null) return;
    const diff = e.changedTouches[0].clientX - touchStartX.current;
    if (Math.abs(diff) > 40) {
      diff > 0 ? prev() : next();
    }
    touchStartX.current = null;
  };

  if (!cards.length) {
    return <div className="rounded-xl bg-panel p-6 text-ink shadow-card">Нет карточек</div>;
  }

  return (
    <div className="space-y-6 rounded-2xl bg-panel p-6 shadow-card">
      {title && <h3 className="text-2xl font-semibold text-white">{title}</h3>}

      <div className="rounded-3xl bg-midnight p-4 shadow-inner">
        <div className="relative flex items-center gap-3">
          <button
            onClick={prev}
            disabled={index === 0}
            className="absolute left-0 z-10 flex h-12 w-12 items-center justify-center rounded-full bg-gold text-slateDeep shadow-soft transition hover:bg-goldDark disabled:cursor-not-allowed disabled:opacity-50"
            type="button"
          >
            ←
          </button>

          <div
            className="mx-auto flex w-full max-w-4xl cursor-pointer items-center justify-between gap-6 rounded-2xl bg-slateDeep/50 px-10 py-12 text-left shadow-card transition hover:bg-slateDeep/60"
            onClick={() => setFlipped((f) => !f)}
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
            role="button"
            tabIndex={0}
          >
            <div className="flex-1">
              <p className="text-sm uppercase tracking-wide text-gold">{flipped ? "Перевод" : "Слово"}</p>
              <p className="mt-2 text-4xl font-bold text-gold">{flipped ? card.translation || card.back : card.word || card.front}</p>
              {flipped ? (
                card.example_sentence ? (
                  <p className="mt-4 text-base text-ink/80">{card.example_sentence}</p>
                ) : null
              ) : (
                <p className="mt-4 text-sm text-ink/60">Нажмите, чтобы увидеть перевод</p>
              )}
            </div>
            {card.image_url && (
              <div className="h-40 w-40 shrink-0 overflow-hidden rounded-xl border border-slate/40 bg-slate/30">
                <img src={card.image_url} alt={card.word || "flashcard"} className="h-full w-full object-cover" />
              </div>
            )}
          </div>

          <button
            onClick={next}
            className="absolute right-0 z-10 flex h-12 w-12 items-center justify-center rounded-full bg-gold text-slateDeep shadow-soft transition hover:bg-goldDark"
            type="button"
          >
            →
          </button>
        </div>
        <div className="mt-4 flex items-center justify-between text-sm text-ink/80">
          <span>
            {index + 1} / {cards.length}
          </span>
          <div className="flex gap-3">
            <button
              onClick={speak}
              className="rounded-lg bg-slate px-3 py-2 text-xs font-semibold text-ink shadow-soft transition hover:bg-slateDeep hover:text-white"
              type="button"
            >
              Озвучить
            </button>
          </div>
        </div>
      </div>

      {ctaLabel && onCta && (
        <div className="flex justify-end">
          <button
            onClick={onCta}
            className="rounded-xl bg-gold px-5 py-3 text-sm font-semibold text-slateDeep shadow-soft transition hover:bg-goldDark"
            type="button"
          >
            {ctaLabel}
          </button>
        </div>
      )}
    </div>
  );
}
