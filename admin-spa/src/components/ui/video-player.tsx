import { useEffect, useRef } from "react";

type VideoPlayerProps = {
  videoType: string; // youtube, vimeo, file
  videoUrl: string;
  width?: string;
  height?: string;
};

export function VideoPlayer({ videoType, videoUrl, width = "100%", height = "400px" }: VideoPlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !videoUrl) return;

    const container = containerRef.current;
    container.innerHTML = "";

    if (videoType === "youtube") {
      // Extract YouTube video ID from various URL formats
      const youtubeRegex = /(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/;
      const match = videoUrl.match(youtubeRegex);
      const videoId = match ? match[1] : videoUrl;

      const iframe = document.createElement("iframe");
      iframe.width = "100%";
      iframe.height = height;
      iframe.src = `https://www.youtube.com/embed/${videoId}`;
      iframe.frameBorder = "0";
      iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
      iframe.allowFullscreen = true;
      iframe.style.borderRadius = "8px";
      container.appendChild(iframe);
    } else if (videoType === "vimeo") {
      // Extract Vimeo video ID
      const vimeoRegex = /(?:vimeo\.com\/)(\d+)/;
      const match = videoUrl.match(vimeoRegex);
      const videoId = match ? match[1] : videoUrl;

      const iframe = document.createElement("iframe");
      iframe.width = "100%";
      iframe.height = height;
      iframe.src = `https://player.vimeo.com/video/${videoId}`;
      iframe.frameBorder = "0";
      iframe.allow = "autoplay; fullscreen; picture-in-picture";
      iframe.allowFullscreen = true;
      iframe.style.borderRadius = "8px";
      container.appendChild(iframe);
    } else if (videoType === "file") {
      // Self-hosted MP4
      const video = document.createElement("video");
      video.width = parseInt(width);
      video.height = parseInt(height);
      video.src = videoUrl;
      video.controls = true;
      video.style.width = "100%";
      video.style.height = "auto";
      video.style.borderRadius = "8px";
      container.appendChild(video);
    }
  }, [videoType, videoUrl, width, height]);

  if (!videoUrl) {
    return null;
  }

  return (
    <div
      ref={containerRef}
      style={{
        width,
        minHeight: height,
        borderRadius: "8px",
        overflow: "hidden",
        backgroundColor: "#000",
      }}
    />
  );
}
