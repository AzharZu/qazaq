const YOUTUBE_HOSTS = [
  "youtube.com",
  "www.youtube.com",
  "m.youtube.com",
  "music.youtube.com",
  "youtube-nocookie.com",
  "www.youtube-nocookie.com",
];
const YOUTU_BE_HOSTS = ["youtu.be", "www.youtu.be"];

export function extractYouTubeId(url: string | null | undefined): string | null {
  if (!url || typeof url !== "string") return null;
  const trimmed = url.trim();
  if (!trimmed) return null;

  const candidate = trimmed.startsWith("http://") || trimmed.startsWith("https://") ? trimmed : `https://${trimmed}`;

  let parsed: URL;
  try {
    parsed = new URL(candidate);
  } catch {
    return null;
  }

  const hostname = parsed.hostname.toLowerCase();
  const pathnameParts = parsed.pathname.split("/").filter(Boolean);
  const addCandidates: string[] = [];

  if (YOUTU_BE_HOSTS.includes(hostname)) {
    if (pathnameParts[0] === "shorts" && pathnameParts[1]) {
      addCandidates.push(pathnameParts[1]);
    } else if (pathnameParts[0]) {
      addCandidates.push(pathnameParts[0]);
    }
  }

  if (hostname.includes("youtube")) {
    const searchId = parsed.searchParams.get("v") || parsed.searchParams.get("vi");
    if (searchId) addCandidates.push(searchId);

    // Handle /shorts/:id, /live/:id, /embed/:id, /v/:id
    const [first, second] = pathnameParts;
    if (["shorts", "live", "embed", "v", "e"].includes(first || "") && second) {
      addCandidates.push(second);
    }

    // Fallback: sometimes shared links look like /watch/:id
    if (first === "watch" && second) {
      addCandidates.push(second);
    }
  }

  for (const raw of addCandidates) {
    const cleaned = cleanId(raw);
    if (cleaned) return cleaned;
  }

  return null;
}

export function buildYouTubeEmbedUrl(videoId: string): string {
  return `https://www.youtube.com/embed/${videoId}`;
}

export function isDirectVideoUrl(url: string | null | undefined): boolean {
  if (!url || typeof url !== "string") return false;
  const trimmed = url.trim();
  if (!trimmed) return false;

  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    try {
      parsed = new URL(`https://${trimmed}`);
    } catch {
      return false;
    }
  }

  const path = parsed.pathname.toLowerCase();
  return path.endsWith(".mp4") || path.endsWith(".webm");
}

function cleanId(raw: string): string | null {
  const id = raw.split(/[?&#]/)[0];
  return id && id.length >= 6 ? id : null;
}

// Mini sanity check to keep the parsing logic honest.
export const __extractYouTubeIdSamples__ = [
  ["https://www.youtube.com/watch?v=abc123XYZ09", "abc123XYZ09"],
  ["https://youtu.be/abc123XYZ09?t=5", "abc123XYZ09"],
  ["https://www.youtube.com/shorts/abc123XYZ09?si=foo", "abc123XYZ09"],
  ["https://www.youtube.com/embed/abc123XYZ09", "abc123XYZ09"],
  ["https://youtu.be/shorts/abc123XYZ09", "abc123XYZ09"],
  ["https://www.youtube.com/live/abc123XYZ09?feature=shared", "abc123XYZ09"],
  ["https://music.youtube.com/watch?v=abc123XYZ09&si=bar", "abc123XYZ09"],
  ["https://example.com/video.mp4", null],
] as const;

export function runExtractYouTubeIdMiniTest(): void {
  __extractYouTubeIdSamples__.forEach(([input, expected]) => {
    const actual = extractYouTubeId(input);
    if (actual !== expected) {
      // eslint-disable-next-line no-console
      console.error(`extractYouTubeId failed for "${input}" → got "${actual}", expected "${expected}"`);
    }
  });
}
