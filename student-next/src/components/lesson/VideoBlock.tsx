export default function VideoBlock({ url }: { url: string }) {
  if (!url) {
    return <div className="h-48 w-full rounded-lg border border-slate-200 bg-[#e0e0e0]" />;
  }
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-[#ededed]">
      <video controls className="w-full" src={url} />
    </div>
  );
}
