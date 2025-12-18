import { useMemo, useState } from "react";
import { buildYouTubeEmbedUrl } from "@/lib/video";

type Props = {
  videoId: string;
  className?: string;
  title?: string;
};

export default function YouTubeEmbed({ videoId, className = "", title = "YouTube video player" }: Props) {
  const [hasError, setHasError] = useState(false);

  const embedUrl = useMemo(() => buildYouTubeEmbedUrl(videoId), [videoId]);

  if (hasError) {
    return (
      <div className={`relative aspect-video w-full overflow-hidden rounded-xl bg-midnight ${className}`}>
        <div className="flex h-full items-center justify-center px-4 text-center text-sm text-ink/70">
          Видео не загрузилось. Проверьте ссылку или попробуйте обновить страницу.
        </div>
      </div>
    );
  }

  return (
    <div className={`relative aspect-video w-full overflow-hidden rounded-xl bg-midnight ${className}`}>
      <iframe
        key={embedUrl}
        title={title}
        src={embedUrl}
        className="absolute inset-0 h-full w-full"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        allowFullScreen
        referrerPolicy="strict-origin-when-cross-origin"
        onError={() => setHasError(true)}
      />
    </div>
  );
}
