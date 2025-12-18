const getApiBase = (): string => {
  const raw = (process.env.NEXT_PUBLIC_API_URL || "").trim();
  return raw.replace(/\/+$/, "");
};

export function resolveMediaUrl(path: string | null | undefined): string {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const base = getApiBase();
  if (!base) {
    console.error("NEXT_PUBLIC_API_URL is not set, media URL may resolve to the wrong host");
    return path;
  }
  const root = base.replace(/\/api\/?$/, "");
  return `${root}/${path.replace(/^\/+/, "")}`;
}
