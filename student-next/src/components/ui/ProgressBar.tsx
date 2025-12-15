type Props = {
  value: number;
  label?: string;
};

export function ProgressBar({ value, label }: Props) {
  const safe = Math.min(Math.max(value || 0, 0), 100);
  return (
    <div className="w-full space-y-1">
      {label && <p className="text-xs text-slate-600">{label}</p>}
      <div className="h-3 w-full rounded-full bg-[#e5e5e5]">
        <div className="h-3 rounded-full bg-slate-900 transition-[width] duration-300" style={{ width: `${safe}%` }} />
      </div>
    </div>
  );
}

export default ProgressBar;
