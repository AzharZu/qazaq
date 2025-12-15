export default function ImageBlock({ url, caption }: { url: string; caption?: string }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-[#ededed]">
      {url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={url} alt={caption || "image"} className="w-full object-cover" />
      ) : (
        <div className="h-40 w-full bg-[#dcdcdc]" />
      )}
      {caption && <p className="px-4 py-2 text-sm text-slate-700">{caption}</p>}
    </div>
  );
}
