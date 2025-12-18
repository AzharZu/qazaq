import { useState } from "react";
import { resolveMediaUrl } from "@/lib/media";

export default function AudioBlock({ url, transcript }: { url: string; transcript?: string }) {
  const [error, setError] = useState<string | null>(null);
  const src = resolveMediaUrl(url);
  return (
    <div className="rounded-lg border border-slate-200 bg-[#ededed] p-4">
      <audio controls className="w-full" src={src} onError={() => setError("Не удалось загрузить аудио. Проверьте ссылку.")}>
        Ваш браузер не поддерживает аудио.
      </audio>
      {error ? <div className="mt-1 text-xs text-red-500">{error}</div> : null}
      {transcript && <p className="mt-2 text-sm text-slate-700">{transcript}</p>}
    </div>
  );
}
