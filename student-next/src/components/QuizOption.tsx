type QuizOptionProps = {
  index: number;
  label: string;
  onSelect: () => void;
  selected?: boolean;
  disabled?: boolean;
};

export default function QuizOption({ index, label, onSelect, selected, disabled }: QuizOptionProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={disabled}
      className={`flex w-full items-start gap-3 rounded-xl px-4 py-3 text-left shadow-soft transition ${
        selected ? "bg-gold text-slateDeep" : "bg-slate/60 text-ink hover:bg-slate"
      } ${disabled ? "cursor-not-allowed opacity-80" : ""}`}
    >
      <span className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-full bg-slate text-sm font-semibold text-ink">
        {index + 1}
      </span>
      <span className="text-base">{label}</span>
    </button>
  );
}
