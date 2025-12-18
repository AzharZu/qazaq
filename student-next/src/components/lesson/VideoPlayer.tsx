import YouTubeEmbed from "../YouTubeEmbed";
import { extractYouTubeId, isDirectVideoUrl } from "@/lib/video";

type Props = {
  url?: string | null;
  poster?: string | null;
  className?: string;
};

export default function VideoPlayer({ url, poster, className = "" }: Props) {
  const videoUrl = typeof url === "string" ? url.trim() : "";
  const youtubeId = extractYouTubeId(videoUrl);
  const isDirect = isDirectVideoUrl(videoUrl);
  const looksLikeYouTube = /youtu(\.be)?|youtube/i.test(videoUrl);
  const wrapperClass = `relative aspect-video w-full overflow-hidden rounded-xl bg-midnight ${className}`.trim();

  if (!videoUrl) {
    return <div className={wrapperClass} />;
  }

  if (youtubeId) {
    return <YouTubeEmbed videoId={youtubeId} className={className} />;
  }

  if (isDirect) {
    return (
      <div className={wrapperClass}>
        <video src={videoUrl} poster={typeof poster === "string" ? poster : undefined} controls className="h-full w-full bg-black" />
      </div>
    );
  }

  if (looksLikeYouTube) {
    return (
      <div className={wrapperClass}>
        <div className="flex h-full items-center justify-center px-4 text-center text-sm text-ink/80">
          Не удалось распознать ссылку YouTube. Проверьте URL или вставьте стандартную ссылку вида
          {" https://www.youtube.com/watch?v=ID"}.
        </div>
      </div>
    );
  }

  return (
    <div className={wrapperClass}>
      <div className="flex h-full items-center justify-center px-4 text-center text-sm text-ink/70">
        Ссылка на видео должна быть YouTube или прямой mp4/webm.
      </div>
    </div>
  );
}
