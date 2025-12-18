import VideoPlayer from "./VideoPlayer";

export default function VideoBlock({ url }: { url: string }) {
  return <VideoPlayer url={url} className="border border-slate/30" />;
}
