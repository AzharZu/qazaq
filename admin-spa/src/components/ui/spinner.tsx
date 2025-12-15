export function Spinner() {
  return (
    <svg
      className="h-4 w-4 animate-spin text-slate-500"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <circle cx="12" cy="12" r="9" strokeOpacity="0.2" />
      <path d="M21 12a9 9 0 0 1-9 9" />
    </svg>
  );
}
