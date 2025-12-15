export default function TheoryBlock({ title, content }: { title?: string; content?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-[#ededed] px-4 py-3">
      {title && <h3 className="text-lg font-semibold text-slate-900">{title}</h3>}
      <p className="mt-2 whitespace-pre-line text-slate-700">{content || ""}</p>
    </div>
  );
}
