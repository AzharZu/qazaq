export interface TestQuestion {
  id?: string;
  question?: string;
  prompt?: string;
  text?: string;
  title?: string;
  label?: string;
  name?: string;
  body?: string;
  content?: string;
  description?: string;
  options: string[];
  correct?: number;
  correct_option?: number;
  section?: string;
}

export interface RecommendedCourseInfo {
  id?: number;
  slug?: string;
  name?: string;
  description?: string;
  audience?: string;
}

export interface PlacementResult {
  score: number;
  total: number;
  raw_score?: number;
  level: string;
  recommended_course?: string | RecommendedCourseInfo | null;
  course?: RecommendedCourseInfo | null;
}

type UnknownRecord = Record<string, unknown>;

const isRecord = (value: unknown): value is UnknownRecord =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const toNumber = (value: unknown): number | null => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return null;
    const parsed = Number(trimmed);
    if (Number.isFinite(parsed)) return parsed;
  }
  return null;
};

const sanitizeCourseInfo = (value: unknown): RecommendedCourseInfo | null => {
  if (!isRecord(value)) return null;
  const info: RecommendedCourseInfo = {};
  if (typeof value.id === "number") info.id = value.id;
  if (typeof value.slug === "string") info.slug = value.slug;
  if (typeof value.name === "string") info.name = value.name;
  if (typeof value.description === "string") info.description = value.description;
  if (typeof value.audience === "string") info.audience = value.audience;
  return Object.keys(info).length ? info : null;
};

const normalizeRecommended = (value: unknown): PlacementResult["recommended_course"] => {
  if (typeof value === "string") return value;
  if (value === null || value === undefined) return null;
  return sanitizeCourseInfo(value);
};

export const parsePlacementResult = (value: unknown): PlacementResult | null => {
  if (!isRecord(value)) return null;
  const score = toNumber(value.score);
  const total = toNumber(value.total);
  const level = typeof value.level === "string" ? value.level : null;
  if (score === null || total === null || !level) return null;
  const rawScore = toNumber(value.raw_score);
  return {
    score,
    total,
    level,
    ...(rawScore !== null ? { raw_score: rawScore } : {}),
    recommended_course: normalizeRecommended(value.recommended_course),
    course: sanitizeCourseInfo(value.course),
  };
};
