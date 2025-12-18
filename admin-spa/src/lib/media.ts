const getApiBase = () => {
  const raw = (import.meta.env.VITE_API_URL || "").trim();
  return raw.replace(/\/+$/, "");
};

export const resolveMediaUrl = (path?: string | null): string => {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const base = getApiBase();
  const root = base.replace(/\/api\/?$/, "");
  return `${root}/${path.replace(/^\/+/, "")}`;
};
