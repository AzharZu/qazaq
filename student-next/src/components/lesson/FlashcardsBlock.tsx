import { useState } from "react";

type Card = { word?: string; translation: string; example_sentence?: string };

export default function FlashcardsBlock({ cards }: { cards: Card[] }) {
  const [current, setCurrent] = useState(0);
  const [flipped, setFlipped] = useState(false);

  const card = cards[current];
  if (!card) return null;

  const next = () => {
    setCurrent((c) => Math.min(cards.length - 1, c + 1));
    setFlipped(false);
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-[#ededed] p-4">
      <div
        className="flex min-h-[150px] cursor-pointer flex-col justify-center rounded-md border border-dashed border-slate-300 bg-white p-4 text-center"
        onClick={() => setFlipped((f) => !f)}
      >
        <p className="text-xl font-bold">{flipped ? card.translation : card.word}</p>
        {card.example_sentence && <p className="mt-2 text-sm text-slate-600">{card.example_sentence}</p>}
        <p className="mt-3 text-xs text-slate-500">Нажмите, чтобы перевернуть</p>
      </div>
      <div className="mt-3 flex gap-2">
        <button className="flex-1 rounded-md bg-slate-900 px-3 py-2 text-white" onClick={next}>
          Далее
        </button>
        <button className="flex-1 rounded-md bg-[#dcdcdc] px-3 py-2" onClick={() => setFlipped((f) => !f)}>
          Перевернуть
        </button>
      </div>
      <p className="mt-2 text-center text-xs text-slate-600">
        Карта {current + 1} / {cards.length}
      </p>
    </div>
  );
}
