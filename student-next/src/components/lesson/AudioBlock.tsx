export default function AudioBlock({ url, transcript }: { url: string; transcript?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-[#ededed] p-4">
      <audio controls className="w-full">
        <source src={url} />
      </audio>
      {transcript && <p className="mt-2 text-sm text-slate-700">{transcript}</p>}
    </div>
  );
}
