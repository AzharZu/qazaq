type ProgressBarProps = {
  value: number;
  label?: string;
};

export default function ProgressBar({ value, label }: ProgressBarProps) {
  const safeValue = Math.max(0, Math.min(100, Math.round(value)));
  return (
    <div className="space-y-2">
      {label && <div className="text-sm font-semibold text-ink/80">{label}</div>}
      <div className="flex h-4 w-full items-center rounded-full bg-slate/50 shadow-inner">
        <div
          className="h-4 rounded-full bg-gradient-to-r from-gold to-goldDark transition-all shadow-soft"
          style={{ width: `${safeValue}%` }}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={safeValue}
        />
      </div>
      <div className="text-xs font-semibold text-ink/70">{safeValue}%</div>
    </div>
  );
}
